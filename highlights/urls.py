from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'', views.HighlightViewSet, basename='highlight')

urlpatterns = [
    path('', include(router.urls)),
    path('list/', views.HighlightListView.as_view(), name='highlight-list'),
    path('<uuid:pk>/download/', views.HighlightDownloadView.as_view(), name='highlight-download'),
    path('<uuid:pk>/', views.HighlightDetailView.as_view(), name='highlight-detail'),
] 