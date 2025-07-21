from rest_framework import generics, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from django.db.models import Q

from .models import Action
from videos.models import Video
from .serializers import (
    ActionSerializer, ActionListSerializer, ActionCreateSerializer,
    ActionFilterSerializer, ActionInferenceSerializer
)
from core.tasks import detect_actions_with_mmaction


class ActionViewSet(viewsets.ModelViewSet):
    """ViewSet for Action operations"""
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['type', 'is_successful', 'model_type']
    
    def get_queryset(self):
        queryset = Action.objects.filter(video__user=self.request.user)
        
        # Apply custom filters
        video_id = self.request.query_params.get('video')
        if video_id:
            queryset = queryset.filter(video__id=video_id)
        
        player_id = self.request.query_params.get('player')
        if player_id:
            queryset = queryset.filter(player__id=player_id)
        
        min_confidence = self.request.query_params.get('min_confidence')
        if min_confidence:
            try:
                queryset = queryset.filter(confidence__gte=float(min_confidence))
            except ValueError:
                pass
        
        action_type = self.request.query_params.get('type')
        if action_type:
            queryset = queryset.filter(type=action_type)
        
        return queryset.select_related('video', 'player').order_by('video', 'start_time')
    
    def get_serializer_class(self):
        if self.action == 'create':
            return ActionCreateSerializer
        elif self.action == 'list':
            return ActionListSerializer
        return ActionSerializer
    
    @action(detail=False, methods=['post'])
    def infer(self, request):
        """Start action inference on a video using mmaction2"""
        serializer = ActionInferenceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        video_id = serializer.validated_data['video_id']
        model_type = serializer.validated_data['model_type']
        confidence_threshold = serializer.validated_data['confidence_threshold']
        
        try:
            video = Video.objects.get(id=video_id, user=request.user)
        except Video.DoesNotExist:
            return Response(
                {'error': 'Video not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        if video.status not in ['uploaded', 'players_detected']:
            return Response(
                {'error': 'Video must be uploaded or have players detected first'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Start action detection task
        detect_actions_with_mmaction.delay(
            str(video.id), 
            model_type, 
            confidence_threshold
        )
        
        return Response({
            'message': 'Action inference started',
            'video_id': video_id,
            'model_type': model_type,
            'confidence_threshold': confidence_threshold
        })
    
    @action(detail=False, methods=['get'])
    def types(self, request):
        """Get available action types"""
        return Response({
            'action_types': [{'value': choice[0], 'label': choice[1]} 
                           for choice in Action.ACTION_TYPES]
        })
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get action summary for a video"""
        video_id = request.query_params.get('video')
        if not video_id:
            return Response(
                {'error': 'video parameter is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            video = Video.objects.get(id=video_id, user=request.user)
        except Video.DoesNotExist:
            return Response(
                {'error': 'Video not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Generate summary statistics
        actions = Action.objects.filter(video=video)
        
        summary = {
            'total_actions': actions.count(),
            'action_breakdown': {},
            'player_breakdown': {},
            'success_rate': {},
            'avg_confidence': 0
        }
        
        # Action type breakdown
        for action_type, label in Action.ACTION_TYPES:
            count = actions.filter(type=action_type).count()
            if count > 0:
                summary['action_breakdown'][action_type] = {
                    'count': count,
                    'label': label
                }
        
        # Player breakdown
        for action in actions.select_related('player'):
            if action.player:
                player_key = f"Player {action.player.jersey_number}"
                if player_key not in summary['player_breakdown']:
                    summary['player_breakdown'][player_key] = 0
                summary['player_breakdown'][player_key] += 1
        
        # Success rate for shooting actions
        shooting_actions = actions.filter(
            type__in=['shot_2pt', 'shot_3pt', 'free_throw', 'dunk', 'layup']
        )
        if shooting_actions.exists():
            successful_shots = shooting_actions.filter(is_successful=True).count()
            total_shots = shooting_actions.count()
            summary['success_rate']['shooting'] = {
                'successful': successful_shots,
                'total': total_shots,
                'percentage': (successful_shots / total_shots * 100) if total_shots > 0 else 0
            }
        
        # Average confidence
        if actions.exists():
            from django.db import models
            summary['avg_confidence'] = actions.aggregate(
                avg_conf=models.Avg('confidence')
            )['avg_conf'] or 0
        
        return Response(summary)


class ActionListView(generics.ListAPIView):
    """List actions with filtering"""
    serializer_class = ActionListSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['type', 'is_successful']
    
    def get_queryset(self):
        queryset = Action.objects.filter(video__user=self.request.user)
        
        # Apply video filter
        video_id = self.request.query_params.get('video')
        if video_id:
            queryset = queryset.filter(video__id=video_id)
        
        return queryset.select_related('video', 'player').order_by('start_time')


class ActionDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or delete an action"""
    serializer_class = ActionSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Action.objects.filter(video__user=self.request.user)


class ActionCreateView(generics.CreateAPIView):
    """Create a new action (manual annotation)"""
    serializer_class = ActionCreateSerializer
    permission_classes = [IsAuthenticated]
    
    def perform_create(self, serializer):
        # Ensure user owns the video
        video = serializer.validated_data['video']
        if video.user != self.request.user:
            raise PermissionError("You don't have permission to add actions to this video")
        
        serializer.save() 