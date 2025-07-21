from django.contrib import admin
from .models import Stats


@admin.register(Stats)
class StatsAdmin(admin.ModelAdmin):
    list_display = ['video', 'player', 'points', 'fgm_2pt', 'fgm_3pt', 'assists', 'rebounds', 'created_at']
    list_filter = ['created_at', 'video__status']
    search_fields = ['video__user__username', 'player__jersey_number']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('video', 'player')
        }),
        ('Shooting Statistics', {
            'fields': ('fga_2pt', 'fgm_2pt', 'fga_3pt', 'fgm_3pt', 'fta', 'ftm')
        }),
        ('Other Statistics', {
            'fields': ('assists', 'rebounds', 'offensive_rebounds', 'defensive_rebounds', 
                      'steals', 'blocks', 'turnovers', 'fouls')
        }),
        ('Calculated Fields', {
            'fields': ('points', 'minutes_played', 'plus_minus')
        })
    )
    
    readonly_fields = ['points', 'rebounds']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('video', 'player') 