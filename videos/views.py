from rest_framework import generics, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
import cv2
from moviepy.editor import VideoFileClip

from .models import Video
from .serializers import (
    VideoListSerializer, VideoDetailSerializer, VideoUploadSerializer, VideoStatusSerializer
)
from core.tasks import process_video_task


class VideoViewSet(viewsets.ModelViewSet):
    """ViewSet for Video operations"""
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['status']
    
    def get_queryset(self):
        return Video.objects.filter(user=self.request.user).order_by('-upload_date')
    
    def get_serializer_class(self):
        if self.action == 'create':
            return VideoUploadSerializer
        elif self.action == 'list':
            return VideoListSerializer
        return VideoDetailSerializer
    
    def get_parsers(self):
        if self.action == 'create':
            return [MultiPartParser(), FormParser()]
        return super().get_parsers()
    
    def perform_create(self, serializer):
        """Handle video upload and metadata extraction"""
        video = serializer.save(user=self.request.user)
        
        # Extract video metadata
        try:
            self._extract_video_metadata(video)
        except Exception as e:
            video.error_message = f"Failed to extract metadata: {str(e)}"
            video.status = 'error'
            video.save()
    
    def _extract_video_metadata(self, video):
        """Extract video metadata using OpenCV and MoviePy"""
        video_path = video.file.path
        
        # Use OpenCV for basic properties
        cap = cv2.VideoCapture(video_path)
        if cap.isOpened():
            video.fps = cap.get(cv2.CAP_PROP_FPS)
            video.width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            video.height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
            video.duration = frame_count / video.fps if video.fps > 0 else 0
            cap.release()
        
        # Use MoviePy for duration verification
        try:
            clip = VideoFileClip(video_path)
            video.duration = clip.duration
            clip.close()
        except Exception:
            pass  # Use OpenCV duration if MoviePy fails
        
        video.save()
    
    @action(detail=True, methods=['post'])
    def process(self, request, pk=None):
        """Start video processing"""
        video = self.get_object()
        
        if video.status != 'uploaded':
            return Response(
                {'error': 'Video can only be processed from uploaded status'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Start async processing
        process_video_task.delay(video.id)
        video.status = 'processing'
        video.save()
        
        return Response({'message': 'Video processing started'})
    
    @action(detail=True, methods=['get'])
    def status(self, request, pk=None):
        """Get video processing status"""
        video = self.get_object()
        serializer = VideoStatusSerializer(video)
        return Response(serializer.data)


class VideoUploadView(generics.CreateAPIView):
    """Dedicated view for video upload"""
    queryset = Video.objects.all()
    serializer_class = VideoUploadSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    
    def perform_create(self, serializer):
        video = serializer.save(user=self.request.user)
        
        # Extract metadata in background
        try:
            self._extract_video_metadata(video)
        except Exception as e:
            video.error_message = f"Metadata extraction failed: {str(e)}"
            video.save()
    
    def _extract_video_metadata(self, video):
        """Extract video metadata"""
        video_path = video.file.path
        
        cap = cv2.VideoCapture(video_path)
        if cap.isOpened():
            video.fps = cap.get(cv2.CAP_PROP_FPS)
            video.width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            video.height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
            video.duration = frame_count / video.fps if video.fps > 0 else 0
            cap.release()
        
        video.save()


class VideoProcessView(generics.GenericAPIView):
    """View to start video processing"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        video_id = request.data.get('video_id')
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
        
        if video.status != 'uploaded':
            return Response(
                {'error': 'Video must be in uploaded status'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Start processing
        process_video_task.delay(str(video.id))
        video.status = 'processing'
        video.save()
        
        return Response({'message': 'Processing started', 'video_id': video.id})


class VideoStatusView(generics.RetrieveAPIView):
    """View to check video processing status"""
    queryset = Video.objects.all()
    serializer_class = VideoStatusSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'pk'
    
    def get_queryset(self):
        return Video.objects.filter(user=self.request.user) 