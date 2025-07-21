from django.db import models
from videos.models import Video
from players.models import Player
from core.models import BaseModel


class Stats(BaseModel):
    video = models.ForeignKey(Video, on_delete=models.CASCADE, related_name='stats')
    player = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='stats')
    
    # Shooting statistics
    fga_2pt = models.IntegerField(default=0)  # 2-point field goal attempts
    fgm_2pt = models.IntegerField(default=0)  # 2-point field goals made
    fga_3pt = models.IntegerField(default=0)  # 3-point field goal attempts
    fgm_3pt = models.IntegerField(default=0)  # 3-point field goals made
    fta = models.IntegerField(default=0)      # Free throw attempts
    ftm = models.IntegerField(default=0)      # Free throws made
    
    # Other statistics
    assists = models.IntegerField(default=0)
    rebounds = models.IntegerField(default=0)
    offensive_rebounds = models.IntegerField(default=0)
    defensive_rebounds = models.IntegerField(default=0)
    steals = models.IntegerField(default=0)
    blocks = models.IntegerField(default=0)
    turnovers = models.IntegerField(default=0)
    fouls = models.IntegerField(default=0)
    
    # Calculated fields
    points = models.IntegerField(default=0)
    
    # Time-based statistics
    minutes_played = models.FloatField(default=0.0)  # In minutes
    
    # Advanced statistics (calculated)
    plus_minus = models.IntegerField(default=0)
    
    class Meta:
        unique_together = ['video', 'player']
        verbose_name_plural = 'Stats'
        
    def __str__(self):
        return f"Stats - Player {self.player.jersey_number} - Video {self.video.id}"
    
    def calculate_shooting_percentages(self):
        """Calculate and return shooting percentages"""
        fg2_pct = (self.fgm_2pt / self.fga_2pt * 100) if self.fga_2pt > 0 else 0
        fg3_pct = (self.fgm_3pt / self.fga_3pt * 100) if self.fga_3pt > 0 else 0
        ft_pct = (self.ftm / self.fta * 100) if self.fta > 0 else 0
        
        total_fga = self.fga_2pt + self.fga_3pt
        total_fgm = self.fgm_2pt + self.fgm_3pt
        fg_pct = (total_fgm / total_fga * 100) if total_fga > 0 else 0
        
        return {
            'fg_pct': round(fg_pct, 1),
            'fg2_pct': round(fg2_pct, 1),
            'fg3_pct': round(fg3_pct, 1),
            'ft_pct': round(ft_pct, 1),
        }
    
    def calculate_points(self):
        """Calculate total points and update the field"""
        self.points = (self.fgm_2pt * 2) + (self.fgm_3pt * 3) + self.ftm
        return self.points
    
    def save(self, *args, **kwargs):
        # Auto-calculate points before saving
        self.calculate_points()
        # Calculate total rebounds
        self.rebounds = self.offensive_rebounds + self.defensive_rebounds
        super().save(*args, **kwargs) 