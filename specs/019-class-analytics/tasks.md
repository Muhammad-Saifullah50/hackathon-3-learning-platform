# Tasks: Class Analytics (F019)

**Input**: Design documents from `/specs/019-class-analytics/`
**Feature Branch**: `019-class-analytics`
**Generated**: 2026-05-19

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: Which user story this task belongs to (US1–US3)
- Exact file paths are included in every task description

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Confirm prerequisites are met. No new migrations, no new packages — F019 reads only from existing tables (`users`, `user_module_mastery`, `quiz_sessions`, `modules`).

- [X] T001 Confirm `alembic current` is at head and all prior feature migrations (F015–F017) are applied; confirm `modules` table has 8 seeded rows with `slug` and `name` columns populated per `backend/alembic/versions/`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Backend repository, schemas, dependency factory, and endpoint; frontend fetch helper and React Query hook. All three user stories are served by a single API response, so this entire backend + frontend wiring is foundational before any user story UI work begins.

**⚠️ CRITICAL**: No user story phase can begin until this phase is complete.

- [X] T002 [P] Add three Pydantic schemas — `ModuleMasteryItem(module_slug, module_name, avg_score)`, `StrugglingStudent(student_id, display_name, score, module_slug, topic_label)`, `TeacherAnalyticsResponse(total_students, avg_mastery, low_quiz_count, module_mastery, struggling_students)` — in `backend/src/schemas/dashboard.py`
- [X] T003 Create `AnalyticsRepository` class with four async SQLAlchemy methods — `get_total_students()` (COUNT users WHERE role='student' AND deleted_at IS NULL), `get_avg_mastery()` (AVG from `user_module_mastery`, returns `float | None`), `get_module_mastery_breakdown()` (LEFT JOIN `modules` + `user_module_mastery`, GROUP BY module, COALESCE(AVG, 0)), `get_struggling_students()` (DISTINCT ON student_id latest completed quiz < 50, JOIN users) — in `backend/src/repositories/analytics_repository.py`
- [X] T004 Register `get_analytics_repository` async dependency factory (`AnalyticsRepository(db)`) in `backend/src/dependencies.py`
- [X] T005 Add `GET /api/v1/dashboard/teacher/analytics` endpoint in `backend/src/api/v1/dashboard.py` — role guard (403 if not teacher/admin), run all four repository methods via `asyncio.gather()`, return `TeacherAnalyticsResponse`; include FastAPI `summary=` and `description=` fields per constitution
- [X] T006 [P] Create `fetchTeacherAnalytics()` typed fetch helper with `TeacherAnalytics` TypeScript interface (matching `TeacherAnalyticsResponse` schema) in `frontend/src/lib/api/analytics.ts`; follow the same fetch pattern as `frontend/src/lib/api/chat.ts`
- [X] T007 Create `useTeacherAnalytics` React Query hook with `queryKey: ['teacher', 'analytics']`, `queryFn: fetchTeacherAnalytics`, `staleTime: 30_000` in `frontend/src/hooks/useTeacherAnalytics.ts` (depends on T006)

**Checkpoint**: Backend endpoint returns `TeacherAnalyticsResponse` for teacher token; frontend hook is wired and ready. User story UI phases can now begin.

---

## Phase 3: User Story 1 — View Real Class Overview Stats (Priority: P1) 🎯 MVP

**Goal**: Teacher opens dashboard and sees live stat cards — Total Students, Avg Mastery, Open Alerts — sourced from DB instead of hardcoded constants.

**Independent Test**: Teacher with at least one student in DB opens `/teacher/dashboard` and sees stat card values that change when a new student row is added to `users` table.

- [X] T008 [US1] Wire `useTeacherAnalytics()` in `frontend/src/components/teacher/AnalyticsDashboard.tsx` — add hook call at component top; add loading skeleton (spinner or Tailwind pulse placeholders) while `isLoading`; add error banner when `isError`; remove the hardcoded `STAT_CARDS` constant and the "Active Classes" stat card
- [X] T009 [US1] Render three live stat cards — "Total Students" from `total_students`, "Avg Mastery" from `avg_mastery` (null renders as "N/A"), "Open Alerts" from `low_quiz_count` — in `frontend/src/components/teacher/AnalyticsDashboard.tsx`

**Checkpoint**: US1 fully functional. Stat cards show real DB counts and update on page reload after DB changes.

---

## Phase 4: User Story 2 — View Module Mastery Bar Chart (Priority: P1)

**Goal**: Existing Recharts `BarChart` is fed live `module_mastery` data instead of the hardcoded `MODULE_MASTERY` constant; bars are color-coded by mastery band.

**Independent Test**: Bar chart shows values that differ from the prior hardcoded data when real mastery records exist in `user_module_mastery`; a module with no records shows 0%.

- [X] T010 [US2] Remove `MODULE_MASTERY` hardcoded constant; feed `data.module_mastery` array from `useTeacherAnalytics()` into the existing Recharts `BarChart`; apply color fill — red for avg_score < 40, amber for 40–70, green for > 70 — in `frontend/src/components/teacher/AnalyticsDashboard.tsx`

**Checkpoint**: US2 fully functional. Chart renders 8 module bars with live data; modules with no records show 0%.

---

## Phase 5: User Story 3 — View Students Needing Attention (Priority: P2)

**Goal**: Teacher sees a live list of students whose most recent completed quiz score is below 50%, including name, score, and module context. Empty state shown when no students qualify.

**Independent Test**: A student whose most recent completed quiz score is 40% appears in the list; a student at 60% does not; when list is empty the section shows "All students are on track".

- [X] T011 [US3] Remove `STRUGGLING_STUDENTS` hardcoded constant; render live `data.struggling_students` list in the existing table (columns: display_name, score, topic_label); show "All students are on track" empty-state message when the array is empty in `frontend/src/components/teacher/AnalyticsDashboard.tsx`

**Checkpoint**: US3 fully functional. Struggling students table reflects real quiz data.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Remove remaining placeholder UI (FR-008), add integration tests, and validate against quickstart acceptance checks.

- [X] T012 Remove `WEEKLY_ACTIVITY` constant and the entire Recharts `LineChart` block (including unused `LineChart` and `Line` recharts imports) from `frontend/src/components/teacher/AnalyticsDashboard.tsx` per FR-008
- [X] T013 [P] Create integration tests for `GET /api/v1/dashboard/teacher/analytics` covering: valid teacher token → 200 with correct `total_students` count, student token → 403, no auth → 401, `avg_mastery` is null when `user_module_mastery` is empty, all 8 modules present in `module_mastery` with missing modules at 0.0, student with score = 49% appears in `struggling_students` and student at score = 50% does not in `backend/tests/api/v1/test_teacher_analytics.py`
- [X] T014 Run all `quickstart.md` acceptance checks: backend `GET /dashboard/teacher/analytics` returns correct live counts for teacher token, browser shows loading skeleton during fetch delay, error banner appears on fetch failure (network error simulation), Weekly Activity `LineChart` is absent from DOM, Active Classes stat card is absent from DOM

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Setup — **BLOCKS all user story phases**
- **US1 (Phase 3)**: Depends on Foundational complete — no dependency on US2 or US3
- **US2 (Phase 4)**: Depends on Foundational complete — no dependency on US1 or US3 (different DOM sections, same hook)
- **US3 (Phase 5)**: Depends on Foundational complete — no dependency on US1 or US2
- **Polish (Phase 6)**: T012 can run any time after Foundational; T013 requires T005 (endpoint exists); T014 requires all story phases complete

### Within Each Phase

- T002 and T006 are marked [P] — can start simultaneously
- T007 depends on T006 (import)
- T005 depends on T002 (schemas) and T004 (dependency factory registered)
- T008 and T009 must be sequential (T009 uses hook already wired by T008)
- US1, US2, US3 story phases all touch `AnalyticsDashboard.tsx` — serialize them

### Parallel Opportunities

```bash
# Phase 2 — start these together (different files):
Task: T002 "Add Pydantic schemas in backend/src/schemas/dashboard.py"
Task: T003 "Create AnalyticsRepository in backend/src/repositories/analytics_repository.py"
Task: T006 "Create fetchTeacherAnalytics() in frontend/src/lib/api/analytics.ts"

# Phase 6 — these can run in parallel:
Task: T012 "Remove WEEKLY_ACTIVITY LineChart"
Task: T013 "Write integration tests"
```

---

## Implementation Strategy

### MVP First (US1 Only)

1. Complete Phase 1: Setup (T001)
2. Complete Phase 2: Foundational (T002–T007)
3. Complete Phase 3: US1 (T008–T009)
4. **STOP AND VALIDATE**: Stat cards show real DB values; teacher token returns 200; student token returns 403
5. Demo to stakeholders — the core value ("replace hardcoded data") is delivered

### Incremental Delivery

1. Setup + Foundational → endpoint live, hook ready
2. US1 (T008–T009) → Stat cards show real data (**MVP**)
3. US2 (T010) → Module mastery chart live
4. US3 (T011) → Struggling students list live
5. Polish (T012–T014) → Remove last placeholder, integration tests pass

---

## Notes

- F019 has no new DB migrations — confirm `alembic current` at head before starting
- All 3 user stories share one endpoint; the foundational phase delivers the full API response
- `avg_mastery` may be `null` if `user_module_mastery` is empty; frontend must guard with `?? 'N/A'`
- `DISTINCT ON` in `get_struggling_students` is a PostgreSQL feature — verified available on Neon
- Weekly Activity chart and Active Classes stat card MUST be removed before PR (FR-008)
- Teacher role check on endpoint is required — integration test T013 covers this boundary
