from rest_framework import serializers
from .models import Action
from players.serializers import PlayerListSerializer


class ActionSerializer(serializers.ModelSerializer):
    """Serializer for Action model"""
    player = PlayerListSerializer(read_only=True)
    duration = serializers.ReadOnlyField()
    
    class Meta:
        model = Action
        fields = [
            'id', 'video', 'player', 'type', 'start_time', 'end_time', 'duration',
            'is_successful', 'x', 'y', 'model_type', 'confidence', 'segment_path',
            'metadata', 'created_at'
        ]
        read_only_fields = [
            'id', 'duration', 'model_type', 'confidence', 'segment_path', 'metadata', 'created_at'
        ]


class ActionListSerializer(serializers.ModelSerializer):
    """Simplified serializer for listing actions"""
    player_jersey = serializers.CharField(source='player.jersey_number', read_only=True)
    duration = serializers.ReadOnlyField()
    
    class Meta:
        model = Action
        fields = [
            'id', 'type', 'start_time', 'end_time', 'duration', 'is_successful', 
            'confidence', 'player_jersey'
        ]


class ActionCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating actions (primarily for manual annotation)"""
    
    class Meta:
        model = Action
        fields = [
            'video', 'player', 'type', 'start_time', 'end_time', 'is_successful', 'x', 'y'
        ]
    
    def validate(self, data):
        """Validate action data"""
        if data['start_time'] >= data['end_time']:
            raise serializers.ValidationError("End time must be after start time")
        
        if data['end_time'] - data['start_time'] > 30:  # Max 30 seconds for single action
            raise serializers.ValidationError("Action duration cannot exceed 30 seconds")
        
        return data
    
    def create(self, validated_data):
        # Set default values for manual annotations
        validated_data['model_type'] = 'manual_annotation'
        validated_data['confidence'] = 1.0
        return super().create(validated_data)


class ActionFilterSerializer(serializers.Serializer):
    """Serializer for action filtering parameters"""
    video = serializers.UUIDField(required=False)
    player = serializers.IntegerField(required=False)
    type = serializers.ChoiceField(choices=Action.ACTION_TYPES, required=False)
    min_confidence = serializers.FloatField(min_value=0.0, max_value=1.0, required=False)
    is_successful = serializers.BooleanField(required=False)
    start_time_min = serializers.FloatField(min_value=0, required=False)
    start_time_max = serializers.FloatField(min_value=0, required=False)


class ActionInferenceSerializer(serializers.Serializer):
    """Serializer for starting action inference on a video"""
    video_id = serializers.UUIDField()
    model_type = serializers.ChoiceField(
        choices=['mmaction2_tsn', 'mmaction2_slowfast'], 
        default='mmaction2_tsn'
    )
    confidence_threshold = serializers.FloatField(
        min_value=0.1, max_value=1.0, default=0.5
    ) 