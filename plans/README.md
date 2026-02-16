# Plans App - Group Planning Feature

## Overview

The Plans app is the core feature of Tripvo that enables collaborative group planning for trips, events, and family activities. It provides a complete REST API for creating, managing, and collaborating on plans with support for both registered users and guests.

## Features

### ✅ Plan Management

- Create plans with title, category, dates, and description
- Four categories: Travel, Event, Family, Custom
- Status tracking: Draft, Active, Completed, Cancelled
- Automatic creator assignment and permissions

### ✅ Member Collaboration

- **Email Invitations**: Invite members by email address
- **Shareable Links**: Generate unique invite links for easy sharing
- **Guest Mode**: Allow participation without account registration
- **Role System**: Creator, Admin, Member, Guest roles with appropriate permissions

### ✅ Notifications

- In-app notification system
- Email notifications for invites and member joins
- Read/unread status tracking
- Batch operations (mark all as read)

## Quick Start

### 1. Server is Running

The development server should be running at: http://127.0.0.1:8000/

### 2. Create a Superuser (if needed)

```bash
python manage.py createsuperuser
```

### 3. Access Admin Interface

Visit http://127.0.0.1:8000/admin/ to:

- View and manage plans
- Add members manually
- Check notifications
- Monitor system activity

### 4. Browse the API

Visit http://127.0.0.1:8000/api/plans/ to:

- See the browsable API interface
- Test endpoints interactively
- View documentation

## API Endpoints

### Plans

- `POST /api/plans/` - Create a new plan
- `GET /api/plans/` - List all your plans
- `GET /api/plans/{id}/` - Get plan details
- `PATCH /api/plans/{id}/` - Update a plan
- `DELETE /api/plans/{id}/` - Delete a plan

### Invitations & Members

- `POST /api/plans/{id}/invite/` - Invite someone by email
- `POST /api/plans/{plan_id}/join/{token}/` - Join via invite link
- `GET /api/plans/{id}/members/` - List all members
- `DELETE /api/plans/{id}/members/{member_id}/` - Remove a member

### Notifications

- `GET /api/notifications/` - List your notifications
- `POST /api/notifications/{id}/mark_read/` - Mark one as read
- `POST /api/notifications/mark_all_read/` - Mark all as read

## Models

### Plan

Core model for group plans with:

- UUID primary key for security
- Title, category, description, dates
- Creator reference and status
- Unique invite token for sharing

### PlanMember

Tracks plan membership with:

- Support for both users and guests
- Role-based permissions
- Status tracking (invited, active, etc.)
- Join date tracking

### Notification

User notification system with:

- In-app and email support
- Type categorization
- Read/unread status
- Plan relationships

## Usage Examples

### Creating a Plan

```python
from plans.models import Plan
from django.contrib.auth.models import User

user = User.objects.get(username='myuser')
plan = Plan.objects.create(
    title='Summer Beach Trip',
    category='travel',
    description='Annual family vacation',
    creator=user
)
```

### Inviting Members

```python
from plans.models import PlanMember

# Invite a registered user
member = PlanMember.objects.create(
    plan=plan,
    user=other_user,
    role='member',
    status='invited',
    invited_by=user
)

# Invite a guest
guest = PlanMember.objects.create(
    plan=plan,
    guest_name='John Doe',
    guest_email='john@example.com',
    role='guest',
    status='invited',
    invited_by=user
)
```

### Sending Notifications

```python
from plans.services import NotificationService

# Send invite notification
NotificationService.send_plan_invite(plan, member, user)

# Notify when member joins
NotificationService.send_member_joined(plan, member, plan.creator)
```

## Testing

Run the test suite:

```bash
python manage.py test plans
```

All 17 tests cover:

- Model functionality
- API endpoints
- Permissions
- Guest mode
- Notifications

## Permissions

### Creating Plans

- Requires authentication
- Any authenticated user can create

### Managing Plans

- Only creator and admins can:
    - Update plan details
    - Invite new members
    - Remove members
    - Delete the plan

### Joining Plans

- Anyone with an invite link can join
- Guests don't need accounts
- Authenticated users are automatically linked

## Guest Mode

Guests can:

- Join plans via invite links
- View plan details
- Receive notifications via email
- Participate without registration

Guests cannot:

- Create new plans
- Invite others
- Access features requiring authentication

## Admin Interface

All models registered with admin for easy management:

**Plans Admin:**

- List view with filters by category, status, date
- Search by title, description, creator
- Bulk actions available

**Members Admin:**

- View all memberships
- Filter by role, status
- Search by user, email, plan

**Notifications Admin:**

- Monitor notification delivery
- Track read status
- Filter by type and recipient

## Configuration

### Email Settings

Configure in `tripvo_backend/settings.py`:

```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.example.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
DEFAULT_FROM_EMAIL = 'noreply@tripvo.com'
```

### CORS Settings

Already configured for frontend development:

```python
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]
```

## Security

- UUID primary keys prevent enumeration
- Invite tokens are secure UUIDs
- Permission checks on all operations
- Database constraints prevent duplicates
- SQL injection protection via ORM

## Documentation

See the `docs/` directory for:

- `PLAN_CREATION_API.md` - Complete API documentation
- `QUICK_START.md` - Quick start guide with examples
- `IMPLEMENTATION_SUMMARY.md` - Implementation details

## Support

For questions or issues:

1. Check the documentation in `docs/`
2. Review the test suite for examples
3. Use Django admin for debugging
4. Check server logs for errors

## Version

Current Version: 1.0.0
Django Version: 6.0.1
Python Version: 3.12.10

## License

Proprietary - All Rights Reserved
