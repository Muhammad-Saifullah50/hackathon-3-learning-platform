# Research: User Management

**Feature**: 004-user-management
**Date**: 2026-03-15
**Phase**: 0 - Research & Discovery

## Executive Summary

User Management feature builds on existing F01 (Authentication) and F02 (Database Schema) infrastructure. All required database models and repositories already exist. This feature adds API endpoints, business logic layer, and frontend UI for profile management, preferences configuration, and account deletion.

## Technical Discoveries

### Existing Infrastructure (F01 + F02)

**Database Models** (already implemented):
- `User` model in [backend/src/models/user.py](backend/src/models/user.py:11-40)
  - Fields: id, email, password_hash, role, display_name, email_verified_at, mfa_enabled, mfa_secret, permissions, preferences (JSONB)
  - Relationships: profile (1:1), streak (1:1), exercise_progress, quiz_attempts, module_mastery, code_submissions
  - Soft delete support via SoftDeleteMixin
  - Role constraint: student/teacher/admin

- `UserProfile` model in [backend/src/models/user.py](backend/src/models/user.py:43-57)
  - Fields: id, user_id, bio, profile_metadata (JSONB as 'metadata')
  - 1:1 relationship with User (CASCADE delete)

- `UserStreak` model in [backend/src/models/user.py](backend/src/models/user.py:60-80)
  - Fields: id, user_id, current_streak, longest_streak, last_activity_date
  - Business logic for streak calculation already implemented

**Repositories** (already implemented):
- `UserRepository` in [backend/src/repositories/user_repository.py](backend/src/repositories/user_repository.py:10-67)
  - Methods: get_by_id, get_by_email, get_by_role, create, update_preferences, soft_delete
  - Soft delete with PII anonymization (GDPR)

- `UserProfileRepository` in [backend/src/repositories/user_repository.py](backend/src/repositories/user_repository.py:69-97)
  - Methods: get_by_user_id, create, update_metadata

**Schemas** (already implemented):
- `UserResponse`, `UserUpdate`, `UserPreferencesUpdate` in [backend/src/schemas/user.py](backend/src/schemas/user.py:31-42)
- `UserProfileResponse`, `UserProfileUpdate` in [backend/src/schemas/user.py](backend/src/schemas/user.py:56-70)

**Authentication** (already implemented):
- JWT-based auth with `get_current_user` dependency in [backend/src/auth/dependencies.py](backend/src/auth/dependencies.py:17-86)
- Role-based access control via `require_role` factory in [backend/src/auth/dependencies.py](backend/src/auth/dependencies.py:89-111)
- Session management with revocation support

### Gaps Identified (What We Need to Build)

1. **Service Layer** (NEW)
   - `UserProfileService` - Business logic for profile operations
   - Responsibilities:
     - Validate display name (fallback to email if empty)
     - Validate bio length (max 500 chars)
     - Validate learning preferences (enum: slow/normal/fast)
     - Validate difficulty level (enum: beginner/intermediate/advanced)
     - Orchestrate hard deletion (user + profile + progress + submissions + sessions)

2. **API Routes** (NEW)
   - `GET /api/profile` - Get current user's profile
   - `PATCH /api/profile` - Update profile (display_name, bio)
   - `PATCH /api/preferences` - Update learning preferences
   - `DELETE /api/account` - Hard delete account with password confirmation
   - `GET /api/admin/users` - List all users (admin only, paginated, filterable by role)

3. **Pydantic Schemas** (EXTEND EXISTING)
   - `ProfileUpdateRequest` - display_name, bio validation
   - `PreferencesUpdateRequest` - learning_pace, difficulty_level enums
   - `AccountDeleteRequest` - password confirmation
   - `AdminUserListResponse` - paginated user list with filters

4. **Frontend Pages** (NEW)
   - `/profile` - View/edit profile page
   - `/preferences` - Learning preferences configuration
   - `/admin/users` - Admin user management (list, filter)

5. **Frontend Components** (NEW)
   - `ProfileForm` - Form for display_name and bio
   - `PreferencesForm` - Form for learning_pace and difficulty_level
   - `UserList` - Admin table with pagination and role filter
   - `AccountDeleteDialog` - Confirmation dialog with password input

## Key Decisions

### Decision 1: Hard Delete vs Soft Delete for Account Deletion

**Context**: Spec requires GDPR compliance with permanent data removal (FR-009).

**Options Considered**:
1. Soft delete (existing `soft_delete` method in UserRepository)
2. Hard delete (physical removal from database)

**Decision**: Hard delete

**Rationale**:
- GDPR "right to be forgotten" requires permanent data removal
- Soft delete leaves data in database (not compliant)
- Existing `soft_delete` method anonymizes email but retains records
- Hard delete requires cascading deletion across all related tables

**Implementation**:
- Add `hard_delete` method to UserRepository
- Cascade delete: User → UserProfile, UserStreak, UserExerciseProgress, UserQuizAttempt, UserModuleMastery, CodeSubmission, Sessions
- SQLAlchemy CASCADE already configured on relationships
- Password confirmation required before deletion (security)

**Alternatives Rejected**:
- Soft delete: Not GDPR compliant (data still exists)
- Soft delete + scheduled purge: Adds complexity, delayed compliance

### Decision 2: Learning Preferences Storage Location

**Context**: Students need to configure learning_pace and difficulty_level (FR-004, FR-005).

**Options Considered**:
1. Store in `User.preferences` JSONB field (existing)
2. Store in `UserProfile.profile_metadata` JSONB field (existing)
3. Create new `learning_preferences` table with dedicated columns

**Decision**: Store in `User.preferences` JSONB field

**Rationale**:
- Field already exists and is indexed
- Preferences are user-level settings (not profile metadata)
- JSONB allows flexible schema evolution
- No migration needed
- Consistent with existing `update_preferences` repository method

**Schema**:
```json
{
  "learning_pace": "normal",  // enum: slow, normal, fast
  "difficulty_level": "beginner",  // enum: beginner, intermediate, advanced
  "theme": "dark"  // future: light mode support
}
```

**Alternatives Rejected**:
- UserProfile.profile_metadata: Profile is for bio/avatar, not settings
- New table: Over-engineering for 2-3 fields, adds JOIN overhead

### Decision 3: Display Name Fallback Strategy

**Context**: Spec requires email as default display name when empty (FR-007).

**Options Considered**:
1. Database constraint: NOT NULL with default = email (requires migration)
2. Application-level fallback in service layer
3. Frontend-only fallback (display logic)

**Decision**: Application-level fallback in service layer

**Rationale**:
- No migration needed (display_name already NOT NULL in User model)
- Service layer validates and sets email as display_name if empty string provided
- Frontend can also show email as placeholder for better UX
- Keeps database schema unchanged

**Implementation**:
- UserProfileService validates display_name on update
- If empty/whitespace, set to user.email
- Frontend shows email in input placeholder

**Alternatives Rejected**:
- Database constraint: Requires migration, couples display_name to email
- Frontend-only: Not reliable, backend must enforce business rules

### Decision 4: Admin User List Pagination Strategy

**Context**: Admin needs to view all users with pagination (50 per page) and role filtering (FR-011, FR-012).

**Options Considered**:
1. Offset-based pagination (LIMIT/OFFSET)
2. Cursor-based pagination (keyset pagination)
3. Load all users, paginate in memory

**Decision**: Offset-based pagination with LIMIT/OFFSET

**Rationale**:
- Simple to implement with SQLAlchemy
- Performance acceptable for MVP scale (< 10k users)
- Supports page jumping (cursor-based doesn't)
- Role filtering via WHERE clause (indexed on role column)

**Implementation**:
```python
# GET /api/admin/users?page=1&role=student
query = select(User).where(User.deleted_at.is_(None))
if role:
    query = query.where(User.role == role)
query = query.limit(50).offset((page - 1) * 50)
```

**Alternatives Rejected**:
- Cursor-based: Over-engineering for MVP, no page jumping
- In-memory: Doesn't scale, loads all users unnecessarily

### Decision 5: Password Confirmation for Account Deletion

**Context**: Account deletion is irreversible and requires security confirmation (FR-008).

**Options Considered**:
1. Password confirmation only
2. Email confirmation link (send email, click link)
3. Two-factor confirmation (password + email)

**Decision**: Password confirmation only

**Rationale**:
- Balances security and UX
- User is already authenticated (JWT token)
- Password confirms intent and identity
- Email confirmation adds friction (MVP scope)
- Consistent with industry standards (GitHub, Twitter)

**Implementation**:
- `DELETE /api/account` endpoint requires `password` in request body
- Verify password using existing bcrypt verification
- Return 401 if password incorrect
- Show confirmation dialog in frontend with password input

**Alternatives Rejected**:
- Email confirmation: Adds complexity, delays deletion
- Two-factor: Over-engineering for MVP, excessive friction

## Technology Best Practices

### FastAPI Service Layer Pattern

**Pattern**: Separate business logic from route handlers

**Structure**:
```python
# services/user_profile_service.py
class UserProfileService:
    def __init__(self, db: AsyncSession):
        self.user_repo = UserRepository(db)
        self.profile_repo = UserProfileRepository(db)

    async def update_profile(self, user_id: UUID, display_name: str, bio: str):
        # Validation logic
        # Business rules (display_name fallback)
        # Repository calls
        pass
```

**Benefits**:
- Testable business logic (unit tests without FastAPI)
- Reusable across multiple endpoints
- Clear separation of concerns

**Reference**: Existing `AuthService` in [backend/src/auth/service.py](backend/src/auth/service.py)

### Pydantic Enum Validation

**Pattern**: Use Pydantic enums for learning preferences

**Implementation**:
```python
from enum import Enum
from pydantic import BaseModel

class LearningPace(str, Enum):
    SLOW = "slow"
    NORMAL = "normal"
    FAST = "fast"

class DifficultyLevel(str, Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"

class PreferencesUpdateRequest(BaseModel):
    learning_pace: LearningPace
    difficulty_level: DifficultyLevel
```

**Benefits**:
- Automatic validation (400 error if invalid value)
- Type safety in IDE
- Self-documenting API (OpenAPI schema shows allowed values)

### Next.js Server Actions for Mutations

**Pattern**: Use Server Actions for profile updates (Next.js 14+)

**Implementation**:
```typescript
// app/profile/actions.ts
'use server'

export async function updateProfile(formData: FormData) {
  const response = await fetch('/api/profile', {
    method: 'PATCH',
    headers: { 'Authorization': `Bearer ${token}` },
    body: JSON.stringify({
      display_name: formData.get('display_name'),
      bio: formData.get('bio')
    })
  })
  revalidatePath('/profile')
  return response.json()
}
```

**Benefits**:
- Progressive enhancement (works without JS)
- Automatic revalidation
- Type-safe with TypeScript

**Reference**: Next.js 14 Server Actions documentation

### SQLAlchemy Cascade Delete

**Pattern**: Use CASCADE on foreign keys for hard deletion

**Existing Configuration**:
```python
# User model relationships already have cascade="all, delete-orphan"
profile = relationship("UserProfile", back_populates="user", cascade="all, delete-orphan")
exercise_progress = relationship("UserExerciseProgress", back_populates="user", cascade="all, delete-orphan")
```

**Implementation**:
```python
# Hard delete in repository
async def hard_delete(self, user_id: UUID) -> bool:
    user = await self.get_by_id(user_id)
    if user:
        await self.session.delete(user)  # Cascades to all relationships
        await self.session.commit()
        return True
    return False
```

**Benefits**:
- Database enforces referential integrity
- Single delete statement cascades automatically
- No orphaned records

## Integration Points

### F01 Authentication Integration
- Use `get_current_user` dependency for all profile endpoints
- Use `require_role(['admin'])` for admin user list endpoint
- Invalidate all sessions on account deletion (call AuthService.logout_all)

### F02 Database Schema Integration
- Use existing User, UserProfile, UserStreak models
- Use existing UserRepository, UserProfileRepository
- No new migrations needed (all fields exist)

### Frontend Integration
- Use Better Auth client for JWT token management
- Use Next.js 14 app router for pages
- Use React Hook Form for form validation
- Use Tailwind CSS for styling (consistent with existing frontend)

## Performance Considerations

### Database Queries
- User profile GET: Single query with JOIN (< 40ms)
- Profile update: Single UPDATE (< 40ms)
- Admin user list: Paginated query with role filter (< 2s for 50 users)
- Account deletion: Single DELETE with CASCADE (< 5s)

### Indexes (already exist from F02)
- `users.email` (unique index)
- `users.role` (index for filtering)
- `user_profiles.user_id` (unique index for JOIN)

### Caching Strategy
- No caching needed for MVP (profile data changes infrequently)
- Future: Redis cache for admin user list (invalidate on user create/delete)

## Security Considerations

### Authorization
- Users can only access their own profile (403 if user_id mismatch)
- Admin endpoints require admin role (403 if not admin)
- Account deletion requires password confirmation (401 if incorrect)

### Input Validation
- Display name: max 100 chars (Pydantic validation)
- Bio: max 500 chars (Pydantic validation)
- Learning preferences: enum validation (Pydantic)
- SQL injection: Prevented by SQLAlchemy ORM (parameterized queries)

### GDPR Compliance
- Hard deletion removes all user data permanently
- Cascade delete ensures no orphaned records
- No data retention after deletion (compliant with "right to be forgotten")

## Testing Strategy

### Unit Tests
- UserProfileService business logic (display_name fallback, validation)
- Repository methods (hard_delete, update_profile)
- Pydantic schema validation (enum values, length constraints)

### Integration Tests
- FastAPI routes with test database
- Auth-protected endpoints (401 without token, 403 with wrong role)
- Account deletion cascade (verify all related records deleted)

### E2E Tests (Playwright)
- Profile update flow (login → edit profile → save → verify)
- Account deletion flow (login → delete account → confirm → verify logout)
- Admin user list (login as admin → view users → filter by role)

## Open Questions

None - all technical unknowns resolved.

## References

- [F01 Authentication Spec](../001-auth/spec.md)
- [F02 Database Schema Spec](../002-database-schema/spec.md)
- [LearnPyByAI Constitution](.specify/memory/constitution.md)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Next.js 14 Server Actions](https://nextjs.org/docs/app/building-your-application/data-fetching/server-actions)
- [SQLAlchemy Cascade](https://docs.sqlalchemy.org/en/20/orm/cascades.html)
- [GDPR Right to Erasure](https://gdpr-info.eu/art-17-gdpr/)
