from django.contrib import admin
from .models import Action


@admin.register(Action)
class ActionAdmin(admin.ModelAdmin):
    list_display = ['id', 'video', 'player', 'type', 'start_time', 'end_time', 'confidence', 'is_successful']
    list_filter = ['type', 'model_type', 'is_successful', 'created_at']
    search_fields = ['video__user__username', 'player__jersey_number', 'type']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('video', 'player', 'type', 'is_successful')
        }),
        ('Timing', {
            'fields': ('start_time', 'end_time')
        }),
        ('Position', {
            'fields': ('x', 'y')
        }),
        ('Model Information', {
            'fields': ('model_type', 'confidence', 'metadata')
        }),
        ('Media', {
            'fields': ('segment_path',)
        })
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('video', 'player') 