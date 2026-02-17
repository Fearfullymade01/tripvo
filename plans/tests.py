from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
 
from django.utils import timezone
from datetime import timedelta
from plans.models import Plan, PlanMember, Notification, ItineraryItem


class PlanModelTest(TestCase):
    """Test Plan model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_create_plan(self):
        """Test creating a plan"""
        plan = Plan.objects.create(
            title='Test Trip',
            category='travel',
            creator=self.user
        )
        self.assertEqual(plan.title, 'Test Trip')
        self.assertEqual(plan.category, 'travel')
        self.assertEqual(plan.creator, self.user)
        self.assertIsNotNone(plan.invite_token)
    
    def test_plan_str(self):
        """Test plan string representation"""
        plan = Plan.objects.create(
            title='Test Trip',
            category='travel',
            creator=self.user
        )
        
        self.assertEqual(str(plan), 'Test Trip (Travel)')
    
    def test_get_invite_link(self):
        """Test invite link generation"""
        plan = Plan.objects.create(
            title='Test Trip',
            category='travel',
            creator=self.user
        )
        
        invite_link = plan.get_invite_link()
        self.assertIn(str(plan.invite_token), invite_link)


class PlanMemberModelTest(TestCase):
    """Test PlanMember model"""
    
    def setUp(self):
        self.creator = User.objects.create_user(
            username='creator',
            email='creator@example.com',
            password='pass123'
        )
        self.member = User.objects.create_user(
            username='member',
            email='member@example.com',
            password='pass123'
        )
        self.plan = Plan.objects.create(
            title='Test Plan',
            category='event',
            creator=self.creator
        )
    
    def test_create_member(self):
        """Test creating a plan member"""
        plan_member = PlanMember.objects.create(
            plan=self.plan,
            user=self.member,
            role='member',
            status='invited',
            invited_by=self.creator
        )
        
        self.assertEqual(plan_member.user, self.member)
        self.assertEqual(plan_member.role, 'member')
        self.assertEqual(plan_member.status, 'invited')
    
    def test_create_guest_member(self):
        """Test creating a guest member"""
        guest_member = PlanMember.objects.create(
            plan=self.plan,
            guest_name='John Doe',
            guest_email='john@example.com',
            role='guest',
            status='invited',
            invited_by=self.creator
        )
        
        self.assertIsNone(guest_member.user)
        self.assertEqual(guest_member.guest_email, 'john@example.com')
        self.assertTrue(guest_member.is_guest())
    
    def test_accept_invite(self):
        """Test accepting an invitation"""
        plan_member = PlanMember.objects.create(
            plan=self.plan,
            user=self.member,
            role='member',
            status='invited',
            invited_by=self.creator
        )
        
        plan_member.accept_invite()
        
        self.assertEqual(plan_member.status, 'active')
        self.assertIsNotNone(plan_member.joined_at)


class PlanAPITest(APITestCase):
    """Test Plan API endpoints"""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='pass123'
        )
    
    def test_create_plan_authenticated(self):
        """Test creating a plan when authenticated"""
        self.client.force_authenticate(user=self.user)
        
        data = {
            'title': 'Beach Vacation',
            'category': 'travel',
            'description': 'Summer beach trip',
            'start_date': '2026-07-01T10:00:00Z',
            'end_date': '2026-07-10T10:00:00Z'
        }
        
        response = self.client.post('/api/plans/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['title'], 'Beach Vacation')
        self.assertEqual(response.data['category'], 'travel')
        
        # Check creator was added as member
        plan = Plan.objects.get(id=response.data['id'])
        self.assertTrue(
            PlanMember.objects.filter(
                plan=plan,
                user=self.user,
                role='creator'
            ).exists()
        )
    
    def test_create_plan_unauthenticated(self):
        """Test creating a plan when not authenticated"""
        data = {
            'title': 'Beach Vacation',
            'category': 'travel'
        }
        
        response = self.client.post('/api/plans/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_list_plans(self):
        """Test listing plans"""
        self.client.force_authenticate(user=self.user)
        
        # Create plans
        Plan.objects.create(
            title='Plan 1',
            category='travel',
            creator=self.user
        )
        plan2 = Plan.objects.create(
            title='Plan 2',
            category='event',
            creator=self.other_user
        )
        
        # Add user as member to plan2
        PlanMember.objects.create(
            plan=plan2,
            user=self.user,
            role='member',
            status='active'
        )
        
        response = self.client.get('/api/plans/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)
    
    def test_invite_member_email(self):
        """Test inviting a member by email"""
        self.client.force_authenticate(user=self.user)
        
        plan = Plan.objects.create(
            title='Test Plan',
            category='event',
            creator=self.user
        )
        
        data = {
            'email': 'newuser@example.com',
            'name': 'New User',
            'role': 'member'
        }
        
        response = self.client.post(
            f'/api/plans/{plan.id}/invite/',
            data,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Check member was created
        member = PlanMember.objects.get(
            plan=plan,
            guest_email='newuser@example.com'
        )
        self.assertEqual(member.guest_name, 'New User')
        self.assertEqual(member.status, 'invited')
    
    def test_invite_existing_user(self):
        """Test inviting an existing user"""
        self.client.force_authenticate(user=self.user)
        
        plan = Plan.objects.create(
            title='Test Plan',
            category='event',
            creator=self.user
        )
        
        data = {
            'email': self.other_user.email,
            'role': 'member'
        }
        
        response = self.client.post(
            f'/api/plans/{plan.id}/invite/',
            data,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Check member was created with user link
        member = PlanMember.objects.get(
            plan=plan,
            user=self.other_user
        )
        self.assertEqual(member.status, 'invited')
    
    def test_join_plan_with_token(self):
        """Test joining a plan with invite token"""
        plan = Plan.objects.create(
            title='Test Plan',
            category='event',
            creator=self.user
        )
        
        self.client.force_authenticate(user=self.other_user)
        
        response = self.client.post(
            f'/api/plans/{plan.id}/join/{str(plan.invite_token)}/',
            {},
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Check member was created
        member = PlanMember.objects.get(
            plan=plan,
            user=self.other_user
        )
        self.assertEqual(member.status, 'active')
        self.assertIsNotNone(member.joined_at)
    
    def test_join_plan_as_guest(self):
        """Test joining a plan as guest"""
        plan = Plan.objects.create(
            title='Test Plan',
            category='event',
            creator=self.user
        )
        
        data = {
            'name': 'Guest User',
            'email': 'guest@example.com'
        }
        
        response = self.client.post(
            f'/api/plans/{plan.id}/join/{str(plan.invite_token)}/',
            data,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Check guest member was created
        member = PlanMember.objects.get(
            plan=plan,
            guest_email='guest@example.com'
        )
        self.assertEqual(member.guest_name, 'Guest User')
        self.assertEqual(member.status, 'active')
        self.assertTrue(member.is_guest())
    
    def test_get_plan_members(self):
        """Test getting plan members"""
        self.client.force_authenticate(user=self.user)
        
        plan = Plan.objects.create(
            title='Test Plan',
            category='event',
            creator=self.user
        )
        
        # Add members (with unique emails to avoid constraint)
        PlanMember.objects.create(
            plan=plan,
            user=self.user,
            role='creator',
            status='active',
            guest_email=''
        )
        PlanMember.objects.create(
            plan=plan,
            user=self.other_user,
            role='member',
            status='active',
            guest_email=''
        )
        
        response = self.client.get(f'/api/plans/{plan.id}/members/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
    
    def test_remove_member(self):
        """Test removing a member from plan"""
        self.client.force_authenticate(user=self.user)
        
        plan = Plan.objects.create(
            title='Test Plan',
            category='event',
            creator=self.user
        )
        
        member = PlanMember.objects.create(
            plan=plan,
            user=self.other_user,
            role='member',
            status='active'
        )
        
        response = self.client.delete(
            f'/api/plans/{plan.id}/members/{member.id}/'
        )
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        # Check member was marked as removed
        member.refresh_from_db()
        self.assertEqual(member.status, 'removed')


class NotificationTest(TestCase):
    """Test Notification functionality"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='pass123'
        )
        self.plan = Plan.objects.create(
            title='Test Plan',
            category='event',
            creator=self.user
        )
    
    def test_create_notification(self):
        """Test creating a notification"""
        notification = Notification.objects.create(
            recipient=self.user,
            notification_type='plan_invite',
            title='Test Notification',
            message='This is a test',
            plan=self.plan
        )
        
        self.assertEqual(notification.recipient, self.user)
        self.assertFalse(notification.is_read)
        self.assertFalse(notification.sent)
    
    def test_mark_notification_as_read(self):
        """Test marking notification as read"""
        notification = Notification.objects.create(
            recipient=self.user,
            notification_type='plan_invite',
            title='Test Notification',
            message='This is a test',
            plan=self.plan
        )
        
        notification.mark_as_read()
        
        self.assertTrue(notification.is_read)
        self.assertIsNotNone(notification.read_at)


class ItineraryItemTest(APITestCase):
    """Test itinerary item CRUD and conflict detection"""
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='itineraryuser',
            email='itinerary@example.com',
            password='testpass123'
        )
        self.plan = Plan.objects.create(
            title='Test Plan',
            category='event',
            creator=self.user
        )
        PlanMember.objects.create(
            plan=self.plan,
            user=self.user,
            role='creator',
            status='active'
        )
        self.client.force_authenticate(user=self.user)

    def test_create_itinerary_item(self):
        """Test creating an itinerary item"""
        start = timezone.now() + timedelta(days=1)
        end = start + timedelta(hours=2)
        data = {
            'plan': str(self.plan.id),
            'title': 'Check In',
            'start_time': start.isoformat(),
            'end_time': end.isoformat(),
            'location': 'Hotel',
            'notes': 'Arrive early'
        }
        response = self.client.post('/api/itinerary/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['title'], 'Check In')
        self.assertEqual(response.data['location'], 'Hotel')

    def test_conflict_detection(self):
        """Test conflict detection for overlapping items"""
        start1 = timezone.now() + timedelta(days=1, hours=8)
        end1 = start1 + timedelta(hours=2)
        item1 = ItineraryItem.objects.create(
            plan=self.plan,
            title='Breakfast',
            start_time=start1,
            end_time=end1,
            created_by=self.user
        )
        start2 = start1 + timedelta(hours=1)
        end2 = start2 + timedelta(hours=2)
        item2 = ItineraryItem.objects.create(
            plan=self.plan,
            title='Tour',
            start_time=start2,
            end_time=end2,
            created_by=self.user
        )
        item2.check_conflicts()
        item1.refresh_from_db()
        item2.refresh_from_db()
        self.assertTrue(item1.has_conflict)
        self.assertTrue(item2.has_conflict)

    def test_list_itinerary_items(self):
        """Test listing itinerary items for a plan"""
        for i in range(3):
            ItineraryItem.objects.create(
                plan=self.plan,
                title=f'Item {i+1}',
                start_time=timezone.now() + timedelta(days=1, hours=i),
                end_time=timezone.now() + timedelta(days=1, hours=i+1),
                created_by=self.user
            )
        response = self.client.get(f'/api/itinerary/?plan={self.plan.id}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 3)

    def test_comment_on_itinerary_item(self):
        """Test adding a comment to an itinerary item"""
        start = timezone.now() + timedelta(days=1)
        end = start + timedelta(hours=2)
        item = ItineraryItem.objects.create(
            plan=self.plan,
            title='Lunch',
            start_time=start,
            end_time=end,
            created_by=self.user
        )
        data = {
            'itinerary_item': str(item.id),
            'content': 'Let’s meet at the lobby.'
        }
        response = self.client.post('/api/comments/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['content'], 'Let’s meet at the lobby.')
        self.assertEqual(str(response.data['itinerary_item']), str(item.id))

    def test_calendar_view(self):
        """Test calendar endpoint for itinerary items"""
        for i in range(2):
            ItineraryItem.objects.create(
                plan=self.plan,
                title=f'Event {i+1}',
                start_time=timezone.now() + timedelta(days=2, hours=i),
                end_time=timezone.now() + timedelta(days=2, hours=i+1),
                created_by=self.user
            )
        response = self.client.get(f'/api/itinerary/calendar/?plan={self.plan.id}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 2)

    def test_offline_edit_versioning(self):
        """Test version increment on update (for offline sync)"""
        start = timezone.now() + timedelta(days=1)
        end = start + timedelta(hours=2)
        item = ItineraryItem.objects.create(
            plan=self.plan,
            title='Dinner',
            start_time=start,
            end_time=end,
            created_by=self.user
        )
        orig_version = item.version
        data = {
            'notes': 'Updated notes'
        }
        response = self.client.patch(f'/api/itinerary/{item.id}/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        item.refresh_from_db()
        self.assertEqual(item.version, orig_version + 1)
        self.assertEqual(item.notes, 'Updated notes')


class DashboardAggregationTest(APITestCase):
    """Test dashboard aggregation endpoint"""
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='dashboarduser',
            email='dashboard@example.com',
            password='testpass123'
        )
        self.plan = Plan.objects.create(
            title='Dashboard Plan',
            category='event',
            creator=self.user,
            status='active'
        )
        PlanMember.objects.create(
            plan=self.plan,
            user=self.user,
            role='creator',
            status='active'
        )
        self.client.force_authenticate(user=self.user)
        # Create itinerary event
        start = timezone.now() + timedelta(days=2)
        end = start + timedelta(hours=1)
        ItineraryItem.objects.create(
            plan=self.plan,
            title='Dashboard Event',
            start_time=start,
            end_time=end,
            created_by=self.user
        )
        # Create notification (pending poll)
        Notification.objects.create(
            recipient=self.user,
            notification_type='poll',
            title='Dashboard Poll',
            message='Vote now!',
            plan=self.plan,
            is_read=False
        )

    def test_dashboard_endpoint(self):
        response = self.client.get('/api/dashboard/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('active_plans', response.data)
        self.assertIn('upcoming_events', response.data)
        self.assertIn('pending_polls', response.data)
        self.assertIn('outstanding_expenses', response.data)
        self.assertGreaterEqual(len(response.data['active_plans']), 1)
        self.assertGreaterEqual(len(response.data['upcoming_events']), 1)
        self.assertGreaterEqual(len(response.data['pending_polls']), 1)
