from rest_framework import generics, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.http import HttpResponse, Http404
from django.shortcuts import get_object_or_404
import os

from .models import Highlight
from videos.models import Video
from .serializers import (
    HighlightSerializer, HighlightListSerializer, HighlightCreateSerializer,
    HighlightFilterSerializer, HighlightDownloadSerializer
)
from core.tasks import create_highlight_video


class HighlightViewSet(viewsets.ModelViewSet):
    """ViewSet for Highlight operations"""
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['highlight_type']
    
    def get_queryset(self):
        queryset = Highlight.objects.filter(video__user=self.request.user)
        
        # Apply custom filters
        player_id = self.request.query_params.get('player')
        if player_id:
            queryset = queryset.filter(player__id=player_id)
        
        highlight_type = self.request.query_params.get('type')
        if highlight_type:
            queryset = queryset.filter(highlight_type=highlight_type)
        
        min_duration = self.request.query_params.get('min_duration')
        if min_duration:
            try:
                queryset = queryset.filter(duration__gte=float(min_duration))
            except ValueError:
                pass
        
        max_duration = self.request.query_params.get('max_duration')
        if max_duration:
            try:
                queryset = queryset.filter(duration__lte=float(max_duration))
            except ValueError:
                pass
        
        return queryset.select_related('video', 'player').prefetch_related('actions').order_by('-created_at')
    
    def get_serializer_class(self):
        if self.action == 'create':
            return HighlightCreateSerializer
        elif self.action == 'list':
            return HighlightListSerializer
        return HighlightSerializer
    
    def perform_create(self, serializer):
        """Create highlight and start video generation"""
        highlight = serializer.save()
        
        # Start highlight video generation task
        create_highlight_video.delay(str(highlight.id))
        
    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        """Download highlight video"""
        highlight = self.get_object()
        
        if not highlight.file:
            return Response(
                {'error': 'Highlight video not available'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Increment download count
        highlight.increment_download_count()
        
        # Return download URL
        serializer = HighlightDownloadSerializer(highlight, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def view(self, request, pk=None):
        """Increment view count"""
        highlight = self.get_object()
        highlight.increment_view_count()
        
        return Response({'message': 'View count incremented'})
    
    @action(detail=False, methods=['get'])
    def types(self, request):
        """Get available highlight types"""
        return Response({
            'highlight_types': [{'value': choice[0], 'label': choice[1]} 
                              for choice in Highlight.HIGHLIGHT_TYPES]
        })
    
    @action(detail=False, methods=['post'])
    def auto_generate(self, request):
        """Auto-generate highlights for a video"""
        video_id = request.data.get('video_id')
        highlight_type = request.data.get('type', 'best_plays')
        min_confidence = request.data.get('min_confidence', 0.7)
        max_duration = request.data.get('max_duration', 60.0)
        
        if not video_id:
            return Response(
                {'error': 'video_id is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            video = Video.objects.get(id=video_id, user=request.user)
        except Video.DoesNotExist:
            return Response(
                {'error': 'Video not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        if video.status != 'actions_done':
            return Response(
                {'error': 'Video must have actions analyzed first'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create highlight object
        highlight = Highlight.objects.create(
            video=video,
            title=f"Auto-generated {highlight_type.replace('_', ' ').title()}",
            highlight_type=highlight_type,
            min_confidence=min_confidence,
            max_duration=max_duration,
            is_processing=True
        )
        
        # Start generation task
        create_highlight_video.delay(str(highlight.id))
        
        return Response({
            'message': 'Highlight generation started',
            'highlight_id': highlight.id
        })


class HighlightListView(generics.ListAPIView):
    """List highlights with filtering"""
    serializer_class = HighlightListSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['highlight_type']
    
    def get_queryset(self):
        queryset = Highlight.objects.filter(video__user=self.request.user)
        
        # Apply filters
        player_id = self.request.query_params.get('player')
        if player_id:
            queryset = queryset.filter(player__id=player_id)
        
        highlight_type = self.request.query_params.get('type')
        if highlight_type:
            queryset = queryset.filter(highlight_type=highlight_type)
        
        return queryset.select_related('video', 'player').order_by('-created_at')


class HighlightDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or delete a highlight"""
    serializer_class = HighlightSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Highlight.objects.filter(video__user=self.request.user)


class HighlightDownloadView(generics.GenericAPIView):
    """Download highlight video file"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, pk):
        try:
            highlight = Highlight.objects.get(pk=pk, video__user=request.user)
        except Highlight.DoesNotExist:
            raise Http404("Highlight not found")
        
        if not highlight.file:
            return Response(
                {'error': 'Highlight video not available'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Increment download count
        highlight.increment_download_count()
        
        # Serve file
        try:
            with open(highlight.file.path, 'rb') as f:
                response = HttpResponse(f.read(), content_type='video/mp4')
                response['Content-Disposition'] = f'attachment; filename="{highlight.title}.mp4"'
                return response
        except FileNotFoundError:
            return Response(
                {'error': 'Video file not found on server'}, 
                status=status.HTTP_404_NOT_FOUND
            ) 