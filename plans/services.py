
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from .models import Notification


class NotificationService:
    """Service for handling notifications and emails"""

    @staticmethod
    def send_poll_notification(title, message, recipients, poll_id=None):
        """Send notification for poll events (new poll, poll closed)"""
        from notifications.models import Notification as AppNotification
        from notifications.fcm_service import FCMNotificationService
        notifications = []
        for recipient in recipients:
            notification = Notification.objects.create(
                recipient=recipient,
                notification_type='plan_update',
                title=title,
                message=message,
                plan=None
            )
            notifications.append(notification)
            # Unified feed
            if recipient:
                AppNotification.objects.create(
                    user=recipient,
                    notification_type='poll',
                    message=message,
                    data={"poll_id": poll_id} if poll_id else None
                )
                # Push notification
                device_token = getattr(getattr(recipient, 'profile', None), 'device_token', None)
                if device_token and getattr(settings, 'FCM_SERVER_KEY', None):
                    fcm = FCMNotificationService(settings.FCM_SERVER_KEY)
                    fcm.send_notification(
                        registration_id=device_token,
                        title=title,
                        body=message,
                        data={"poll_id": poll_id} if poll_id else None
                    )
            # Optionally send email
            try:
                send_mail(
                    title,
                    message,
                    settings.DEFAULT_FROM_EMAIL if hasattr(settings, 'DEFAULT_FROM_EMAIL') else 'noreply@tripvo.com',
                    [recipient.email],
                    fail_silently=True
                )
                notification.sent = True
                notification.save()
            except Exception as e:
                print(f"Failed to send poll notification email: {e}")
        return notifications

    @staticmethod
    def send_expense_notification(expense, plan, members):
        """Send notification for new expense added to a plan"""
        from notifications.models import Notification as AppNotification
        from notifications.fcm_service import FCMNotificationService
        notifications = []
        for member in members:
            notification = Notification.objects.create(
                recipient=member.user,
                recipient_email=member.user.email if member.user else member.guest_email,
                notification_type='plan_update',
                title=f'New Expense Added: {expense.description}',
                message=f'A new expense of {expense.amount} ({expense.category}) was added and split among members.',
                plan=plan
            )
            notifications.append(notification)
            # Unified feed
            if member.user:
                AppNotification.objects.create(
                    user=member.user,
                    notification_type='expense',
                    message=f'A new expense of {expense.amount} ({expense.category}) was added.',
                    data={"plan_id": str(plan.id), "expense_id": str(expense.id)}
                )
                # Push notification
                device_token = getattr(getattr(member.user, 'profile', None), 'device_token', None)
                if device_token and getattr(settings, 'FCM_SERVER_KEY', None):
                    fcm = FCMNotificationService(settings.FCM_SERVER_KEY)
                    fcm.send_notification(
                        registration_id=device_token,
                        title=f'New Expense: {expense.description}',
                        body=f'A new expense of {expense.amount} ({expense.category}) was added.',
                        data={"plan_id": str(plan.id), "expense_id": str(expense.id)}
                    )
            try:
                subject = f'New Expense Added to "{plan.title}"'
                message = f"""
Hello {member.user.get_full_name() if member.user else member.guest_name},

A new expense was added to the plan "{plan.title}":
- Description: {expense.description}
- Amount: {expense.amount}
- Category: {expense.category}

Check your balance and settle up!

Best regards,
The Tripvo Team
"""
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL if hasattr(settings, 'DEFAULT_FROM_EMAIL') else 'noreply@tripvo.com',
                    [member.user.email if member.user else member.guest_email],
                    fail_silently=True
                )
                notification.sent = True
                notification.save()
            except Exception as e:
                print(f"Failed to send expense notification email: {e}")
        return notifications

from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from .models import Notification


class NotificationService:
    """Service for handling notifications and emails"""
    
    @staticmethod
    def send_plan_invite(plan, member, inviter):
        """Send invitation notification to a new plan member"""
        from notifications.models import Notification as AppNotification
        from notifications.fcm_service import FCMNotificationService
        # Determine recipient
        recipient_user = member.user
        recipient_email = member.user.email if member.user else member.guest_email
        recipient_name = member.guest_name if member.is_guest() else member.user.get_full_name()
        # Create notification
        notification = Notification.objects.create(
            recipient=recipient_user,
            recipient_email=recipient_email,
            notification_type='plan_invite',
            title=f'Invitation to join "{plan.title}"',
            message=f'{inviter.get_full_name() or inviter.username} has invited you to join the plan "{plan.title}".',
            plan=plan
        )
        # Unified feed
        if recipient_user:
            AppNotification.objects.create(
                user=recipient_user,
                notification_type='member',
                message=f'{inviter.get_full_name() or inviter.username} has invited you to join the plan "{plan.title}".',
                data={"plan_id": str(plan.id)}
            )
            # Push notification
            device_token = getattr(getattr(recipient_user, 'profile', None), 'device_token', None)
            if device_token and getattr(settings, 'FCM_SERVER_KEY', None):
                fcm = FCMNotificationService(settings.FCM_SERVER_KEY)
                fcm.send_notification(
                    registration_id=device_token,
                    title=f'Plan Invitation',
                    body=f'{inviter.get_full_name() or inviter.username} invited you to join "{plan.title}".',
                    data={"plan_id": str(plan.id)}
                )
        # Send email
        try:
            subject = f'You\'ve been invited to join "{plan.title}" on Tripvo'
            message = f'''
Hello {recipient_name or 'there'},

{inviter.get_full_name() or inviter.username} has invited you to join the plan "{plan.title}" on Tripvo.

Plan Details:
- Title: {plan.title}
- Category: {plan.get_category_display()}
- Description: {plan.description or 'No description provided'}

Click the link below to join:
{plan.get_invite_link()}

Best regards,
The Tripvo Team
            '''
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL if hasattr(settings, 'DEFAULT_FROM_EMAIL') else 'noreply@tripvo.com',
                [recipient_email],
                fail_silently=True
            )
            notification.sent = True
            notification.save()
        except Exception as e:
            print(f"Failed to send email: {e}")
        return notification
    
    @staticmethod
    def send_member_joined(plan, member, recipient):
        """Notify creator/admins when a new member joins"""
        from notifications.models import Notification as AppNotification
        from notifications.fcm_service import FCMNotificationService
        member_name = member.guest_name if member.is_guest() else member.user.get_full_name() or member.user.username
        # Create notification
        notification = Notification.objects.create(
            recipient=recipient,
            notification_type='member_joined',
            title=f'New member joined "{plan.title}"',
            message=f'{member_name} has joined your plan "{plan.title}".',
            plan=plan
        )
        # Unified feed
        if recipient:
            AppNotification.objects.create(
                user=recipient,
                notification_type='member',
                message=f'{member_name} has joined your plan "{plan.title}".',
                data={"plan_id": str(plan.id)}
            )
            # Push notification
            device_token = getattr(getattr(recipient, 'profile', None), 'device_token', None)
            if device_token and getattr(settings, 'FCM_SERVER_KEY', None):
                fcm = FCMNotificationService(settings.FCM_SERVER_KEY)
                fcm.send_notification(
                    registration_id=device_token,
                    title=f'New member joined',
                    body=f'{member_name} joined your plan "{plan.title}".',
                    data={"plan_id": str(plan.id)}
                )
        # Send email
        try:
            subject = f'New member joined "{plan.title}"'
            message = f'''
Hello {recipient.get_full_name() or recipient.username},

{member_name} has joined your plan "{plan.title}".

Plan: {plan.title}
Category: {plan.get_category_display()}

View your plan at: /plans/{plan.id}

Best regards,
The Tripvo Team
            '''
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL if hasattr(settings, 'DEFAULT_FROM_EMAIL') else 'noreply@tripvo.com',
                [recipient.email],
                fail_silently=True
            )
            notification.sent = True
            notification.save()
        except Exception as e:
            print(f"Failed to send email: {e}")
        return notification
    
    @staticmethod
    def send_plan_update(plan, message_text, recipients):
        """Send plan update notification to members"""
        notifications = []
        
        for recipient in recipients:
            notification = Notification.objects.create(
                recipient=recipient,
                notification_type='plan_update',
                title=f'Update to "{plan.title}"',
                message=message_text,
                plan=plan
            )
            notifications.append(notification)
            
            # Send email
            try:
                subject = f'Update to "{plan.title}"'
                message = f'''
Hello {recipient.get_full_name() or recipient.username},

There has been an update to the plan "{plan.title}":

{message_text}

View the plan at: /plans/{plan.id}

Best regards,
The Tripvo Team
                '''
                
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL if hasattr(settings, 'DEFAULT_FROM_EMAIL') else 'noreply@tripvo.com',
                    [recipient.email],
                    fail_silently=True
                )
                
                notification.sent = True
                notification.save()
            except Exception as e:
                print(f"Failed to send email: {e}")
        
        return notifications
