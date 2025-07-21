from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'', views.ActionViewSet, basename='action')

urlpatterns = [
    path('', include(router.urls)),
    path('list/', views.ActionListView.as_view(), name='action-list'),
    path('create/', views.ActionCreateView.as_view(), name='action-create'),
    path('<int:pk>/', views.ActionDetailView.as_view(), name='action-detail'),
] 