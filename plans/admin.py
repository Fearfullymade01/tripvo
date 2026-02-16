from django.contrib import admin
from .models import Plan, PlanMember, Notification, ItineraryItem, ItemComment


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'creator', 'status', 'start_date', 'created_at']
    list_filter = ['category', 'status', 'created_at']
    search_fields = ['title', 'description', 'creator__username']
    readonly_fields = ['id', 'invite_token', 'created_at', 'updated_at']
    date_hierarchy = 'created_at'


@admin.register(PlanMember)
class PlanMemberAdmin(admin.ModelAdmin):
    list_display = ['get_member_name', 'plan', 'role', 'status', 'joined_at']
    list_filter = ['role', 'status', 'created_at']
    search_fields = ['user__username', 'guest_name', 'guest_email', 'plan__title']
    readonly_fields = ['id', 'invited_at', 'created_at', 'updated_at']
    
    def get_member_name(self, obj):
        if obj.user:
            return obj.user.username
        return f"{obj.guest_name or obj.guest_email} (Guest)"
    get_member_name.short_description = 'Member'


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['title', 'get_recipient', 'notification_type', 'is_read', 'sent', 'created_at']
    list_filter = ['notification_type', 'is_read', 'sent', 'created_at']
    search_fields = ['title', 'message', 'recipient__username', 'recipient_email']
    readonly_fields = ['id', 'created_at', 'read_at']
    date_hierarchy = 'created_at'
    
    def get_recipient(self, obj):
        if obj.recipient:
            return obj.recipient.username
        return obj.recipient_email
    get_recipient.short_description = 'Recipient'


@admin.register(ItineraryItem)
class ItineraryItemAdmin(admin.ModelAdmin):
    list_display = ['title', 'plan', 'start_time', 'end_time', 'location', 'has_conflict', 'created_by']
    list_filter = ['has_conflict', 'start_time', 'created_at']
    search_fields = ['title', 'location', 'notes', 'plan__title']
    readonly_fields = ['id', 'has_conflict', 'version', 'created_at', 'updated_at']
    date_hierarchy = 'start_time'
    ordering = ['plan', 'start_time']


@admin.register(ItemComment)
class ItemCommentAdmin(admin.ModelAdmin):
    list_display = ['get_author_name', 'itinerary_item', 'content_preview', 'created_at']
    list_filter = ['created_at']
    search_fields = ['content', 'author__username', 'author_name', 'itinerary_item__title']
    readonly_fields = ['id', 'created_at', 'updated_at']
    date_hierarchy = 'created_at'
    
    def get_author_name(self, obj):
        if obj.author:
            return obj.author.username
        return obj.author_name or 'Anonymous'
    get_author_name.short_description = 'Author'
    
    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Content'
