from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

urlpatterns = [
    path('register/', views.UserRegistrationView.as_view(), name='user-register'),
    path('login/', views.UserLoginView.as_view(), name='user-login'),
    path('logout/', views.logout_view, name='user-logout'),
    path('profile/', views.UserProfileView.as_view(), name='user-profile'),
    path('user/', views.UserDetailView.as_view(), name='user-detail'),
    path('change-password/', views.PasswordChangeView.as_view(), name='change-password'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    path('token/', views.CustomTokenObtainPairView.as_view(), name='token-obtain-pair'),
    path('health/', views.health_check, name='health-check'),
] 