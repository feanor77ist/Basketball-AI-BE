from rest_framework import serializers
from .models import Highlight
from actions.serializers import ActionListSerializer
from players.serializers import PlayerListSerializer


class HighlightSerializer(serializers.ModelSerializer):
    """Serializer for Highlight model"""
    player = PlayerListSerializer(read_only=True)
    actions = ActionListSerializer(many=True, read_only=True)
    action_count = serializers.ReadOnlyField()
    
    class Meta:
        model = Highlight
        fields = [
            'id', 'video', 'player', 'title', 'description', 'highlight_type',
            'file', 'duration', 'actions', 'action_count', 'min_confidence',
            'max_duration', 'is_processing', 'processing_error', 'view_count',
            'download_count', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'file', 'duration', 'action_count', 'is_processing', 
            'processing_error', 'view_count', 'download_count', 'created_at', 'updated_at'
        ]


class HighlightListSerializer(serializers.ModelSerializer):
    """Simplified serializer for listing highlights"""
    player_jersey = serializers.CharField(source='player.jersey_number', read_only=True)
    action_count = serializers.ReadOnlyField()
    
    class Meta:
        model = Highlight
        fields = [
            'id', 'title', 'highlight_type', 'duration', 'player_jersey',
            'action_count', 'view_count', 'created_at'
        ]


class HighlightCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating highlights"""
    action_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False
    )
    
    class Meta:
        model = Highlight
        fields = [
            'video', 'player', 'title', 'description', 'highlight_type',
            'min_confidence', 'max_duration', 'action_ids'
        ]
    
    def create(self, validated_data):
        action_ids = validated_data.pop('action_ids', [])
        highlight = super().create(validated_data)
        
        if action_ids:
            # Add specified actions to highlight
            from actions.models import Action
            actions = Action.objects.filter(id__in=action_ids, video=highlight.video)
            highlight.actions.set(actions)
        
        return highlight


class HighlightFilterSerializer(serializers.Serializer):
    """Serializer for highlight filtering parameters"""
    player = serializers.IntegerField(required=False)
    type = serializers.ChoiceField(choices=Highlight.HIGHLIGHT_TYPES, required=False)
    min_duration = serializers.FloatField(min_value=0, required=False)
    max_duration = serializers.FloatField(min_value=0, required=False)


class HighlightDownloadSerializer(serializers.ModelSerializer):
    """Serializer for highlight download response"""
    download_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Highlight
        fields = ['id', 'title', 'file', 'download_url', 'duration']
    
    def get_download_url(self, obj):
        request = self.context.get('request')
        if obj.file and request:
            return request.build_absolute_uri(obj.file.url)
        return None 