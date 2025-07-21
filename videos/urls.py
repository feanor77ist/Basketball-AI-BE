from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'videos', views.VideoViewSet, basename='video')

urlpatterns = [
    path('', include(router.urls)),
    path('upload/', views.VideoUploadView.as_view(), name='video-upload'),
    path('process/', views.VideoProcessView.as_view(), name='video-process'),
    path('status/<uuid:pk>/', views.VideoStatusView.as_view(), name='video-status'),
] 