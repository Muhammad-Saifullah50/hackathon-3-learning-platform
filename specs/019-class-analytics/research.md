# Research: 019-class-analytics

**Phase**: 0 — Unknowns Resolution  
**Date**: 2026-05-19

---

## Unknown 1 — Class/Membership Table Existence

**Question**: Does a `classes` / `class_memberships` table exist that F019 can query?

**Finding**: No. Alembic migrations checked (latest: `20260518_add_mastery_snapshots.py`). No `classes`, `class_memberships`, or `class_enrollment` tables are present. No corresponding SQLAlchemy model files exist under `backend/src/models/`. The 018-class-management feature was never specced or implemented.

**Decision**: Scope analytics to **all platform students** (users WHERE role='student'), not per-teacher class membership.

**Rationale**: The spec says "Fast scope: all classes combined" and FR-005 says "aggregate across all classes owned by the teacher." With no class infrastructure, a teacher-unscoped aggregate over all students achieves the same UX goal. FR-008 mandates removing any section that cannot be backed by real data — `Active Classes` stat is therefore **removed** from the dashboard.

**Alternatives considered**:
- Create `classes` + `class_memberships` tables in F019 — rejected; out of scope ("fast scope"), would double the feature size.
- Hardcode Active Classes = 0 — rejected; FR-008 explicitly bans placeholder data.

---

## Unknown 2 — Quiz Score Field for "Low Quiz Score" Detection

**Question**: Which field/table is the authoritative source of quiz scores for struggle detection?

**Finding**: `quiz_sessions` table (`backend/src/models/quiz_session.py`) has:
- `score: Float | None` (0–100 range, nullable)
- `status: str` — values: `'generated'`, `'in_progress'`, `'completed'`
- `student_id: UUID`
- `completed_at: TIMESTAMP`

**Decision**: Use `quiz_sessions` where `status='completed'` AND `score IS NOT NULL` AND `score < 50`. "Most recent" = MAX(`completed_at`) per student via a window function or subquery.

**Rationale**: Only completed quizzes have reliable scores. `score IS NOT NULL` guard prevents false positives from in-progress sessions.

---

## Unknown 3 — Module Name Lookup for Chart Labels

**Question**: How are module slugs mapped to human-readable names?

**Finding**: `modules` table exists (seeded via `20260315_0655_002g_seed_curriculum.py`). `Module` model in `backend/src/models/curriculum.py` has `name` and `slug` columns. The 8 modules are: Basics, Control Flow, Data Structures, Functions, OOP, Files, Errors, Libraries.

**Decision**: JOIN `user_module_mastery` with `modules` on `module_id` to get `name` and `slug` for each bar in the chart.

---

## Unknown 4 — Existing Dashboard API Pattern

**Question**: Should teacher analytics go in the existing `dashboard.py` router or a new router?

**Finding**: `backend/src/api/v1/dashboard.py` uses `APIRouter(prefix="/dashboard")`. It currently serves student-facing endpoints (`/dashboard/mastery-history`, `/dashboard/recommendations/stream`). No teacher endpoints exist yet.

**Decision**: Add teacher analytics to the **same `dashboard.py` router** under `/dashboard/teacher/analytics`. Avoids creating a new file for a single endpoint; all dashboard reads live in one place.

**Rationale**: Consistent with existing pattern; teacher analytics is read-only like the existing student endpoints. If teacher endpoints multiply (future), they can be split to `teacher_dashboard.py` at that time.

---

## Unknown 5 — Frontend Data Fetching Pattern

**Question**: Does the project use React Query, SWR, or plain fetch for API calls in the teacher dashboard?

**Finding**: `frontend/src/` uses React Query (`@tanstack/react-query`) confirmed in feature 013 setup. `AnalyticsDashboard.tsx` currently has no data fetching — all data is hardcoded module-level constants. The component is rendered inside `frontend/src/app/(teacher)/teacher/dashboard/`.

**Decision**: Fetch analytics via `useQuery` from React Query in `AnalyticsDashboard.tsx`. Follow the same pattern as existing hooks (`useChatSessions`, `useChatQuota`, etc.).

---

## Unknown 6 — Weekly Activity Chart Fate

**Question**: The spec says the Weekly Activity chart (line chart) MUST be removed. Confirm this is safe to delete.

**Finding**: The `WEEKLY_ACTIVITY` data and `LineChart` component are entirely within `AnalyticsDashboard.tsx` — no other component imports them. Safe to delete.

**Decision**: Remove the `LineChart` block, the `WEEKLY_ACTIVITY` constant, and the `LineChart` import from recharts entirely.

---

## Summary of Decisions

| Decision | Outcome |
|----------|---------|
| Class scope | All platform students (no class filtering) |
| Active Classes stat | Removed (FR-008, no data) |
| Quiz score source | `quiz_sessions` WHERE status='completed' AND score < 50 |
| Module names | JOIN with `modules` table |
| New tables | None |
| API router | Extend existing `dashboard.py` |
| Frontend fetching | React Query `useQuery` |
| Weekly Activity chart | Deleted |
