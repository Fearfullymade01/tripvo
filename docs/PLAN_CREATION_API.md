# Group Plan Creation Feature - API Documentation

## Overview

This document describes the Group Plan Creation feature for Tripvo, which allows users to create and manage collaborative plans for trips, events, and family activities.

## Features Implemented

✅ **Plan Creation**

- Users can create plans with title, category, dates, and description
- Categories: Travel, Event, Family, Custom
- Plans appear immediately in creator's dashboard

✅ **Member Management**

- Invite members via email
- Invite links for easy sharing
- Guest mode (no account required)
- Role-based permissions (Creator, Admin, Member, Guest)

✅ **Notifications**

- Email and in-app notifications for invites
- Notifications when members join
- Notification system with read/unread status

✅ **Complete Test Coverage**

- 17 unit and integration tests
- All tests passing

## API Endpoints

### Plans

#### Create a Plan

```http
POST /api/plans/
Authorization: Bearer <token>

{
  "title": "Summer Beach Trip",
  "category": "travel",
  "description": "Annual family beach vacation",
  "start_date": "2026-07-01T10:00:00Z",
  "end_date": "2026-07-10T10:00:00Z"
}
```

**Response (201 Created):**

```json
{
  "id": "uuid",
  "title": "Summer Beach Trip",
  "category": "travel",
  "description": "Annual family beach vacation",
  "start_date": "2026-07-01T10:00:00Z",
  "end_date": "2026-07-10T10:00:00Z",
  "creator": 1,
  "creator_info": {
    "id": 1,
    "username": "john",
    "email": "john@example.com",
    "first_name": "John",
    "last_name": "Doe"
  },
  "status": "draft",
  "invite_token": "uuid",
  "invite_link": "http://localhost:8000/api/plans/{id}/join/{token}/",
  "members": [...],
  "member_count": 1,
  "is_creator": true,
  "created_at": "2026-01-28T10:00:00Z",
  "updated_at": "2026-01-28T10:00:00Z"
}
```

#### List Plans

```http
GET /api/plans/
Authorization: Bearer <token>
```

Returns all plans the user has created or is a member of.

#### Get Plan Details

```http
GET /api/plans/{id}/
Authorization: Bearer <token>
```

#### Update Plan

```http
PATCH /api/plans/{id}/
Authorization: Bearer <token>

{
  "title": "Updated Title",
  "status": "active"
}
```

#### Delete Plan

```http
DELETE /api/plans/{id}/
Authorization: Bearer <token>
```

### Invitations

#### Invite Member by Email

```http
POST /api/plans/{id}/invite/
Authorization: Bearer <token>

{
  "email": "friend@example.com",
  "name": "Friend Name",
  "role": "member"
}
```

**Roles:** `member`, `admin`, `guest`

**Response (201 Created):**

```json
{
    "id": "uuid",
    "plan": "plan-uuid",
    "user": null,
    "user_info": null,
    "guest_name": "Friend Name",
    "guest_email": "friend@example.com",
    "member_name": "Friend Name",
    "member_email": "friend@example.com",
    "role": "member",
    "status": "invited",
    "invited_by": 1,
    "invited_at": "2026-01-28T10:00:00Z",
    "joined_at": null,
    "created_at": "2026-01-28T10:00:00Z"
}
```

#### Join Plan via Invite Link (Authenticated User)

```http
POST /api/plans/{plan_id}/join/{token}/
Authorization: Bearer <token>

{}
```

#### Join Plan as Guest

```http
POST /api/plans/{plan_id}/join/{token}/

{
  "name": "Guest Name",
  "email": "guest@example.com"
}
```

**Response (201 Created):**

```json
{
    "id": "uuid",
    "plan": "plan-uuid",
    "guest_name": "Guest Name",
    "guest_email": "guest@example.com",
    "role": "guest",
    "status": "active",
    "joined_at": "2026-01-28T10:00:00Z"
}
```

### Members

#### Get Plan Members

```http
GET /api/plans/{id}/members/
Authorization: Bearer <token>
```

#### Remove Member

```http
DELETE /api/plans/{id}/members/{member_id}/
Authorization: Bearer <token>
```

Only plan creator or admins can remove members.

### Notifications

#### List Notifications

```http
GET /api/notifications/
Authorization: Bearer <token>
```

#### Mark Notification as Read

```http
POST /api/notifications/{id}/mark_read/
Authorization: Bearer <token>
```

#### Mark All Notifications as Read

```http
POST /api/notifications/mark_all_read/
Authorization: Bearer <token>
```

## Models

### Plan

- **id**: UUID (primary key)
- **title**: String (max 200 chars)
- **category**: Choice (travel, event, family, custom)
- **description**: Text
- **start_date**: DateTime (optional)
- **end_date**: DateTime (optional)
- **creator**: Foreign key to User
- **status**: Choice (draft, active, completed, cancelled)
- **invite_token**: UUID (unique, for shareable links)
- **created_at**: DateTime (auto)
- **updated_at**: DateTime (auto)

### PlanMember

- **id**: UUID (primary key)
- **plan**: Foreign key to Plan
- **user**: Foreign key to User (null for guests)
- **guest_name**: String (for guests)
- **guest_email**: Email (for guests)
- **role**: Choice (creator, admin, member, guest)
- **status**: Choice (invited, active, declined, removed)
- **invited_by**: Foreign key to User
- **invited_at**: DateTime (auto)
- **joined_at**: DateTime (optional)
- **created_at**: DateTime (auto)
- **updated_at**: DateTime (auto)

**Constraints:**

- Unique (plan, user) for registered users
- Unique (plan, guest_email) for guests

### Notification

- **id**: UUID (primary key)
- **recipient**: Foreign key to User (optional)
- **recipient_email**: Email (for guest notifications)
- **notification_type**: Choice (plan_invite, plan_update, member_joined, member_left)
- **title**: String (max 200 chars)
- **message**: Text
- **plan**: Foreign key to Plan (optional)
- **is_read**: Boolean (default: False)
- **sent**: Boolean (default: False)
- **created_at**: DateTime (auto)
- **read_at**: DateTime (optional)

## Permissions

### Plan Operations

- **Create**: Authenticated users only
- **List**: Authenticated users (see only their plans)
- **Retrieve/Update/Delete**: Plan creator or admins

### Member Operations

- **Invite**: Plan creator or admins
- **Remove**: Plan creator or admins (cannot remove creator)
- **Join via link**: Anyone (including guests)

### Notification Operations

- **List/Read**: Own notifications only

## Guest Mode

Guests can:

- Join plans via invite link
- Participate without creating an account
- Receive email notifications
- Be identified by name and email

Guests cannot:

- Create plans
- Invite others
- Access other features requiring authentication

## Email Notifications

Email notifications are sent for:

- **Plan invitations**: Sent to invited users/guests
- **Member joined**: Sent to plan creator when someone joins

Email configuration:

- Sender: Configured via `DEFAULT_FROM_EMAIL` in settings (default: noreply@tripvo.com)
- Uses Django's email backend
- Fails silently in development if email not configured

## Testing

Run tests:

```bash
python manage.py test plans
```

All 17 tests included:

- Model tests (Plan, PlanMember, Notification)
- API endpoint tests (CRUD operations)
- Invitation tests (email and link)
- Guest mode tests
- Permission tests
- Notification tests

## Admin Interface

All models are registered in Django admin with:

- List displays with key fields
- Filters for easy management
- Search functionality
- Read-only fields for auto-generated data

Access at: `/admin/`

## Next Steps

1. **Frontend Implementation**
    - Create plan creation UI
    - Build plan dashboard
    - Implement invite modal
    - Add notifications display

2. **Enhancements**
    - Real-time updates with WebSockets
    - File attachments for plans
    - Comments and discussions
    - Calendar integration
    - Mobile app development

3. **Production Setup**
    - Configure email service (SendGrid, AWS SES, etc.)
    - Set up PostgreSQL database
    - Configure domain for invite links
    - Set up Celery for background tasks

## Database Migrations

Current migrations:

- `0001_initial.py`: Initial models (Plan, PlanMember, Notification)
- `0002_alter_planmember_unique_together_and_more.py`: Updated constraints

To apply:

```bash
python manage.py migrate
```

## Example Usage

### Creating a Plan and Inviting Members

1. **Create a plan:**

```bash
curl -X POST http://localhost:8000/api/plans/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Summer Beach Trip",
    "category": "travel",
    "description": "Family vacation",
    "start_date": "2026-07-01T10:00:00Z",
    "end_date": "2026-07-10T10:00:00Z"
  }'
```

2. **Invite members:**

```bash
curl -X POST http://localhost:8000/api/plans/{plan_id}/invite/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "friend@example.com",
    "name": "Friend",
    "role": "member"
  }'
```

3. **Share invite link:**
   Share the `invite_link` from the plan response with others.

4. **Members join:**
   Members click the link and either log in or join as guests.

## Security Considerations

- All plan operations require authentication except joining via invite link
- Invite tokens are UUIDs (unguessable)
- Guest emails are validated
- Permissions enforced at model and view level
- SQL injection protected by Django ORM
- CSRF protection enabled
