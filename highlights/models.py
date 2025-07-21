from django.db import models
from videos.models import Video
from players.models import Player
from actions.models import Action
from core.models import BaseModel


class Highlight(BaseModel):
    HIGHLIGHT_TYPES = [
        ('best_plays', 'Best Plays'),
        ('shooting_highlights', 'Shooting Highlights'),
        ('defensive_highlights', 'Defensive Highlights'),
        ('player_specific', 'Player Specific'),
        ('game_winning_moments', 'Game Winning Moments'),
        ('skills_showcase', 'Skills Showcase'),
        ('team_highlights', 'Team Highlights'),
    ]
    
    video = models.ForeignKey(Video, on_delete=models.CASCADE, related_name='highlights')
    player = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='highlights', null=True, blank=True)
    
    # Highlight metadata
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    highlight_type = models.CharField(max_length=30, choices=HIGHLIGHT_TYPES, default='best_plays')
    
    # Generated highlight video
    file = models.FileField(upload_to='highlights/%Y/%m/%d/')
    duration = models.FloatField()  # Duration in seconds
    
    # Actions included in this highlight
    actions = models.ManyToManyField(Action, related_name='highlights', blank=True)
    
    # Generation settings
    min_confidence = models.FloatField(default=0.7)
    max_duration = models.FloatField(default=60.0)  # Maximum highlight duration
    
    # Processing status
    is_processing = models.BooleanField(default=False)
    processing_error = models.TextField(blank=True, null=True)
    
    # Statistics
    view_count = models.IntegerField(default=0)
    download_count = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['video', 'highlight_type']),
            models.Index(fields=['player', 'highlight_type']),
        ]
        
    def __str__(self):
        player_info = f" - {self.player.jersey_number}" if self.player else ""
        return f"Highlight: {self.title}{player_info}"
    
    @property
    def action_count(self):
        return self.actions.count()
    
    def increment_view_count(self):
        self.view_count += 1
        self.save(update_fields=['view_count'])
    
    def increment_download_count(self):
        self.download_count += 1
        self.save(update_fields=['download_count']) 