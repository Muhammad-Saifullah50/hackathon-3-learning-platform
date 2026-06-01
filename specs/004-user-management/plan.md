# Implementation Plan: User Management

**Branch**: `004-user-management` | **Date**: 2026-03-15 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/004-user-management/spec.md`

**Note**: This template is filled in by the `/sp.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Implement CRUD operations for user profiles, preferences, and account management. This feature enables users to view/update their profile information (display name, bio), configure learning preferences (pace, difficulty level), and delete their accounts (GDPR compliance). Admins can view and filter all users. Technical approach uses FastAPI endpoints with SQLAlchemy repositories, Next.js frontend with form validation, and hard deletion for account removal.

## Technical Context

**Language/Version**: Python 3.11+ (backend), TypeScript/Next.js 14+ (frontend)
**Primary Dependencies**: FastAPI, SQLAlchemy 2.0+, Pydantic 2.0+, Next.js, React, Better Auth (JWT validation)
**Storage**: Neon PostgreSQL (user_profiles table exists from F02, sessions from F01)
**Testing**: pytest (backend integration tests), vitest (frontend component tests), Playwright (E2E for profile flows)
**Target Platform**: Linux server (FastAPI), Web browser (Next.js SSR)
**Project Type**: Web application (backend + frontend)
**Performance Goals**: Profile view/update < 150ms p95, account deletion < 5s, admin list < 2s for 50 users
**Constraints**: JWT auth required on all endpoints except public routes, hard deletion for GDPR compliance, 50 users per page for admin list
**Scale/Scope**: 4 API endpoints (GET/PATCH profile, DELETE account, GET admin users), 3 frontend pages (profile, preferences, admin), ~500 LOC backend + ~400 LOC frontend

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Code Quality Standards
- ✅ Python: black + isort (auto-format on save)
- ✅ TypeScript: prettier + eslint (auto-format on save)
- ✅ Naming: snake_case (Python), camelCase (TypeScript), PascalCase (components)
- ✅ Documentation: Google-style docstrings for business logic, JSDoc for props, FastAPI summary/description fields

### Testing Principles
- ✅ FastAPI routes: 80% coverage target (profile CRUD, account deletion)
- ✅ Database repositories: 85% coverage (user profile operations)
- ✅ React components: 65% coverage (profile forms, admin list)
- ✅ E2E: Profile update flow, account deletion flow (Playwright)
- ✅ TDD approach: Auth-protected endpoints require strict TDD

### Performance Standards
- ✅ FastAPI response (non-AI): < 150ms p95 (profile GET/PATCH)
- ✅ PostgreSQL query: < 40ms p95 (indexed on user_id)
- ✅ Account deletion: < 5s (hard delete with cascading)
- ✅ Admin list: < 2s for 50 users (pagination + filtering)

### Security Constraints
- ✅ All routes require JWT auth via get_current_user dependency
- ✅ Users cannot access other users' profiles (403 Forbidden)
- ✅ Account deletion requires password confirmation
- ✅ Hard deletion for GDPR compliance (no soft delete)
- ✅ Admin role check for user list endpoint

### Architecture Patterns
- ✅ Repository Pattern: UserProfileRepository for DB access
- ✅ No business logic in route handlers (delegate to service layer)
- ✅ Pydantic schemas for request/response validation
- ✅ Alembic migration if schema changes needed (check existing user_profiles table)

### Business Logic Integrity
- ✅ Learning preferences: slow/normal/fast (enum validation)
- ✅ Difficulty levels: beginner/intermediate/advanced (enum validation)
- ✅ Display name fallback: use email if empty
- ✅ Hard deletion: remove user + profile + progress + submissions + sessions

**GATE STATUS**: ✅ PASS - All constitution requirements satisfied. No violations to justify.

## Project Structure

### Documentation (this feature)

```text
specs/004-user-management/
├── plan.md              # This file (/sp.plan command output)
├── research.md          # Phase 0 output (/sp.plan command)
├── data-model.md        # Phase 1 output (/sp.plan command)
├── quickstart.md        # Phase 1 output (/sp.plan command)
├── contracts/           # Phase 1 output (/sp.plan command)
│   ├── profile.openapi.yaml
│   ├── admin.openapi.yaml
│   └── schemas.yaml
└── tasks.md             # Phase 2 output (/sp.tasks command - NOT created by /sp.plan)
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── models/
│   │   └── user_profile.py          # SQLAlchemy model (already exists from F02)
│   ├── repositories/
│   │   └── user_profile_repository.py  # CRUD operations (already exists from F02)
│   ├── schemas/
│   │   └── user_profile.py          # Pydantic request/response schemas (NEW)
│   ├── services/
│   │   └── user_profile_service.py  # Business logic layer (NEW)
│   └── api/
│       └── routes/
│           ├── profile.py           # Profile CRUD endpoints (NEW)
│           └── admin.py             # Admin user list endpoint (NEW)
└── tests/
    ├── integration/
    │   ├── test_profile_routes.py   # FastAPI route tests (NEW)
    │   └── test_admin_routes.py     # Admin endpoint tests (NEW)
    └── unit/
        └── test_user_profile_service.py  # Service layer tests (NEW)

frontend/
├── src/
│   ├── app/
│   │   ├── profile/
│   │   │   └── page.tsx             # Profile view/edit page (NEW)
│   │   ├── preferences/
│   │   │   └── page.tsx             # Learning preferences page (NEW)
│   │   └── admin/
│   │       └── users/
│   │           └── page.tsx         # Admin user list page (NEW)
│   ├── components/
│   │   ├── ProfileForm.tsx          # Profile edit form component (NEW)
│   │   ├── PreferencesForm.tsx      # Preferences form component (NEW)
│   │   └── UserList.tsx             # Admin user list component (NEW)
│   └── lib/
│       └── api/
│           └── profile.ts           # API client for profile endpoints (NEW)
└── tests/
    ├── components/
    │   ├── ProfileForm.test.tsx     # Component tests (NEW)
    │   └── PreferencesForm.test.tsx # Component tests (NEW)
    └── e2e/
        ├── profile-update.spec.ts   # E2E profile flow (NEW)
        └── account-deletion.spec.ts # E2E deletion flow (NEW)
```

**Structure Decision**: Web application structure (backend + frontend). Backend uses existing SQLAlchemy models and repositories from F02 (database schema feature). New additions: Pydantic schemas for validation, service layer for business logic, FastAPI routes for endpoints. Frontend uses Next.js 14 app router with new pages for profile, preferences, and admin user management.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

**No violations** - All constitution requirements satisfied. No complexity justification needed.

---

## Phase 0: Research Summary

**Status**: ✅ Complete

**Output**: [research.md](./research.md)

**Key Findings**:
- All required database models exist from F02 (User, UserProfile, UserStreak)
- All required repositories exist from F02 (UserRepository, UserProfileRepository)
- JWT authentication infrastructure exists from F01 (get_current_user, require_role)
- No new migrations needed - all fields exist in current schema
- Hard deletion required for GDPR compliance (not soft delete)
- Learning preferences stored in User.preferences JSONB field
- Display name fallback to email handled in service layer

**Decisions Made**:
1. Hard delete for account deletion (GDPR compliance)
2. Store preferences in User.preferences JSONB (existing field)
3. Application-level display name fallback (service layer)
4. Offset-based pagination for admin user list (simple, performant)
5. Password confirmation only for account deletion (balance security/UX)

---

## Phase 1: Design Summary

**Status**: ✅ Complete

**Outputs**:
- [data-model.md](./data-model.md) - Entity relationships, validation rules, state transitions
- [contracts/profile.openapi.yaml](./contracts/profile.openapi.yaml) - Profile API contract
- [contracts/admin.openapi.yaml](./contracts/admin.openapi.yaml) - Admin API contract
- [quickstart.md](./quickstart.md) - Implementation guide

**Design Highlights**:
- **Service Layer**: UserProfileService with business logic (display_name fallback, validation)
- **API Endpoints**: 5 endpoints (GET/PATCH profile, PATCH preferences, DELETE account, GET admin/users)
- **Pydantic Schemas**: Enum validation for learning_pace and difficulty_level
- **Frontend Components**: ProfileForm, PreferencesForm, AccountDeleteDialog
- **Frontend Pages**: /profile, /preferences, /admin/users

**Performance Targets**:
- Profile GET/PATCH: < 150ms p95 (single JOIN, indexed queries)
- Account deletion: < 5s (CASCADE to 7 tables)
- Admin user list: < 2s for 50 users (paginated, indexed on role)

**Security Measures**:
- JWT auth required on all endpoints (get_current_user dependency)
- Role-based access control for admin endpoints (require_role(['admin']))
- Password confirmation for account deletion (bcrypt verification)
- Users can only access their own profile (user_id from JWT token)
- Hard deletion removes all PII permanently (GDPR compliant)

---

## Phase 2: Constitution Re-Check

**Status**: ✅ PASS

All constitution requirements remain satisfied after design phase:

- ✅ Code Quality: Python (black/isort), TypeScript (prettier/eslint), Google-style docstrings
- ✅ Testing: 80% coverage target for FastAPI routes, 85% for repositories, E2E for critical flows
- ✅ Performance: All endpoints meet latency budgets (< 150ms non-AI, < 5s deletion)
- ✅ Security: JWT auth, role checks, password confirmation, hard deletion for GDPR
- ✅ Architecture: Repository pattern (existing), service layer (new), Pydantic validation

**No new violations introduced.**

---

## Implementation Readiness

### Ready to Implement
- ✅ All technical unknowns resolved
- ✅ Database schema verified (no migrations needed)
- ✅ API contracts defined (OpenAPI specs)
- ✅ Data model documented with validation rules
- ✅ Implementation guide created (quickstart.md)
- ✅ Constitution compliance verified

### Next Steps (Phase 2 - Tasks Generation)

Run `/sp.tasks` to generate actionable tasks from this plan. Expected task breakdown:

1. **Backend Service Layer** (2-3 tasks)
   - Implement UserProfileService with business logic
   - Add hard_delete method to UserRepository
   - Unit tests for service layer

2. **Backend API Routes** (2-3 tasks)
   - Implement profile endpoints (GET/PATCH)
   - Implement preferences endpoint (PATCH)
   - Implement account deletion endpoint (DELETE)
   - Implement admin user list endpoint (GET)
   - Integration tests for all routes

3. **Frontend API Client** (1 task)
   - Create TypeScript API client with type definitions

4. **Frontend Components** (2-3 tasks)
   - ProfileForm component with validation
   - PreferencesForm component with enum dropdowns
   - AccountDeleteDialog with password confirmation

5. **Frontend Pages** (2-3 tasks)
   - Profile page (/profile)
   - Preferences page (/preferences)
   - Admin users page (/admin/users) with pagination

6. **E2E Testing** (1-2 tasks)
   - Profile update flow (Playwright)
   - Account deletion flow (Playwright)

**Estimated Total**: 10-15 tasks, 3-5 days implementation

---

## Artifacts Generated

### Phase 0 (Research)
- ✅ [research.md](./research.md) - Technical discoveries, decisions, best practices

### Phase 1 (Design)
- ✅ [data-model.md](./data-model.md) - Entity relationships, validation rules, state transitions
- ✅ [contracts/profile.openapi.yaml](./contracts/profile.openapi.yaml) - Profile API contract
- ✅ [contracts/admin.openapi.yaml](./contracts/admin.openapi.yaml) - Admin API contract
- ✅ [quickstart.md](./quickstart.md) - Step-by-step implementation guide

### Phase 2 (Tasks) - Not Yet Created
- ⏳ [tasks.md](./tasks.md) - Generated by `/sp.tasks` command

---

## References

- [Feature Spec](./spec.md)
- [Research Document](./research.md)
- [Data Model](./data-model.md)
- [API Contracts](./contracts/)
- [Quickstart Guide](./quickstart.md)
- [F01 Authentication](../001-auth/)
- [F02 Database Schema](../002-database-schema/)
- [LearnPyByAI Constitution](../../.specify/memory/constitution.md)
