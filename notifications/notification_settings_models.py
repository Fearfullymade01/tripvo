from django.db import models
from django.conf import settings

class NotificationSetting(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notification_settings")
    chat = models.BooleanField(default=True)
    poll = models.BooleanField(default=True)
    itinerary = models.BooleanField(default=True)
    expense = models.BooleanField(default=True)
    member = models.BooleanField(default=True)

    def __str__(self):
        return f"Notification settings for {self.user.username}"
