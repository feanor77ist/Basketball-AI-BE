from rest_framework import generics, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
import csv
import json
from io import StringIO

from .models import Stats
from videos.models import Video
from .serializers import (
    StatsSerializer, StatsListSerializer, StatsCreateUpdateSerializer, StatsExportSerializer
)


class StatsViewSet(viewsets.ModelViewSet):
    """ViewSet for Stats operations"""
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    
    def get_queryset(self):
        queryset = Stats.objects.filter(video__user=self.request.user)
        
        # Apply video filter
        video_id = self.request.query_params.get('video')
        if video_id:
            queryset = queryset.filter(video__id=video_id)
        
        # Apply player filter
        player_id = self.request.query_params.get('player')
        if player_id:
            queryset = queryset.filter(player__id=player_id)
        
        return queryset.select_related('video', 'player').order_by('-created_at')
    
    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return StatsCreateUpdateSerializer
        elif self.action == 'list':
            return StatsListSerializer
        return StatsSerializer
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get statistics summary for a video"""
        video_id = request.query_params.get('video')
        if not video_id:
            return Response(
                {'error': 'video parameter is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            video = Video.objects.get(id=video_id, user=request.user)
        except Video.DoesNotExist:
            return Response(
                {'error': 'Video not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        stats = Stats.objects.filter(video=video)
        
        if not stats.exists():
            return Response({
                'message': 'No statistics available for this video',
                'video_id': video_id
            })
        
        # Calculate team totals and averages
        total_stats = {
            'total_points': sum(s.points for s in stats),
            'total_fga_2pt': sum(s.fga_2pt for s in stats),
            'total_fgm_2pt': sum(s.fgm_2pt for s in stats),
            'total_fga_3pt': sum(s.fga_3pt for s in stats),
            'total_fgm_3pt': sum(s.fgm_3pt for s in stats),
            'total_assists': sum(s.assists for s in stats),
            'total_rebounds': sum(s.rebounds for s in stats),
            'total_steals': sum(s.steals for s in stats),
            'total_blocks': sum(s.blocks for s in stats),
            'total_turnovers': sum(s.turnovers for s in stats),
            'total_fouls': sum(s.fouls for s in stats),
        }
        
        # Calculate team shooting percentages
        team_fg2_pct = (total_stats['total_fgm_2pt'] / total_stats['total_fga_2pt'] * 100) if total_stats['total_fga_2pt'] > 0 else 0
        team_fg3_pct = (total_stats['total_fgm_3pt'] / total_stats['total_fga_3pt'] * 100) if total_stats['total_fga_3pt'] > 0 else 0
        
        # Top performers
        top_scorer = stats.order_by('-points').first()
        top_assists = stats.order_by('-assists').first()
        top_rebounds = stats.order_by('-rebounds').first()
        
        summary = {
            'video_id': video_id,
            'player_count': stats.count(),
            'team_totals': total_stats,
            'team_percentages': {
                'fg2_pct': round(team_fg2_pct, 1),
                'fg3_pct': round(team_fg3_pct, 1),
            },
            'top_performers': {
                'points': {
                    'player': f"Player {top_scorer.player.jersey_number}" if top_scorer else None,
                    'value': top_scorer.points if top_scorer else 0
                },
                'assists': {
                    'player': f"Player {top_assists.player.jersey_number}" if top_assists else None,
                    'value': top_assists.assists if top_assists else 0
                },
                'rebounds': {
                    'player': f"Player {top_rebounds.player.jersey_number}" if top_rebounds else None,
                    'value': top_rebounds.rebounds if top_rebounds else 0
                }
            }
        }
        
        return Response(summary)
    
    @action(detail=False, methods=['get'])
    def export(self, request):
        """Export stats to CSV or JSON"""
        video_id = request.query_params.get('video')
        format_type = request.query_params.get('format', 'csv').lower()
        
        if not video_id:
            return Response(
                {'error': 'video parameter is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            video = Video.objects.get(id=video_id, user=request.user)
        except Video.DoesNotExist:
            return Response(
                {'error': 'Video not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        stats = Stats.objects.filter(video=video).select_related('player')
        
        if not stats.exists():
            return Response(
                {'error': 'No statistics available for this video'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Serialize data
        serializer = StatsExportSerializer(stats, many=True)
        data = serializer.data
        
        if format_type == 'csv':
            return self._export_csv(data, video.filename or f"video_{video_id}")
        elif format_type == 'json':
            return self._export_json(data, video.filename or f"video_{video_id}")
        else:
            return Response(
                {'error': 'Unsupported format. Use csv or json'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
    
    def _export_csv(self, data, filename):
        """Export data as CSV"""
        output = StringIO()
        if data:
            writer = csv.DictWriter(output, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)
        
        response = HttpResponse(output.getvalue(), content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{filename}_stats.csv"'
        return response
    
    def _export_json(self, data, filename):
        """Export data as JSON"""
        response = HttpResponse(json.dumps(data, indent=2), content_type='application/json')
        response['Content-Disposition'] = f'attachment; filename="{filename}_stats.json"'
        return response


class VideoStatsView(generics.ListAPIView):
    """Get stats for a specific video"""
    serializer_class = StatsListSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        video_id = self.kwargs.get('video_id')
        return Stats.objects.filter(
            video__id=video_id, 
            video__user=self.request.user
        ).select_related('video', 'player')


class StatsListView(generics.ListCreateAPIView):
    """List or create stats"""
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    
    def get_queryset(self):
        return Stats.objects.filter(video__user=self.request.user).select_related('video', 'player')
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return StatsCreateUpdateSerializer
        return StatsListSerializer


class StatsDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or delete stats"""
    serializer_class = StatsSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Stats.objects.filter(video__user=self.request.user)
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return StatsCreateUpdateSerializer
        return StatsSerializer 