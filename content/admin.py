from django.contrib import admin

from content.models import VideoContent, SiteSetting


# Register your models here.
@admin.register(VideoContent)
class VideoContentAdmin(admin.ModelAdmin):
    list_display = ['title', 'is_premium', 'upload_date']
    list_filter = ['is_premium', 'upload_date']
    search_fields = ['title', 'description']

@admin.register(SiteSetting)
class SiteSettingAdmin(admin.ModelAdmin):
    list_display = ['title', 'key', 'updated_at']
    list_filter = ['updated_at']
    search_fields = ['title', 'content']