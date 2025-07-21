from django.contrib import admin
from .models import Highlight


@admin.register(Highlight)
class HighlightAdmin(admin.ModelAdmin):
    list_display = ['title', 'video', 'player', 'highlight_type', 'duration', 'view_count', 'created_at']
    list_filter = ['highlight_type', 'is_processing', 'created_at']
    search_fields = ['title', 'video__user__username', 'player__jersey_number']
    filter_horizontal = ['actions']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('video', 'player', 'title', 'description', 'highlight_type')
        }),
        ('Media', {
            'fields': ('file', 'duration')
        }),
        ('Generation Settings', {
            'fields': ('min_confidence', 'max_duration')
        }),
        ('Processing', {
            'fields': ('is_processing', 'processing_error')
        }),
        ('Statistics', {
            'fields': ('view_count', 'download_count')
        }),
        ('Actions', {
            'fields': ('actions',)
        })
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('video', 'player').prefetch_related('actions') 