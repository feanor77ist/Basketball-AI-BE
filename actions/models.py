from django.db import models
from videos.models import Video
from players.models import Player
from core.models import BaseModel


class Action(models.Model):
    ACTION_TYPES = [
        # Shooting actions
        ('shot_2pt', '2-Point Shot'),
        ('shot_3pt', '3-Point Shot'),
        ('free_throw', 'Free Throw'),
        ('dunk', 'Dunk'),
        ('layup', 'Layup'),
        
        # Ball handling
        ('dribble', 'Dribble'),
        ('pass', 'Pass'),
        ('steal', 'Steal'),
        ('turnover', 'Turnover'),
        
        # Rebounding
        ('rebound_offensive', 'Offensive Rebound'),
        ('rebound_defensive', 'Defensive Rebound'),
        
        # Defense
        ('block', 'Block'),
        ('foul', 'Foul'),
        
        # Movement
        ('run', 'Run'),
        ('walk', 'Walk'),
        ('jump', 'Jump'),
        
        # Other
        ('assist', 'Assist'),
        ('timeout', 'Timeout'),
        ('substitution', 'Substitution'),
    ]
    
    MODEL_TYPES = [
        ('mmaction2_tsn', 'MMAction2 TSN'),
        ('mmaction2_slowfast', 'MMAction2 SlowFast'),
        ('yolo_detection', 'YOLO Detection'),
        ('manual_annotation', 'Manual Annotation'),
    ]
    
    video = models.ForeignKey(Video, on_delete=models.CASCADE, related_name='actions')
    player = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='actions', null=True, blank=True)
    type = models.CharField(max_length=30, choices=ACTION_TYPES)
    start_time = models.FloatField()  # Start time in seconds
    end_time = models.FloatField()    # End time in seconds
    is_successful = models.BooleanField(null=True, blank=True)  # For shots, passes, etc.
    
    # Position coordinates (center of action)
    x = models.FloatField(null=True, blank=True)  # X coordinate (0-1)
    y = models.FloatField(null=True, blank=True)  # Y coordinate (0-1)
    
    # ML model information
    model_type = models.CharField(max_length=30, choices=MODEL_TYPES)
    confidence = models.FloatField()  # Model confidence (0-1)
    
    # Video segment path for this specific action
    segment_path = models.FileField(upload_to='action_segments/%Y/%m/%d/', null=True, blank=True)
    
    # Additional metadata
    metadata = models.JSONField(default=dict, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['video', 'start_time']
        indexes = [
            models.Index(fields=['video', 'type']),
            models.Index(fields=['player', 'type']),
            models.Index(fields=['start_time', 'end_time']),
        ]
        
    def __str__(self):
        player_info = f" - Player {self.player.jersey_number}" if self.player else ""
        return f"Action {self.type} ({self.start_time:.1f}s-{self.end_time:.1f}s){player_info}"
    
    @property
    def duration(self):
        return self.end_time - self.start_time
    
    def is_shooting_action(self):
        return self.type in ['shot_2pt', 'shot_3pt', 'free_throw', 'dunk', 'layup']
    
    def is_ball_handling_action(self):
        return self.type in ['dribble', 'pass', 'steal', 'turnover'] 