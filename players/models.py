from django.db import models
from django.contrib.auth.models import User
from videos.models import Video
from core.models import BaseModel


class Player(models.Model):
    TEAM_COLORS = [
        ('red', 'Red'),
        ('blue', 'Blue'),
        ('white', 'White'),
        ('black', 'Black'),
        ('yellow', 'Yellow'),
        ('green', 'Green'),
        ('orange', 'Orange'),
        ('purple', 'Purple'),
    ]
    
    video = models.ForeignKey(Video, on_delete=models.CASCADE, related_name='players')
    jersey_number = models.CharField(max_length=10, blank=True, null=True)
    team_color = models.CharField(max_length=20, choices=TEAM_COLORS)
    player_id_model = models.CharField(max_length=100)  # Internal model ID for tracking
    
    # Detection confidence and bounding box info
    detection_confidence = models.FloatField(default=0.0)
    avg_bbox_area = models.FloatField(null=True, blank=True)
    
    class Meta:
        unique_together = ['video', 'player_id_model']
        
    def __str__(self):
        return f"Player {self.jersey_number or 'Unknown'} - {self.team_color} - Video {self.video.id}"


class PlayerProfile(BaseModel):
    """Extended player profile for registered users"""
    POSITIONS = [
        ('PG', 'Point Guard'),
        ('SG', 'Shooting Guard'),
        ('SF', 'Small Forward'),
        ('PF', 'Power Forward'),
        ('C', 'Center'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='player_profile')
    bio = models.TextField(blank=True, null=True)
    height = models.FloatField(null=True, blank=True, help_text="Height in cm")
    position = models.CharField(max_length=2, choices=POSITIONS, blank=True, null=True)
    club = models.CharField(max_length=200, blank=True, null=True)
    
    # Social media links
    instagram = models.URLField(blank=True, null=True)
    twitter = models.URLField(blank=True, null=True)
    
    def __str__(self):
        return f"PlayerProfile - {self.user.username}"


class ScoutProfile(BaseModel):
    """Profile for scouts and analysts"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='scout_profile')
    organization = models.CharField(max_length=200)
    filters = models.JSONField(default=dict, blank=True)  # Saved filter preferences
    
    def __str__(self):
        return f"ScoutProfile - {self.user.username} - {self.organization}" 