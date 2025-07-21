from django.contrib import admin
from .models import Player, PlayerProfile, ScoutProfile


@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    list_display = ['id', 'jersey_number', 'team_color', 'video', 'detection_confidence']
    list_filter = ['team_color', 'video__status']
    search_fields = ['jersey_number', 'player_id_model', 'video__user__username']
    
    fieldsets = (
        ('Player Information', {
            'fields': ('video', 'jersey_number', 'team_color', 'player_id_model')
        }),
        ('Detection Data', {
            'fields': ('detection_confidence', 'avg_bbox_area')
        })
    )


@admin.register(PlayerProfile)
class PlayerProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'position', 'height', 'club', 'created_at']
    list_filter = ['position', 'created_at']
    search_fields = ['user__username', 'club']
    
    fieldsets = (
        ('User Information', {
            'fields': ('user',)
        }),
        ('Player Details', {
            'fields': ('bio', 'height', 'position', 'club')
        }),
        ('Social Media', {
            'fields': ('instagram', 'twitter')
        })
    )


@admin.register(ScoutProfile)
class ScoutProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'organization', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__username', 'organization'] 