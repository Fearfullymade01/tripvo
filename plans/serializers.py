from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Plan, PlanMember, Notification, ItineraryItem, ItemComment


class UserBasicSerializer(serializers.ModelSerializer):
    """Basic user info for nested serialization"""
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']
        read_only_fields = fields


class PlanMemberSerializer(serializers.ModelSerializer):
    """Serializer for plan members"""
    user_info = UserBasicSerializer(source='user', read_only=True)
    member_name = serializers.SerializerMethodField()
    member_email = serializers.SerializerMethodField()
    
    class Meta:
        model = PlanMember
        fields = [
            'id', 'plan', 'user', 'user_info', 'guest_name', 'guest_email',
            'member_name', 'member_email', 'role', 'status', 'invited_by',
            'invited_at', 'joined_at', 'created_at'
        ]
        read_only_fields = ['id', 'invited_at', 'joined_at', 'created_at']
    
    def get_member_name(self, obj):
        if obj.user:
            return obj.user.get_full_name() or obj.user.username
        return obj.guest_name or 'Guest'
    
    def get_member_email(self, obj):
        if obj.user:
            return obj.user.email
        return obj.guest_email


class InviteMemberSerializer(serializers.Serializer):
    """Serializer for inviting members to a plan"""
    email = serializers.EmailField(required=True)
    name = serializers.CharField(max_length=100, required=False, allow_blank=True)
    role = serializers.ChoiceField(
        choices=['admin', 'member', 'guest'],
        default='member'
    )
    
    def validate_email(self, value):
        """Validate email format"""
        return value.lower()


class PlanSerializer(serializers.ModelSerializer):
    """Serializer for Plan model"""
    creator_info = UserBasicSerializer(source='creator', read_only=True)
    members = PlanMemberSerializer(many=True, read_only=True)
    member_count = serializers.SerializerMethodField()
    invite_link = serializers.SerializerMethodField()
    is_creator = serializers.SerializerMethodField()
    
    class Meta:
        model = Plan
        fields = [
            'id', 'title', 'category', 'description', 'start_date', 'end_date',
            'creator', 'creator_info', 'status', 'created_at', 'updated_at',
            'invite_token', 'invite_link', 'members', 'member_count', 'is_creator'
        ]
        read_only_fields = ['id', 'creator', 'invite_token', 'created_at', 'updated_at']
    
    def get_member_count(self, obj):
        return obj.members.filter(status__in=['invited', 'active']).count()
    
    def get_invite_link(self, obj):
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(f'/api/plans/{obj.id}/join/{obj.invite_token}/')
        return obj.get_invite_link()
    
    def get_is_creator(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.creator == request.user
        return False
    
    def create(self, validated_data):
        """Create plan and add creator as admin member"""
        request = self.context.get('request')
        validated_data['creator'] = request.user
        plan = super().create(validated_data)
        
        # Add creator as admin member
        PlanMember.objects.create(
            plan=plan,
            user=request.user,
            role='creator',
            status='active',
            invited_by=request.user,
            joined_at=plan.created_at
        )
        
        return plan


class PlanListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing plans"""
    creator_username = serializers.CharField(source='creator.username', read_only=True)
    member_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Plan
        fields = [
            'id', 'title', 'category', 'description', 'start_date', 'end_date',
            'creator_username', 'status', 'created_at', 'member_count'
        ]
        read_only_fields = fields
    
    def get_member_count(self, obj):
        return obj.members.filter(status__in=['invited', 'active']).count()


class NotificationSerializer(serializers.ModelSerializer):
    """Serializer for notifications"""
    plan_title = serializers.CharField(source='plan.title', read_only=True)
    
    class Meta:
        model = Notification
        fields = [
            'id', 'recipient', 'recipient_email', 'notification_type',
            'title', 'message', 'plan', 'plan_title', 'is_read', 'sent',
            'created_at', 'read_at'
        ]
        read_only_fields = ['id', 'created_at', 'read_at']


class ItemCommentSerializer(serializers.ModelSerializer):
    """Serializer for itinerary item comments"""
    author_name_display = serializers.SerializerMethodField()
    author_info = UserBasicSerializer(source='author', read_only=True)
    
    class Meta:
        model = ItemComment
        fields = [
            'id', 'itinerary_item', 'author', 'author_info', 'author_name',
            'author_name_display', 'content', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_author_name_display(self, obj):
        if obj.author:
            return obj.author.get_full_name() or obj.author.username
        return obj.author_name or 'Anonymous'
    
    def create(self, validated_data):
        """Set author from request user or author_name for guests"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            validated_data['author'] = request.user
        return super().create(validated_data)


class ItineraryItemSerializer(serializers.ModelSerializer):
    """Serializer for itinerary items"""
    created_by_info = UserBasicSerializer(source='created_by', read_only=True)
    comments = ItemCommentSerializer(many=True, read_only=True)
    comment_count = serializers.SerializerMethodField()
    duration_minutes = serializers.SerializerMethodField()
    conflicts = serializers.SerializerMethodField()
    
    class Meta:
        model = ItineraryItem
        fields = [
            'id', 'plan', 'title', 'start_time', 'end_time', 'location', 'notes',
            'created_by', 'created_by_info', 'has_conflict', 'conflicts',
            'created_at', 'updated_at', 'version', 'comments', 'comment_count',
            'duration_minutes'
        ]
        read_only_fields = ['id', 'has_conflict', 'version', 'created_at', 'updated_at']
    
    def get_comment_count(self, obj):
        return obj.comments.count()
    
    def get_duration_minutes(self, obj):
        return obj.duration_minutes()
    
    def get_conflicts(self, obj):
        """Return list of conflicting itinerary item IDs"""
        conflicts = ItineraryItem.objects.filter(
            plan=obj.plan,
            start_time__lt=obj.end_time,
            end_time__gt=obj.start_time
        ).exclude(id=obj.id).values_list('id', flat=True)
        
        return [str(id) for id in conflicts]
    
    def validate(self, data):
        """Validate time ranges and conflicts"""
        start_time = data.get('start_time')
        end_time = data.get('end_time')
        
        if start_time and end_time:
            if start_time >= end_time:
                raise serializers.ValidationError({
                    'end_time': 'End time must be after start time'
                })
        
        return data
    
    def create(self, validated_data):
        """Set creator and check for conflicts"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            validated_data['created_by'] = request.user
        
        item = super().create(validated_data)
        item.check_conflicts()
        return item
    
    def update(self, instance, validated_data):
        """Increment version and check conflicts on update"""
        instance.version += 1
        item = super().update(instance, validated_data)
        item.check_conflicts()
        return item


class ItineraryItemListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing itinerary items"""
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    comment_count = serializers.SerializerMethodField()
    
    class Meta:
        model = ItineraryItem
        fields = [
            'id', 'plan', 'title', 'start_time', 'end_time', 'location',
            'created_by_name', 'has_conflict', 'comment_count', 'created_at'
        ]
        read_only_fields = fields
    
    def get_comment_count(self, obj):
        return obj.comments.count()
