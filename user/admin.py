from django.contrib import admin

# Register your models here.
from .models import User, Profile
@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('id', 'email', 'full_name', 'is_staff', 'is_active')
    search_fields = ('email', 'full_name')
    list_filter = ('is_staff', 'is_active')
    ordering = ('email',)

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('id','user', 'language', 'total_points', 'confidence_level', 'is_verified')
    search_fields = ('user__email', 'user__full_name')
    list_filter = ('language', 'is_verified')
    ordering = ('user__email',)