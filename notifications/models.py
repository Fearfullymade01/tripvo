from django.db import models
from django.conf import settings

class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ("member", "New Member"),
        ("poll", "Poll Update"),
        ("itinerary", "Itinerary Change"),
        ("expense", "Expense Update"),
        ("chat", "Chat Message"),
    ]
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="user_notifications")
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    data = models.JSONField(blank=True, null=True)

    def __str__(self):
        return f"{self.user} - {self.notification_type} - {self.message[:30]}"
