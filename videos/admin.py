from django.contrib import admin
from .models import Video


@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'filename', 'status', 'duration', 'upload_date']
    list_filter = ['status', 'upload_date']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['id', 'upload_date', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'file', 'status')
        }),
        ('Video Properties', {
            'fields': ('duration', 'fps', 'width', 'height')
        }),
        ('Processing Information', {
            'fields': ('processing_started_at', 'processing_completed_at', 'error_message')
        }),
        ('Metadata', {
            'fields': ('id', 'upload_date', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    ) 