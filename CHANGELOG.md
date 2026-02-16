# Changelog

All notable changes to the Tripvo project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-01-28

### Added - Plan Creation Feature

#### Core Functionality

- **Plan Creation**: Users can create collaborative plans with title, category, dates, and description
- **Categories**: Four plan categories - Travel, Event, Family, and Custom
- **Status Tracking**: Plans have status (draft, active, completed, cancelled)
- **Guest Mode**: Non-registered users can join plans without creating accounts
- **Invite System**: Two ways to invite - email invitations and shareable links
- **Notifications**: In-app and email notifications for invites and member joins

#### API Endpoints

- `POST /api/plans/` - Create a new plan
- `GET /api/plans/` - List user's plans
- `GET /api/plans/{id}/` - Get plan details
- `PATCH /api/plans/{id}/` - Update plan
- `DELETE /api/plans/{id}/` - Delete plan
- `POST /api/plans/{id}/invite/` - Invite members by email
- `POST /api/plans/{plan_id}/join/{token}/` - Join via invite link
- `GET /api/plans/{id}/members/` - List plan members
- `DELETE /api/plans/{id}/members/{member_id}/` - Remove member
- `GET /api/notifications/` - List notifications
- `POST /api/notifications/{id}/mark_read/` - Mark notification as read
- `POST /api/notifications/mark_all_read/` - Mark all as read

#### Models

- **Plan Model**: Core model for group plans with UUID primary key, invite tokens, and status tracking
- **PlanMember Model**: Tracks membership with support for both users and guests, role-based permissions
- **Notification Model**: Handles in-app and email notifications with read/unread status

#### Services

- **NotificationService**: Centralized service for sending email and in-app notifications
    - `send_plan_invite()` - Send invitation notifications
    - `send_member_joined()` - Notify when members join
    - `send_plan_update()` - Broadcast plan updates

#### Serializers

- `PlanSerializer` - Full plan details with nested members
- `PlanListSerializer` - Lightweight list view
- `PlanMemberSerializer` - Member details with user info
- `InviteMemberSerializer` - Invite validation
- `NotificationSerializer` - Notification details
- `UserBasicSerializer` - Nested user information

#### Views

- `PlanViewSet` - Complete CRUD operations with custom actions for invites and joins
- `NotificationViewSet` - Read-only view for user notifications

#### Testing

- 17 comprehensive tests covering:
    - Model creation and methods
    - API endpoints and permissions
    - Guest mode functionality
    - Invitation system
    - Notification creation
- All tests passing ✅

#### Documentation

- Complete API documentation (`docs/PLAN_CREATION_API.md`)
- Quick start guide (`docs/QUICK_START.md`)
- Implementation summary (`docs/IMPLEMENTATION_SUMMARY.md`)
- Plans app README (`plans/README.md`)

#### Security

- UUID primary keys to prevent enumeration
- Secure invite tokens (UUID-based)
- Permission-based access control
- Database constraints for data integrity
- SQL injection protection via Django ORM

#### Admin Interface

- Full admin interface for Plans, PlanMembers, and Notifications
- List filters and search functionality
- Bulk operations support

### Changed

- Updated main README with current features and documentation links
- Enhanced project structure documentation
- Added CORS configuration for frontend development

### Configuration

- Added `plans` app to `INSTALLED_APPS`
- Configured REST Framework settings
- Set up CORS for local development
- Added media file serving for development

## [0.1.0] - 2026-01-27

### Added - Initial Setup

#### Project Structure

- Django project initialized as `tripvo_backend`
- Virtual environment configured with Python 3.12.10
- Core apps created: users, groups, trips, events

#### Dependencies

- Django 6.0.1
- Django REST Framework
- django-cors-headers
- Pillow
- psycopg2-binary
- python-decouple
- gunicorn
- whitenoise

#### Configuration

- SQLite database for development
- PostgreSQL support configured
- Static and media file handling
- REST Framework configuration
- CORS settings

#### Documentation

- Initial README.md
- Setup instructions
- Project structure documentation

#### Infrastructure

- `.gitignore` file
- `requirements.txt`
- Environment variable template (`.env.example`)

---

## Categories

- **Added**: New features
- **Changed**: Changes in existing functionality
- **Deprecated**: Soon-to-be removed features
- **Removed**: Removed features
- **Fixed**: Bug fixes
- **Security**: Security improvements

## Links

- [GitHub Repository](https://github.com/Fearfullymade01/tripvo)
- [API Documentation](docs/PLAN_CREATION_API.md)
- [Quick Start Guide](docs/QUICK_START.md)
