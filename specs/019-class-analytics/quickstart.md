# Quickstart: 019-class-analytics

**For developers picking up this feature.**

---

## Prerequisites

- Feature branches 001–007, 013–017 merged (all migrations applied to Neon)
- F015 migration `20260511_add_chat_session_title_surface.py` applied
- F016 migration `20260517_create_quiz_sessions_table.py` applied
- F017 migration `20260518_add_mastery_snapshots.py` applied
- `.env` with `DATABASE_URL` pointing to Neon PostgreSQL

---

## No Migrations Required

F019 reads only from existing tables:
- `users` — role='student' filter
- `user_module_mastery` — mastery scores
- `quiz_sessions` — quiz results
- `modules` — module metadata (8 rows, seeded)

Run `alembic current` to confirm you're on head before starting.

---

## New Files to Create

### Backend

```bash
# 1. Analytics repository
touch backend/src/repositories/analytics_repository.py

# 2. Integration test
touch backend/tests/api/v1/test_teacher_analytics.py
```

### Frontend

```bash
# 3. API fetch helper
touch frontend/src/lib/api/analytics.ts

# 4. React Query hook
touch frontend/src/hooks/useTeacherAnalytics.ts
```

---

## Files to Modify

| File | Change |
|------|--------|
| `backend/src/schemas/dashboard.py` | Add `ModuleMasteryItem`, `StrugglingStudent`, `TeacherAnalyticsResponse` |
| `backend/src/api/v1/dashboard.py` | Add `GET /dashboard/teacher/analytics` endpoint |
| `backend/src/dependencies.py` | Register `get_analytics_repository` |
| `frontend/src/components/teacher/AnalyticsDashboard.tsx` | Wire real data, remove placeholders, delete weekly chart |

---

## Verify Backend Works

```bash
cd backend

# Run the analytics integration test
pytest tests/api/v1/test_teacher_analytics.py -v

# Or start the server and hit the endpoint manually
uvicorn src.main:app --reload
# POST /api/v1/auth/login → get token
# GET /api/v1/dashboard/teacher/analytics with Authorization: Bearer <token>
```

---

## Verify Frontend Works

```bash
cd frontend
npm run dev
# Navigate to http://localhost:3000/teacher/dashboard
# Stat cards and module chart should show real DB values (not hardcoded)
# Weekly Activity chart should be absent from the page
```

---

## Seed Data for Testing (Optional)

If your local DB has no mastery records or quiz sessions:

```sql
-- Add a test student
INSERT INTO users (id, email, password_hash, role, display_name)
VALUES (gen_random_uuid(), 'student1@test.com', 'hash', 'student', 'Test Student');

-- Add a low quiz score (triggers struggling student list)
INSERT INTO quiz_sessions
  (id, student_id, chat_session_id, module_slug, topic_label, status, score, questions, completed_at)
VALUES
  (gen_random_uuid(),
   '<student-uuid>',
   '<any-agent-session-uuid>',
   'basics', 'Variables', 'completed', 42.0, '[]'::jsonb,
   NOW());
```

---

## Key Acceptance Checks Before PR

- `GET /dashboard/teacher/analytics` → 200 with real counts
- Student token → 403
- No auth → 401
- Weekly Activity chart absent in browser
- Active Classes stat card absent
- Loading skeleton visible during fetch
- Empty state shown when no struggling students
