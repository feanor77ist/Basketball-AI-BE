from rest_framework import serializers
from .models import Player, PlayerProfile, ScoutProfile
from django.contrib.auth.models import User


class PlayerSerializer(serializers.ModelSerializer):
    """Serializer for Player model"""
    
    class Meta:
        model = Player
        fields = [
            'id', 'video', 'jersey_number', 'team_color', 'player_id_model',
            'detection_confidence', 'avg_bbox_area'
        ]
        read_only_fields = ['id', 'detection_confidence', 'avg_bbox_area']


class PlayerListSerializer(serializers.ModelSerializer):
    """Simplified serializer for listing players"""
    
    class Meta:
        model = Player
        fields = ['id', 'jersey_number', 'team_color', 'detection_confidence']


class PlayerProfileSerializer(serializers.ModelSerializer):
    """Serializer for PlayerProfile model"""
    user = serializers.StringRelatedField(read_only=True)
    
    class Meta:
        model = PlayerProfile
        fields = [
            'id', 'user', 'bio', 'height', 'position', 'club',
            'instagram', 'twitter', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']


class PlayerProfileCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating PlayerProfile"""
    
    class Meta:
        model = PlayerProfile
        fields = ['bio', 'height', 'position', 'club', 'instagram', 'twitter']
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class ScoutProfileSerializer(serializers.ModelSerializer):
    """Serializer for ScoutProfile model"""
    user = serializers.StringRelatedField(read_only=True)
    
    class Meta:
        model = ScoutProfile
        fields = [
            'id', 'user', 'organization', 'filters', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']


class ScoutProfileCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating ScoutProfile"""
    
    class Meta:
        model = ScoutProfile
        fields = ['organization', 'filters']
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class UserBasicSerializer(serializers.ModelSerializer):
    """Basic user serializer for relationships"""
    
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email']
        read_only_fields = ['id', 'username'] 