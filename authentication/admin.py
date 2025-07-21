from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import UserProfile

# Unregister the default User admin
admin.site.unregister(User)


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)
    
    list_display = ['username', 'email', 'first_name', 'last_name', 'get_user_type', 'is_staff', 'date_joined']
    list_filter = ['is_staff', 'is_superuser', 'is_active', 'date_joined', 'profile__user_type']
    
    def get_user_type(self, obj):
        return obj.profile.user_type if hasattr(obj, 'profile') else 'No Profile'
    get_user_type.short_description = 'User Type'


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'user_type', 'phone_number', 'is_profile_public', 'created_at']
    list_filter = ['user_type', 'is_profile_public', 'allow_notifications', 'created_at']
    search_fields = ['user__username', 'user__email', 'phone_number'] 