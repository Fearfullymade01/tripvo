from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import uuid


class Plan(models.Model):
    """
    Model for group plans (trips, events, family activities, etc.)
    """
    CATEGORY_CHOICES = [
        ('travel', 'Travel'),
        ('event', 'Event'),
        ('family', 'Family'),
        ('custom', 'Custom'),
    ]
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='custom')
    description = models.TextField(blank=True)
    
    # Dates
    start_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)
    
    # Creator and status
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_plans')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Invite link
    invite_token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['creator']),
            models.Index(fields=['category']),
        ]
    
    def __str__(self):
        return f"{self.title} ({self.get_category_display()})"
    
    def get_invite_link(self):
        """Generate shareable invite link"""
        # This would need to be configured with your domain
        return f"/invite/{self.invite_token}"


class PlanMember(models.Model):
    """
    Model for plan members (both registered users and guests)
    """
    ROLE_CHOICES = [
        ('creator', 'Creator'),
        ('admin', 'Admin'),
        ('member', 'Member'),
        ('guest', 'Guest'),
    ]
    
    STATUS_CHOICES = [
        ('invited', 'Invited'),
        ('active', 'Active'),
        ('declined', 'Declined'),
        ('removed', 'Removed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    plan = models.ForeignKey(Plan, on_delete=models.CASCADE, related_name='members')
    
    # User relationship (null for guests)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='plan_memberships')
    
    # Guest information
    guest_name = models.CharField(max_length=100, blank=True)
    guest_email = models.EmailField(blank=True)
    
    # Member details
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='member')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='invited')
    
    # Invite tracking
    invited_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='sent_invites')
    invited_at = models.DateTimeField(auto_now_add=True)
    joined_at = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['plan', 'user'],
                condition=models.Q(user__isnull=False),
                name='unique_plan_user'
            ),
            models.UniqueConstraint(
                fields=['plan', 'guest_email'],
                condition=models.Q(guest_email__gt=''),
                name='unique_plan_guest_email'
            ),
        ]
        indexes = [
            models.Index(fields=['plan', 'status']),
            models.Index(fields=['user']),
        ]
    
    def __str__(self):
        if self.user:
            return f"{self.user.username} - {self.plan.title}"
        return f"{self.guest_name or self.guest_email} (Guest) - {self.plan.title}"
    
    def accept_invite(self):
        """Accept invitation and mark as active"""
        self.status = 'active'
        self.joined_at = timezone.now()
        self.save()
    
    def is_guest(self):
        """Check if member is a guest"""
        return self.user is None


class Notification(models.Model):
    """
    Model for user notifications
    """
    TYPE_CHOICES = [
        ('plan_invite', 'Plan Invitation'),
        ('plan_update', 'Plan Update'),
        ('member_joined', 'Member Joined'),
        ('member_left', 'Member Left'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications', null=True, blank=True)
    recipient_email = models.EmailField(blank=True)  # For guest notifications
    
    notification_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    
    # Related objects
    plan = models.ForeignKey(Plan, on_delete=models.CASCADE, null=True, blank=True)
    
    # Status
    is_read = models.BooleanField(default=False)
    sent = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', '-created_at']),
            models.Index(fields=['is_read']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.recipient or self.recipient_email}"
    
    def mark_as_read(self):
        """Mark notification as read"""
        self.is_read = True
        self.read_at = timezone.now()
        self.save()


class ItineraryItem(models.Model):
    """
    Model for itinerary/schedule items within a plan
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    plan = models.ForeignKey(Plan, on_delete=models.CASCADE, related_name='itinerary_items')
    
    # Item details
    title = models.CharField(max_length=200)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    location = models.CharField(max_length=300, blank=True)
    notes = models.TextField(blank=True)
    
    # Creator and tracking
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_itinerary_items')
    
    # Conflict tracking
    has_conflict = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Versioning for offline sync
    version = models.IntegerField(default=1)
    
    class Meta:
        ordering = ['start_time', 'created_at']
        indexes = [
            models.Index(fields=['plan', 'start_time']),
            models.Index(fields=['start_time', 'end_time']),
            models.Index(fields=['has_conflict']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.start_time.strftime('%Y-%m-%d %H:%M')}"
    
    def check_conflicts(self):
        """Check for time conflicts with other itinerary items in the same plan"""
        conflicts = ItineraryItem.objects.filter(
            plan=self.plan,
            start_time__lt=self.end_time,
            end_time__gt=self.start_time
        ).exclude(id=self.id)
        
        self.has_conflict = conflicts.exists()
        self.save(update_fields=['has_conflict'])
        
        # Update conflict status for overlapping items
        for item in conflicts:
            if not item.has_conflict:
                item.has_conflict = True
                item.save(update_fields=['has_conflict'])
        
        return conflicts
    
    def duration_minutes(self):
        """Calculate duration in minutes"""
        delta = self.end_time - self.start_time
        return int(delta.total_seconds() / 60)


class ItemComment(models.Model):
    """
    Model for comments on itinerary items
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    itinerary_item = models.ForeignKey(ItineraryItem, on_delete=models.CASCADE, related_name='comments')
    
    # Comment content
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='itinerary_comments')
    author_name = models.CharField(max_length=100, blank=True)  # For guest users
    content = models.TextField()
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['itinerary_item', 'created_at']),
        ]
    
    def __str__(self):
        author = self.author.username if self.author else self.author_name or 'Anonymous'
        return f"Comment by {author} on {self.itinerary_item.title}"
