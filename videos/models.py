from django.db import models
from django.contrib.auth.models import User
from core.models import BaseModel


class Video(BaseModel):
    STATUS_CHOICES = [
        ('uploaded', 'Uploaded'),
        ('processing', 'Processing'),
        ('players_detected', 'Players Detected'),
        ('actions_done', 'Actions Analyzed'),
        ('highlights_created', 'Highlights Created'),
        ('done', 'Complete'),
        ('error', 'Error'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='videos')
    file = models.FileField(upload_to='videos/%Y/%m/%d/')
    upload_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='uploaded')
    duration = models.FloatField(null=True, blank=True)  # Duration in seconds
    fps = models.FloatField(null=True, blank=True)
    width = models.IntegerField(null=True, blank=True)
    height = models.IntegerField(null=True, blank=True)
    
    # Processing metadata
    error_message = models.TextField(blank=True, null=True)
    processing_started_at = models.DateTimeField(null=True, blank=True)
    processing_completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-upload_date']
        
    def __str__(self):
        return f"Video {self.id} - {self.user.username} - {self.status}"
    
    @property
    def filename(self):
        return self.file.name.split('/')[-1] if self.file else None 