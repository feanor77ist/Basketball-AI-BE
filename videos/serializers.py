from rest_framework import serializers
from .models import Video
from django.conf import settings
import os


class VideoListSerializer(serializers.ModelSerializer):
    """Serializer for listing videos with minimal fields"""
    user = serializers.StringRelatedField(read_only=True)
    filename = serializers.ReadOnlyField()
    
    class Meta:
        model = Video
        fields = ['id', 'user', 'filename', 'status', 'duration', 'upload_date', 'created_at']


class VideoDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for video with all fields"""
    user = serializers.StringRelatedField(read_only=True)
    filename = serializers.ReadOnlyField()
    
    class Meta:
        model = Video
        fields = [
            'id', 'user', 'file', 'filename', 'status', 'duration', 'fps', 
            'width', 'height', 'upload_date', 'processing_started_at', 
            'processing_completed_at', 'error_message', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'user', 'status', 'duration', 'fps', 'width', 'height',
            'processing_started_at', 'processing_completed_at', 'error_message',
            'upload_date', 'created_at', 'updated_at'
        ]


class VideoUploadSerializer(serializers.ModelSerializer):
    """Serializer for video upload"""
    
    class Meta:
        model = Video
        fields = ['file']
    
    def validate_file(self, value):
        """Validate uploaded video file"""
        if not value:
            raise serializers.ValidationError("No file provided")
        
        # Check file size
        if value.size > settings.FILE_UPLOAD_MAX_MEMORY_SIZE:
            raise serializers.ValidationError(
                f"File size too large. Maximum size is {settings.FILE_UPLOAD_MAX_MEMORY_SIZE / (1024*1024)}MB"
            )
        
        # Check file extension
        ext = os.path.splitext(value.name)[1][1:].lower()
        if ext not in settings.SUPPORTED_VIDEO_FORMATS:
            raise serializers.ValidationError(
                f"Unsupported file format. Supported formats: {', '.join(settings.SUPPORTED_VIDEO_FORMATS)}"
            )
        
        return value
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class VideoStatusSerializer(serializers.ModelSerializer):
    """Serializer for video status updates"""
    
    class Meta:
        model = Video
        fields = ['id', 'status', 'processing_started_at', 'processing_completed_at', 'error_message']
        read_only_fields = ['id'] 