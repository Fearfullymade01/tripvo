from django.db.models.signals import post_save
from django.dispatch import receiver
from plans.models import Notification as PlanNotification
from notifications.models import Notification as AppNotification
from notifications.fcm_service import FCMNotificationService
from django.conf import settings

# Example: Send push notification when a new plan notification is created
@receiver(post_save, sender=PlanNotification)
def send_plan_notification(sender, instance, created, **kwargs):
    if created and instance.recipient and instance.title:
        # Save to notifications app for unified feed
        AppNotification.objects.create(
            user=instance.recipient,
            notification_type="plan",
            message=instance.title + ": " + instance.message,
            data={"plan_id": str(getattr(instance.plan, 'id', ''))}
        )
        # Send push notification (if user has device token)
        device_token = getattr(instance.recipient, 'device_token', None)
        if device_token and settings.FCM_SERVER_KEY:
            fcm = FCMNotificationService(settings.FCM_SERVER_KEY)
            fcm.send_notification(
                registration_id=device_token,
                title=instance.title,
                body=instance.message,
                data={"plan_id": str(getattr(instance.plan, 'id', ''))}
            )
