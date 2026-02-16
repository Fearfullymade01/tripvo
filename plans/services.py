
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from .models import Notification


class NotificationService:
    """Service for handling notifications and emails"""

    @staticmethod
    def send_poll_notification(title, message, recipients, poll_id=None):
        """Send notification for poll events (new poll, poll closed)"""
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
        
        member_name = member.guest_name if member.is_guest() else member.user.get_full_name() or member.user.username
        
        # Create notification
        notification = Notification.objects.create(
            recipient=recipient,
            notification_type='member_joined',
            title=f'New member joined "{plan.title}"',
            message=f'{member_name} has joined your plan "{plan.title}".',
            plan=plan
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
