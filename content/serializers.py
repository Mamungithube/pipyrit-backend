from rest_framework import serializers
from .models import SiteSetting

class SiteSettingSerializer(serializers.ModelSerializer):
    class Meta:
        model = SiteSetting
        fields = ['id', 'key', 'title', 'content', 'updated_at']