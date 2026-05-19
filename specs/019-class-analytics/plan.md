# Implementation Plan: Class Analytics (F019)

**Branch**: `019-class-analytics` | **Date**: 2026-05-19 | **Spec**: [spec.md](spec.md)  
**Input**: Feature specification from `/specs/019-class-analytics/spec.md`

---

## Summary

Replace hardcoded placeholder data in the teacher analytics dashboard with live data queried from the existing `users`, `user_module_mastery`, `quiz_sessions`, and `modules` tables. Add one new read-only API endpoint (`GET /api/v1/dashboard/teacher/analytics`), a new `AnalyticsRepository`, and update `AnalyticsDashboard.tsx` to fetch and render real data. Remove the Weekly Activity line chart (out of scope per spec) and the Active Classes stat card (no class infrastructure exists). No new database tables or migrations required.

---

## Technical Context

**Language/Version**: Python 3.13 (backend) · TypeScript 5+ / React 19 (frontend)  
**Primary Dependencies**: FastAPI, SQLAlchemy 2.0+ async, Pydantic 2.0+, Next.js 14+, React Query (`@tanstack/react-query`), Recharts (chart already present)  
**Storage**: Neon PostgreSQL — reads from `users`, `user_module_mastery`, `quiz_sessions`, `modules` (all existing, no migrations)  
**Testing**: pytest + httpx async client (backend integration tests); vitest + @testing-library/react (frontend)  
**Target Platform**: Linux server (backend) + Vercel (frontend)  
**Project Type**: Web application — `backend/` + `frontend/`  
**Performance Goals**: Analytics endpoint p95 < 400ms (constitution hard limit for non-AI); dashboard load < 2s (SC-001)  
**Constraints**: No new tables; read-only; no class filtering (classless scope per research.md); teacher/admin role guard  
**Scale/Scope**: Up to 100 students, 10 classes (SC-001 reference), 8 modules — small dataset, no pagination needed

---

## Constitution Check

| Gate | Status | Notes |
|------|--------|-------|
| Repository pattern — no raw queries in routes | ✅ PASS | New `AnalyticsRepository`; route delegates to service/repo |
| Auth on all routes | ✅ PASS | `get_current_user` dependency + teacher role check |
| No `exec()`/`eval()` | ✅ N/A | No code execution |
| No hardcoded secrets | ✅ N/A | Read-only DB queries only |
| Testing targets (repos: 85%, routes: 80%) | ✅ PLANNED | Integration tests for endpoint + unit tests for repo queries |
| Alembic for schema changes | ✅ N/A | No schema changes |
| FastAPI route: `summary=` + `description=` | ✅ PLANNED | Included in endpoint definition |
| Black + isort formatting | ✅ PLANNED | Run before commit |
| React Query for data fetching | ✅ PLANNED | `useQuery` hook |
| FR-008: remove placeholder UI sections | ✅ PLANNED | Weekly Activity chart + Active Classes stat removed |

---

## Project Structure

### Documentation (this feature)

```text
specs/019-class-analytics/
├── plan.md              ← this file
├── research.md          ← Phase 0 output (complete)
├── data-model.md        ← Phase 1 output (complete)
├── contracts/
│   └── teacher-analytics.yaml   ← OpenAPI contract (complete)
├── quickstart.md        ← Phase 1 output
└── tasks.md             ← Phase 2 output (/sp.tasks — not created here)
```

### Source Code Changes

```text
backend/
├── src/
│   ├── repositories/
│   │   └── analytics_repository.py     [NEW] — 4 async query methods
│   ├── schemas/
│   │   └── dashboard.py                [MODIFY] — add TeacherAnalyticsResponse + sub-schemas
│   ├── api/v1/
│   │   └── dashboard.py                [MODIFY] — add GET /dashboard/teacher/analytics
│   └── dependencies.py                 [MODIFY] — register get_analytics_repository factory
└── tests/
    └── api/v1/
        └── test_teacher_analytics.py   [NEW] — integration tests

frontend/
└── src/
    ├── lib/api/
    │   └── analytics.ts                [NEW] — fetchTeacherAnalytics() typed fetch helper
    ├── hooks/
    │   └── useTeacherAnalytics.ts      [NEW] — useQuery wrapper
    └── components/teacher/
        └── AnalyticsDashboard.tsx      [MODIFY] — wire real data, remove placeholders
```

---

## Phase 0: Research — Complete

All unknowns resolved in [research.md](research.md). Key decisions:

| Decision | Outcome |
|----------|---------|
| Class scope | All platform students (no class table exists) |
| Active Classes stat | Removed (FR-008) |
| Quiz score source | `quiz_sessions` WHERE status='completed' AND score < 50 |
| Module names | JOIN with `modules` table |
| New tables/migrations | None |
| API router | Extend existing `dashboard.py` |
| Frontend fetching | React Query `useQuery` |
| Weekly Activity chart | Deleted |

---

## Phase 1: Design — Complete

All design artifacts produced:

- **data-model.md**: Entities, SQL query patterns, response shape, indexes
- **contracts/teacher-analytics.yaml**: Full OpenAPI 3.1 spec for `GET /dashboard/teacher/analytics`

---

## Phase 1: Implementation Design

### Backend

#### 1. `AnalyticsRepository` — `backend/src/repositories/analytics_repository.py`

Four async methods, all using SQLAlchemy `select()` (no raw SQL strings):

| Method | Returns | SQL Pattern |
|--------|---------|-------------|
| `get_total_students()` | `int` | COUNT(users WHERE role='student' AND deleted_at IS NULL) |
| `get_avg_mastery()` | `float \| None` | AVG(user_module_mastery.score) — None if no rows |
| `get_module_mastery_breakdown()` | `list[dict]` | LEFT JOIN modules + user_module_mastery, GROUP BY module, COALESCE(AVG, 0) |
| `get_struggling_students()` | `list[dict]` | DISTINCT ON(student_id) latest completed quiz < 50, JOIN users |

All methods take `AsyncSession` injected at construction.

#### 2. Pydantic Schemas — `backend/src/schemas/dashboard.py`

Add three schemas:

```python
class ModuleMasteryItem(BaseModel):
    module_slug: str
    module_name: str
    avg_score: float

class StrugglingStudent(BaseModel):
    student_id: str
    display_name: str
    score: float
    module_slug: str
    topic_label: str

class TeacherAnalyticsResponse(BaseModel):
    total_students: int
    avg_mastery: float | None
    low_quiz_count: int
    module_mastery: list[ModuleMasteryItem]
    struggling_students: list[StrugglingStudent]
```

#### 3. API Endpoint — `backend/src/api/v1/dashboard.py`

```
GET /api/v1/dashboard/teacher/analytics
Auth: get_current_user
Role guard: current_user.role not in ('teacher', 'admin') → 403
Response: TeacherAnalyticsResponse
```

Parallel queries using `asyncio.gather()` for total_students, avg_mastery, low_quiz_count, module_mastery, struggling_students to stay within 400ms budget.

#### 4. Dependency Factory — `backend/src/dependencies.py`

```python
async def get_analytics_repository(db=Depends(get_db)) -> AnalyticsRepository:
    return AnalyticsRepository(db)
```

---

### Frontend

#### 5. API Helper — `frontend/src/lib/api/analytics.ts`

Typed `fetchTeacherAnalytics()` using the same `fetch`-based pattern as `frontend/src/lib/api/chat.ts`. Returns `TeacherAnalytics` TypeScript interface matching the OpenAPI contract.

#### 6. React Query Hook — `frontend/src/hooks/useTeacherAnalytics.ts`

```typescript
export function useTeacherAnalytics() {
  return useQuery({
    queryKey: ['teacher', 'analytics'],
    queryFn: fetchTeacherAnalytics,
    staleTime: 30_000,   // 30s — analytics don't need real-time updates
  })
}
```

#### 7. `AnalyticsDashboard.tsx` — Changes

**Remove**:
- `WEEKLY_ACTIVITY` constant and the entire `LineChart` block (including recharts `LineChart`, `Line` imports if unused after removal)
- `STRUGGLING_STUDENTS`, `MODULE_MASTERY`, `STAT_CARDS` hardcoded constants
- `Active Classes` stat card

**Add**:
- `useTeacherAnalytics()` hook call at component top
- Loading state: skeleton or spinner while `isLoading`
- Error state: error message banner when `isError`
- Dynamic stat cards: Total Students, Avg Mastery, Open Alerts (3 cards instead of 4)
- Live `module_mastery` fed into the existing `BarChart`
- Live `struggling_students` fed into the existing table; empty state when list is empty

---

## Complexity Tracking

No constitution violations. No complexity justification needed.

---

## Risk Analysis

| Risk | Blast Radius | Mitigation |
|------|-------------|-----------|
| `DISTINCT ON` not supported or slow | Dashboard shows wrong/slow data | Verified PostgreSQL feature; indexed on `student_id` + `completed_at` |
| Teacher role check missing on endpoint | Any authenticated user can read all student data | Explicit 403 guard; integration test covers unauthorized student access |
| `user_module_mastery` empty for new deployments | `avg_mastery = None` → frontend crash | API returns `null`; frontend handles with `?? 'N/A'` |

---

## Acceptance Checks

- [ ] `GET /dashboard/teacher/analytics` with valid teacher token → 200 with correct counts
- [ ] Same endpoint with student token → 403
- [ ] No unauthenticated access → 401
- [ ] `total_students` matches COUNT of `role='student'` users in DB
- [ ] `avg_mastery` is null when `user_module_mastery` is empty; frontend shows "N/A"
- [ ] All 8 modules appear in `module_mastery`, missing modules show 0.0
- [ ] Student with last quiz score = 49% appears in `struggling_students`; 50% does not
- [ ] Weekly Activity chart is gone from DOM
- [ ] Active Classes stat card is gone from DOM
- [ ] Dashboard shows loading skeleton during fetch
- [ ] Dashboard shows error message when fetch fails (network error simulation)

---

## Follow-ups / Out of Scope

1. **F018 Class Management** — when implemented, add `teacher_id`-scoped filtering to `AnalyticsRepository` methods with a `teacher_id` parameter. The `Active Classes` stat card can be restored at that point.
2. **Weekly Activity chart** — can be re-introduced in a future feature once `code_sessions` + `quiz_sessions` daily aggregation is scoped.
3. **Individual student drill-down** — explicitly out of scope per spec.

---

📋 **Architectural decision detected**: Classless analytics scope — aggregating over all platform students instead of per-teacher class membership due to missing class infrastructure. Document? Run `/sp.adr classless-analytics-scope`
