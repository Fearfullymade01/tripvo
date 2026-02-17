from rest_framework import serializers
from .notification_settings_models import NotificationSetting

class NotificationSettingSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationSetting
        fields = ['chat', 'poll', 'itinerary', 'expense', 'member']
