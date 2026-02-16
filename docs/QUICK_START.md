# Quick Start Guide - Testing Plan Creation Feature

## Setup

1. **Create a superuser (if not already done):**

```bash
python manage.py createsuperuser
```

2. **Start the development server:**

```bash
python manage.py runserver
```

3. **Access the admin interface:**
   Navigate to http://127.0.0.1:8000/admin/ and log in.

## Testing the Feature

### Option 1: Using Django Admin

1. Go to http://127.0.0.1:8000/admin/plans/plan/
2. Click "Add Plan"
3. Fill in the details and save
4. View the invite link in the plan details

### Option 2: Using the API

#### 1. Get an authentication token

For testing, you can use Django's session authentication:

```bash
# Login via browser at:
http://127.0.0.1:8000/api-auth/login/
```

#### 2. Create a plan using curl or Postman

**Using curl:**

```bash
# First, get CSRF token and session cookie by visiting
# http://127.0.0.1:8000/api-auth/login/ in browser

curl -X POST http://127.0.0.1:8000/api/plans/ \
  -H "Content-Type: application/json" \
  -H "Cookie: sessionid=<your-session-id>" \
  -H "X-CSRFToken: <your-csrf-token>" \
  -d '{
    "title": "Beach Vacation 2026",
    "category": "travel",
    "description": "Summer family trip",
    "start_date": "2026-07-01T10:00:00Z",
    "end_date": "2026-07-10T10:00:00Z"
  }'
```

**Using Python requests:**

```python
import requests

# Login first
session = requests.Session()
login_url = 'http://127.0.0.1:8000/api-auth/login/'
session.get(login_url)  # Get CSRF token

login_data = {
    'username': 'your_username',
    'password': 'your_password',
    'csrfmiddlewaretoken': session.cookies['csrftoken']
}
session.post(login_url, data=login_data)

# Create a plan
create_url = 'http://127.0.0.1:8000/api/plans/'
plan_data = {
    "title": "Beach Vacation 2026",
    "category": "travel",
    "description": "Summer family trip",
    "start_date": "2026-07-01T10:00:00Z",
    "end_date": "2026-07-10T10:00:00Z"
}

response = session.post(
    create_url,
    json=plan_data,
    headers={'X-CSRFToken': session.cookies['csrftoken']}
)

print(response.json())
```

#### 3. Invite a member

```python
plan_id = response.json()['id']
invite_url = f'http://127.0.0.1:8000/api/plans/{plan_id}/invite/'

invite_data = {
    "email": "friend@example.com",
    "name": "Friend Name",
    "role": "member"
}

response = session.post(
    invite_url,
    json=invite_data,
    headers={'X-CSRFToken': session.cookies['csrftoken']}
)

print(response.json())
```

#### 4. Join as a guest (no authentication needed)

```python
# Get the plan and token from previous response
plan_id = "your-plan-id"
invite_token = "your-invite-token"

join_url = f'http://127.0.0.1:8000/api/plans/{plan_id}/join/{invite_token}/'

guest_data = {
    "name": "Guest User",
    "email": "guest@example.com"
}

response = requests.post(join_url, json=guest_data)
print(response.json())
```

### Option 3: Using Django Shell

```bash
python manage.py shell
```

```python
from django.contrib.auth.models import User
from plans.models import Plan, PlanMember
from plans.services import NotificationService

# Create a user if needed
user = User.objects.create_user('testuser', 'test@example.com', 'password123')

# Create a plan
plan = Plan.objects.create(
    title='Family Reunion',
    category='family',
    description='Annual family gathering',
    creator=user
)

# Add creator as member
PlanMember.objects.create(
    plan=plan,
    user=user,
    role='creator',
    status='active'
)

# Create a guest member
guest = PlanMember.objects.create(
    plan=plan,
    guest_name='John Doe',
    guest_email='john@example.com',
    role='guest',
    status='invited',
    invited_by=user
)

# Send notification
NotificationService.send_plan_invite(plan, guest, user)

# Get invite link
print(f"Invite link: {plan.get_invite_link()}")
print(f"Full token: {plan.invite_token}")
```

## Testing Checklist

- [ ] Create a plan
- [ ] List all plans
- [ ] Get plan details
- [ ] Update a plan
- [ ] Invite a member by email
- [ ] Join via invite link (authenticated)
- [ ] Join as guest
- [ ] List plan members
- [ ] Remove a member
- [ ] View notifications
- [ ] Mark notification as read

## Common Issues

### Issue: 403 Forbidden

**Solution:** Make sure you're authenticated and have the CSRF token set.

### Issue: 404 on join endpoint

**Solution:** Ensure the URL format is correct: `/api/plans/{plan_id}/join/{token}/`

### Issue: Email not sending

**Solution:** Configure email backend in settings.py or check console for email output in development.

### Issue: Unique constraint error

**Solution:** Don't try to add the same user/email to a plan twice.

## Sample Data Creation Script

Create a file `create_sample_data.py` in your app root:

```python
# create_sample_data.py
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tripvo_backend.settings')
django.setup()

from django.contrib.auth.models import User
from plans.models import Plan, PlanMember
from django.utils import timezone

# Create users
users = []
for i in range(1, 4):
    user, created = User.objects.get_or_create(
        username=f'user{i}',
        defaults={
            'email': f'user{i}@example.com',
            'first_name': f'User',
            'last_name': f'{i}'
        }
    )
    if created:
        user.set_password('password123')
        user.save()
    users.append(user)

# Create plans
categories = ['travel', 'event', 'family']
for i, category in enumerate(categories, 1):
    plan = Plan.objects.create(
        title=f'Sample {category.title()} Plan {i}',
        category=category,
        description=f'This is a sample {category} plan for testing',
        creator=users[0],
        status='active',
        start_date=timezone.now() + timezone.timedelta(days=30),
        end_date=timezone.now() + timezone.timedelta(days=37)
    )

    # Add creator as member
    PlanMember.objects.create(
        plan=plan,
        user=users[0],
        role='creator',
        status='active',
        joined_at=plan.created_at
    )

    # Add other members
    for j, user in enumerate(users[1:], 1):
        PlanMember.objects.create(
            plan=plan,
            user=user,
            role='member',
            status='active',
            invited_by=users[0],
            joined_at=timezone.now()
        )

    # Add a guest
    PlanMember.objects.create(
        plan=plan,
        guest_name=f'Guest User {i}',
        guest_email=f'guest{i}@example.com',
        role='guest',
        status='invited',
        invited_by=users[0]
    )

    print(f'Created plan: {plan.title}')
    print(f'Invite link: {plan.get_invite_link()}')
    print(f'Token: {plan.invite_token}')
    print('---')

print('Sample data created successfully!')
```

Run it:

```bash
python create_sample_data.py
```

## API Browsability

Django REST Framework provides a browsable API. Visit these URLs in your browser:

- Plans list: http://127.0.0.1:8000/api/plans/
- Notifications: http://127.0.0.1:8000/api/notifications/

You can interact with the API directly from the browser!
