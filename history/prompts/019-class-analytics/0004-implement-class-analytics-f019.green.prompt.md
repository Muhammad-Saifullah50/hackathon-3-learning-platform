---
id: "0004"
title: Implement Class Analytics F019
stage: green
date: 2026-05-19
surface: agent
model: claude-sonnet-4-6
feature: 019-class-analytics
branch: master
user: Muhammad
command: /sp.implement
labels: ["analytics", "teacher-dashboard", "fastapi", "react-query", "f019"]
links:
  spec: specs/019-class-analytics/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - backend/src/repositories/analytics_repository.py
  - backend/src/schemas/dashboard.py
  - backend/src/dependencies.py
  - backend/src/api/v1/dashboard.py
  - frontend/src/lib/api/analytics.ts
  - frontend/src/hooks/useTeacherAnalytics.ts
  - frontend/src/components/teacher/AnalyticsDashboard.tsx
  - backend/tests/api/v1/test_teacher_analytics.py
  - backend/tests/api/__init__.py
  - backend/tests/api/v1/__init__.py
  - specs/019-class-analytics/tasks.md
tests:
  - backend/tests/api/v1/test_teacher_analytics.py (11 tests, all passing)
---

## Prompt

/sp.implement (no additional args — active feature 019-class-analytics detected from specs/)

## Response snapshot

Full implementation of F019 Class Analytics:

**Phase 1 (Setup):** Fixed stale `alembic_version` entry (`20260518_teacher_dashboard` → `20260518_mastery_snapshots`). Confirmed DB at head with 8 module rows.

**Phase 2 (Foundational — backend + frontend parallel):**
- Added `ModuleMasteryItem`, `StrugglingStudent`, `TeacherAnalyticsResponse` Pydantic schemas to `backend/src/schemas/dashboard.py`
- Created `AnalyticsRepository` with 4 async methods: `get_total_students()`, `get_avg_mastery()`, `get_module_mastery_breakdown()` (SQLAlchemy ORM with `func.replace`/`func.lower` for slug derivation from title), `get_struggling_students()` + `get_low_quiz_count()` (raw `DISTINCT ON` SQL — PostgreSQL-specific, verified on Neon)
- Registered `get_analytics_repository` factory in `backend/src/dependencies.py`
- Added `GET /api/v1/dashboard/teacher/analytics` endpoint: teacher/admin role guard (403), `asyncio.gather()` for all 5 queries in parallel, returns `TeacherAnalyticsResponse`
- Created `frontend/src/lib/api/analytics.ts` with `TeacherAnalytics` TS interface and `fetchTeacherAnalytics()`
- Created `frontend/src/hooks/useTeacherAnalytics.ts` using `@tanstack/react-query`, `staleTime: 30_000`

**Phases 3–6 (Frontend rewrite + Polish):**
- Rewrote `AnalyticsDashboard.tsx`: removed all hardcoded constants (`STAT_CARDS`, `MODULE_MASTERY`, `STRUGGLING_STUDENTS`, `WEEKLY_ACTIVITY`) and `LineChart`/`Line` recharts imports; wired `useTeacherAnalytics()`; 3 live stat cards (Total Students, Avg Mastery, Open Alerts) with loading skeletons; live BarChart with color-coded cells; live struggling students table with "All students are on track" empty state; error banner on fetch failure

**T013 Tests:** 11 integration tests in `backend/tests/api/v1/test_teacher_analytics.py` — auth boundary (401/403), teacher 200, correct counts, null avg_mastery, all 8 modules, boundary score 49% vs 50%. All 11 pass.

## Outcome

- ✅ Impact: Teacher analytics dashboard now shows live data from DB instead of hardcoded placeholders. Weekly Activity chart removed per FR-008.
- 🧪 Tests: 11 integration tests pass (auth, response shape, boundary conditions)
- 📁 Files: 3 new files, 5 modified
- 🔁 Next prompts: Run `alembic upgrade head` if new migrations added; implement F018 class management to enable per-teacher filtering
- 🧠 Reflection: `modules` table has `title` not `slug`/`name` — derived slug via `func.replace(func.lower(title), ' ', '_')`; `DISTINCT ON` is Postgres-only so tests mock the repository

## Evaluation notes (flywheel)

- Failure modes observed: Stale alembic_version entry blocked `alembic current`; fixed by direct DB UPDATE
- Graders run and results (PASS/FAIL): 11/11 PASS
- Prompt variant (if applicable): null
- Next experiment: Add per-teacher filtering once F018 class management lands
