from rest_framework import serializers
from .models import SiteSetting , VideoContent

class SiteSettingSerializer(serializers.ModelSerializer):
    class Meta:
        model = SiteSetting
        fields = ['id', 'key', 'title', 'content', 'updated_at']

class VideoContentSerializer(serializers.ModelSerializer):
    class Meta:
        model = VideoContent
        fields = ['id', 'title', 'description', 'thumbnail', 'video_file', 'is_premium', 'upload_date']
        read_only_fields = ['id', 'upload_date']