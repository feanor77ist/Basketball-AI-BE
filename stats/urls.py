from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'', views.StatsViewSet, basename='stats')

urlpatterns = [
    path('', include(router.urls)),
    path('list/', views.StatsListView.as_view(), name='stats-list'),
    path('<uuid:video_id>/', views.VideoStatsView.as_view(), name='video-stats'),
    path('<uuid:pk>/detail/', views.StatsDetailView.as_view(), name='stats-detail'),
] 