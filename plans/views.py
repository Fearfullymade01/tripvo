from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from django.http import JsonResponse
# Poll notification endpoint for FastAPI integration
class PollNotifyView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        event = request.data.get("event")
        poll = request.data.get("poll")
        if not poll or not event:
            return JsonResponse({"error": "Missing event or poll"}, status=400)
        # For demo, notify all users
        users = User.objects.all()
        title = f"New Poll: {poll.get('question')}" if event == "new" else f"Poll Closed: {poll.get('question')}"
        message = f"A poll was {'created' if event == 'new' else 'closed'}: {poll.get('question')}"
        NotificationService.send_poll_notification(title, message, users)
        return JsonResponse({"status": "ok"})
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.utils import timezone
from .models import Plan, PlanMember, Notification, ItineraryItem, ItemComment
from .serializers import (
    PlanSerializer, PlanListSerializer, PlanMemberSerializer,
    InviteMemberSerializer, NotificationSerializer,
    ItineraryItemSerializer, ItineraryItemListSerializer, ItemCommentSerializer
)
from .services import NotificationService

class PlanViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing plans
    """
    serializer_class = PlanSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    
    def get_queryset(self):
        """Return plans user created or is a member of"""
        user = self.request.user
        if user.is_authenticated:
            return Plan.objects.filter(
                Q(creator=user) | Q(members__user=user)
            ).distinct()
        return Plan.objects.none()
    
    def get_serializer_class(self):
        """Use lightweight serializer for list view"""
        if self.action == 'list':
            return PlanListSerializer
        return PlanSerializer
    
    def perform_create(self, serializer):
        """Create plan and set creator"""
        serializer.save(creator=self.request.user)
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def invite(self, request, pk=None):
        """
        Invite members to a plan via email
        POST /api/plans/{id}/invite/
        Body: {
            "email": "user@example.com",
            "name": "John Doe",
            "role": "member"
        }
        """
        plan = self.get_object()
        
        # Check if user has permission to invite
        if not self._can_manage_members(request.user, plan):
            return Response(
                {'error': 'You do not have permission to invite members'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = InviteMemberSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        email = serializer.validated_data['email']
        name = serializer.validated_data.get('name', '')
        role = serializer.validated_data.get('role', 'member')
        
        # Check if user with email exists
        try:
            user = User.objects.get(email=email)
            # Check if already a member
            if PlanMember.objects.filter(plan=plan, user=user).exists():
                return Response(
                    {'error': 'User is already a member of this plan'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Create member record
            member = PlanMember.objects.create(
                plan=plan,
                user=user,
                role=role,
                status='invited',
                invited_by=request.user
            )
        except User.DoesNotExist:
            # Create guest member
            if PlanMember.objects.filter(plan=plan, guest_email=email).exists():
                return Response(
                    {'error': 'This email has already been invited'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            member = PlanMember.objects.create(
                plan=plan,
                guest_name=name,
                guest_email=email,
                role='guest' if role == 'guest' else 'member',
                status='invited',
                invited_by=request.user
            )
        
        # Send notification
        NotificationService.send_plan_invite(plan, member, request.user)
        
        return Response(
            PlanMemberSerializer(member).data,
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=False, methods=['post'], url_path=r'(?P<plan_id>[^/.]+)/join/(?P<token>[^/.]+)',
            permission_classes=[permissions.AllowAny])
    def join_plan(self, request, plan_id=None, token=None):
        """
        Join a plan via invite link
        POST /api/plans/{plan_id}/join/{token}/
        Body (optional for guest): {
            "name": "John Doe",
            "email": "john@example.com"
        }
        """
        plan = get_object_or_404(Plan, id=plan_id)
        
        # Verify token
        if str(plan.invite_token) != token:
            return Response(
                {'error': 'Invalid invite link'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if authenticated user
        if request.user.is_authenticated:
            # Check if already a member
            member, created = PlanMember.objects.get_or_create(
                plan=plan,
                user=request.user,
                defaults={
                    'role': 'member',
                    'status': 'active',
                    'invited_by': plan.creator,
                    'joined_at': timezone.now()
                }
            )
            
            if not created:
                if member.status == 'invited':
                    member.accept_invite()
                return Response({'message': 'Already a member of this plan'})
            
            # Send notification to creator
            NotificationService.send_member_joined(plan, member, plan.creator)
            
            return Response(
                PlanMemberSerializer(member).data,
                status=status.HTTP_201_CREATED
            )
        
        # Guest user
        name = request.data.get('name', '')
        email = request.data.get('email', '')
        
        if not email:
            return Response(
                {'error': 'Email is required for guest access'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if guest already exists
        member, created = PlanMember.objects.get_or_create(
            plan=plan,
            guest_email=email,
            defaults={
                'guest_name': name,
                'role': 'guest',
                'status': 'active',
                'invited_by': plan.creator,
                'joined_at': timezone.now()
            }
        )
        
        if not created:
            if member.status == 'invited':
                member.accept_invite()
            return Response({'message': 'Already a member of this plan'})
        
        # Send notification to creator
        NotificationService.send_member_joined(plan, member, plan.creator)
        
        return Response(
            PlanMemberSerializer(member).data,
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=True, methods=['get'])
    def members(self, request, pk=None):
        """
        Get all members of a plan
        GET /api/plans/{id}/members/
        """
        plan = self.get_object()
        members = plan.members.filter(status__in=['invited', 'active'])
        serializer = PlanMemberSerializer(members, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['delete'], url_path='members/(?P<member_id>[^/.]+)')
    def remove_member(self, request, pk=None, member_id=None):
        """
        Remove a member from the plan
        DELETE /api/plans/{id}/members/{member_id}/
        """
        plan = self.get_object()
        
        # Check permission
        if not self._can_manage_members(request.user, plan):
            return Response(
                {'error': 'You do not have permission to remove members'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        member = get_object_or_404(PlanMember, id=member_id, plan=plan)
        
        # Cannot remove creator
        if member.role == 'creator':
            return Response(
                {'error': 'Cannot remove the plan creator'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        member.status = 'removed'
        member.save()
        
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    def _can_manage_members(self, user, plan):
        """Check if user can manage plan members"""
        if plan.creator == user:
            return True
        
        try:
            member = PlanMember.objects.get(plan=plan, user=user)
            return member.role in ['creator', 'admin']
        except PlanMember.DoesNotExist:
            return False


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing notifications
    """
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Return notifications for current user"""
        return Notification.objects.filter(recipient=self.request.user)
    
    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        """
        Mark notification as read
        POST /api/notifications/{id}/mark_read/
        """
        notification = self.get_object()
        notification.mark_as_read()
        return Response({'status': 'marked as read'})
    
    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        """
        Mark all notifications as read
        POST /api/notifications/mark_all_read/
        """
        count = self.get_queryset().filter(is_read=False).update(is_read=True)
        return Response({'status': f'{count} notifications marked as read'})


class ItineraryItemViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing itinerary/schedule items
    """
    serializer_class = ItineraryItemSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    
    def get_queryset(self):
        """Return itinerary items for plans the user is a member of"""
        user = self.request.user
        plan_id = self.request.query_params.get('plan')
        
        if user.is_authenticated:
            queryset = ItineraryItem.objects.filter(
                Q(plan__creator=user) | Q(plan__members__user=user)
            ).distinct()
            
            if plan_id:
                queryset = queryset.filter(plan_id=plan_id)
            
            return queryset.select_related('plan', 'created_by').prefetch_related('comments')
        
        return ItineraryItem.objects.none()
    
    def get_serializer_class(self):
        """Use lightweight serializer for list view"""
        if self.action == 'list':
            return ItineraryItemListSerializer
        return ItineraryItemSerializer
    
    @action(detail=False, methods=['get'])
    def conflicts(self, request):
        """
        Get all itinerary items with time conflicts
        GET /api/itinerary/conflicts/?plan={plan_id}
        """
        plan_id = request.query_params.get('plan')
        if not plan_id:
            return Response(
                {'error': 'plan parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        conflicts = self.get_queryset().filter(
            plan_id=plan_id,
            has_conflict=True
        )
        
        serializer = ItineraryItemListSerializer(conflicts, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def check_conflicts(self, request, pk=None):
        """
        Manually trigger conflict check for an item
        POST /api/itinerary/{id}/check_conflicts/
        """
        item = self.get_object()
        conflicts = item.check_conflicts()
        
        return Response({
            'has_conflict': item.has_conflict,
            'conflict_count': conflicts.count(),
            'conflicts': [str(c.id) for c in conflicts]
        })
    
    @action(detail=False, methods=['get'])
    def calendar(self, request):
        """
        Get itinerary items in calendar format
        GET /api/itinerary/calendar/?plan={plan_id}&start={date}&end={date}
        """
        plan_id = request.query_params.get('plan')
        start_date = request.query_params.get('start')
        end_date = request.query_params.get('end')
        
        if not plan_id:
            return Response(
                {'error': 'plan parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        queryset = self.get_queryset().filter(plan_id=plan_id)
        
        if start_date:
            queryset = queryset.filter(start_time__gte=start_date)
        if end_date:
            queryset = queryset.filter(start_time__lte=end_date)
        
        serializer = ItineraryItemListSerializer(queryset, many=True)
        return Response(serializer.data)


class ItemCommentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing comments on itinerary items
    """
    serializer_class = ItemCommentSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    
    def get_queryset(self):
        """Return comments for itinerary items the user can access"""
        user = self.request.user
        itinerary_id = self.request.query_params.get('itinerary_item')
        
        if user.is_authenticated:
            queryset = ItemComment.objects.filter(
                Q(itinerary_item__plan__creator=user) |
                Q(itinerary_item__plan__members__user=user)
            ).distinct()
            
            if itinerary_id:
                queryset = queryset.filter(itinerary_item_id=itinerary_id)
            
            return queryset.select_related('itinerary_item', 'author')
        
        return ItemComment.objects.none()
    
    def perform_create(self, serializer):
        """Set author from request user"""
        if self.request.user.is_authenticated:
            serializer.save(author=self.request.user)
        else:
            serializer.save()
