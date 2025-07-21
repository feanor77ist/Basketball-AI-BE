from rest_framework import serializers
from .models import Stats
from players.serializers import PlayerListSerializer


class StatsSerializer(serializers.ModelSerializer):
    """Serializer for Stats model"""
    player = PlayerListSerializer(read_only=True)
    shooting_percentages = serializers.SerializerMethodField()
    
    class Meta:
        model = Stats
        fields = [
            'id', 'video', 'player', 'fga_2pt', 'fgm_2pt', 'fga_3pt', 'fgm_3pt',
            'fta', 'ftm', 'assists', 'rebounds', 'offensive_rebounds', 
            'defensive_rebounds', 'steals', 'blocks', 'turnovers', 'fouls',
            'points', 'minutes_played', 'plus_minus', 'shooting_percentages',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'points', 'rebounds', 'shooting_percentages', 'created_at', 'updated_at'
        ]
    
    def get_shooting_percentages(self, obj):
        return obj.calculate_shooting_percentages()


class StatsListSerializer(serializers.ModelSerializer):
    """Simplified serializer for listing stats"""
    player_jersey = serializers.CharField(source='player.jersey_number', read_only=True)
    fg_pct = serializers.SerializerMethodField()
    
    class Meta:
        model = Stats
        fields = [
            'id', 'player_jersey', 'points', 'fgm_2pt', 'fga_2pt', 'fgm_3pt', 'fga_3pt',
            'assists', 'rebounds', 'fg_pct', 'minutes_played'
        ]
    
    def get_fg_pct(self, obj):
        percentages = obj.calculate_shooting_percentages()
        return percentages['fg_pct']


class StatsCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating stats"""
    
    class Meta:
        model = Stats
        fields = [
            'video', 'player', 'fga_2pt', 'fgm_2pt', 'fga_3pt', 'fgm_3pt',
            'fta', 'ftm', 'assists', 'offensive_rebounds', 'defensive_rebounds',
            'steals', 'blocks', 'turnovers', 'fouls', 'minutes_played', 'plus_minus'
        ]
    
    def validate(self, data):
        """Validate stats data"""
        # Validate that made shots don't exceed attempts
        if data.get('fgm_2pt', 0) > data.get('fga_2pt', 0):
            raise serializers.ValidationError("2-point made cannot exceed attempts")
        
        if data.get('fgm_3pt', 0) > data.get('fga_3pt', 0):
            raise serializers.ValidationError("3-point made cannot exceed attempts")
        
        if data.get('ftm', 0) > data.get('fta', 0):
            raise serializers.ValidationError("Free throws made cannot exceed attempts")
        
        return data


class StatsExportSerializer(serializers.ModelSerializer):
    """Serializer for exporting stats to CSV/JSON"""
    player_jersey = serializers.CharField(source='player.jersey_number', read_only=True)
    player_team = serializers.CharField(source='player.team_color', read_only=True)
    video_filename = serializers.CharField(source='video.filename', read_only=True)
    fg_pct = serializers.SerializerMethodField()
    fg2_pct = serializers.SerializerMethodField()
    fg3_pct = serializers.SerializerMethodField()
    ft_pct = serializers.SerializerMethodField()
    
    class Meta:
        model = Stats
        fields = [
            'video_filename', 'player_jersey', 'player_team', 'points',
            'fga_2pt', 'fgm_2pt', 'fg2_pct', 'fga_3pt', 'fgm_3pt', 'fg3_pct',
            'fta', 'ftm', 'ft_pct', 'fg_pct', 'assists', 'rebounds',
            'offensive_rebounds', 'defensive_rebounds', 'steals', 'blocks',
            'turnovers', 'fouls', 'minutes_played', 'plus_minus'
        ]
    
    def get_fg_pct(self, obj):
        return obj.calculate_shooting_percentages()['fg_pct']
    
    def get_fg2_pct(self, obj):
        return obj.calculate_shooting_percentages()['fg2_pct']
    
    def get_fg3_pct(self, obj):
        return obj.calculate_shooting_percentages()['fg3_pct']
    
    def get_ft_pct(self, obj):
        return obj.calculate_shooting_percentages()['ft_pct'] 