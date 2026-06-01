# Tasks: Enhanced Student Dashboard & Module Progress Detail

**Input**: Design documents from `/specs/017-enhanced-dashboard/`
**Feature Branch**: `017-enhanced-dashboard`
**Generated**: 2026-05-18

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: Which user story this task belongs to (US1–US5)
- Exact file paths are included in every task description

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Database migration that unblocks all backend work for this feature. No new packages required (recharts already in `frontend/package.json`).

- [X] T001 Create Alembic migration for `mastery_snapshots` table with columns (id UUID PK, user_id UUID FK, module_id INT FK, score FLOAT, recorded_at TIMESTAMPTZ) and indexes `idx_mastery_snapshots_user_recorded (user_id, recorded_at DESC)` and `idx_mastery_snapshots_user_module (user_id, module_id)` in `backend/alembic/versions/YYYYMMDD_add_mastery_snapshots.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [X] T002 [P] Create Pydantic schemas `MasteryHistoryResponse`, `MasterySnapshot`, `RecommendationItem`, `TopicProgressItem` in `backend/src/schemas/dashboard.py`
- [X] T003 [P] Extend `LearnPyByAIContext` with optional fields `agent_mode: Literal["recommendations", "module_detail"] | None = None` and `module_slug: str | None = None` in `backend/src/services/agents/context.py`
- [X] T004 [P] Add frontend TypeScript types `MasterySnapshot`, `TopicStatus`, `TopicProgressItem`, `Recommendation` to `frontend/src/types/index.ts`
- [X] T005 Create `backend/src/api/v1/dashboard.py` router skeleton (empty router with prefix `/api/v1`), mount it in `backend/src/main.py`, and register `get_mastery_snapshot_repository` dependency factory in `backend/src/dependencies.py`

**Checkpoint**: Foundation ready — all user story implementation can now begin.

---

## Phase 3: User Story 1 — Student Sees Richer Dashboard with Charts (Priority: P1) 🎯 MVP

**Goal**: Add "Mastery Over Time" line chart and "Module Mastery" bar chart to `/dashboard`, both rendered from DB data with no agent dependency.

**Independent Test**: Navigate to `/dashboard` as a student with at least one past mastery record. Both Recharts charts render with correct data. Page loads without waiting for any agent response. Brand-new student sees empty-state messages in both chart areas.

- [X] T006 [P] [US1] Create `MasterySnapshotRepository` with `insert_snapshot(user_id, module_id, score)` and `get_daily_averages(user_id)` (daily AVG(score) query grouped by DATE(recorded_at)) in `backend/src/repositories/mastery_snapshot_repository.py`
- [X] T007 [P] [US1] Extend `ProgressRepository.update_mastery_score()` to insert one row into `mastery_snapshots` as a side-effect after updating `user_module_mastery` in `backend/src/repositories/progress_repository.py`
- [X] T008 [US1] Implement `GET /api/v1/dashboard/mastery-history` endpoint in `backend/src/api/v1/dashboard.py` — queries `MasterySnapshotRepository.get_daily_averages()` for the authenticated student and returns `MasteryHistoryResponse`; returns `{"snapshots": []}` when no data exists
- [X] T009 [P] [US1] Create `mastery-timeline-chart.tsx` as a Recharts `<LineChart>` loaded via `next/dynamic({ ssr: false })`; x-axis = date, y-axis = avg_score (0–100); empty-state message "Start learning to see your progress here" when `snapshots.length === 0` in `frontend/src/components/dashboard/mastery-timeline-chart.tsx`
- [X] T010 [P] [US1] Create `module-mastery-chart.tsx` as a Recharts `<BarChart layout="vertical">`; one bar per module (all 8); colour-coded by mastery band (Red 0–40%, Yellow 41–70%, Green 71–90%, Blue 91–100%); empty state when all scores are 0 in `frontend/src/components/dashboard/module-mastery-chart.tsx`
- [X] T011 [P] [US1] Add `fetchMasteryHistory()` fetch helper to `frontend/src/lib/api/dashboard.ts` (creates the file if it does not exist)
- [X] T012 [US1] Integrate `MasteryTimelineChart` and `ModuleMasteryChart` into `dashboard-client.tsx` using React Query to fetch mastery history; charts appear alongside existing module cards without blocking page interactivity in `frontend/src/components/dashboard/dashboard-client.tsx`

**Checkpoint**: US1 fully functional and independently testable. Charts render from real DB data.

---

## Phase 4: User Story 2 — Student Receives AI-Generated Recommendations (Priority: P1)

**Goal**: "Recommended Next" card on `/dashboard` shows a loading state immediately then updates in-place with Progress Agent recommendations delivered via SSE — non-blocking.

**Independent Test**: Load the dashboard. The "Recommended Next" card appears immediately with loading state. Within ~15s it updates with AI content, without any page reload. If the agent fails/times out, a graceful fallback message with retry option is shown.

- [X] T013 [P] [US2] Add `get_recommendations_prompt(mastery_context: str) -> str` function to `backend/src/llm/prompts.py` — returns a system prompt directing the Progress Agent to produce 1–3 JSON `RecommendationItem` objects based on mastery scores
- [X] T014 [P] [US2] Extend `get_progress_agent()` in `backend/src/services/agents/agents.py` to branch `dynamic_instructions` on `agent_mode == "recommendations"`, returning the recommendations system prompt with mastery context from `LearnPyByAIContext`
- [X] T015 [US2] Implement `GET /api/v1/dashboard/recommendations/stream` SSE endpoint in `backend/src/api/v1/dashboard.py` — builds `LearnPyByAIContext(agent_mode="recommendations")` with the authenticated student's mastery scores, runs Progress Agent, streams `event: recommendation` events then `event: done`; emits `event: error` and closes on any exception; 30s server timeout
- [X] T016 [P] [US2] Add `recommendationsStreamUrl()` helper that returns the SSE endpoint URL to `frontend/src/lib/api/dashboard.ts`
- [X] T017 [US2] Create `use-recommendations-stream.ts` SSE hook — opens `EventSource` on mount, parses `recommendation` events into `Recommendation[]`, transitions state through `loading → loaded | error`; 30s client-side timeout fallback; closes connection on `done` event in `frontend/src/hooks/use-recommendations-stream.ts`
- [X] T018 [US2] Update `recommendations-panel.tsx` to accept `{ streamUrl: string }` prop instead of static `recommendations: string[]`; use `useRecommendationsStream` hook; show "Personalising your recommendations…" loading state; show fallback message with retry button on error/timeout in `frontend/src/components/dashboard/recommendations-panel.tsx`
- [X] T019 [US2] Wire updated `RecommendationsPanel` with SSE stream URL into `dashboard-client.tsx`; ensure it renders independently of chart data fetch in `frontend/src/components/dashboard/dashboard-client.tsx`

**Checkpoint**: US2 fully functional. Recommendations card loads asynchronously without blocking the dashboard.

---

## Phase 5: User Story 3 — Student Navigates from Module Card to Module Progress Detail (Priority: P1)

**Goal**: Module cards show "View Progress" instead of "Start Lesson". Clicking navigates to `/module/[moduleId]/progress` which renders immediately with a skeleton.

**Independent Test**: From the dashboard, click "View Progress" on any module card. The module detail page loads at the correct URL and shows at minimum a skeleton/loading state (topic list area) before any agent responds.

- [X] T020 [US3] Replace the "Start Lesson" primary action button with a "View Progress" button linking to `/module/{module.slug}/progress` in `frontend/src/components/dashboard/module-card.tsx`
- [X] T021 [P] [US3] Create `topic-skeleton.tsx` — shimmer skeleton matching the topic list layout (e.g., 5–8 skeleton rows with alternating covered/remaining widths) in `frontend/src/components/module-progress/topic-skeleton.tsx`
- [X] T022 [US3] Create `/module/[moduleId]/progress/page.tsx` — SSR auth check (redirect to `/login` if not authenticated); validate `moduleId` against `MODULE_SLUG_MAP` slugs (redirect to `/dashboard` on unknown slug); render module name header and `<TopicSkeleton />` placeholder (the live `TopicList` is wired in US4); in `frontend/src/app/(student)/module/[moduleId]/progress/page.tsx`

**Checkpoint**: US3 fully functional. Navigation from dashboard to module detail page works; page renders skeleton immediately.

---

## Phase 6: User Story 4 — Module Progress Detail Generated Asynchronously by Agent (Priority: P2)

**Goal**: The skeleton on `/module/[moduleId]/progress` is replaced by the Progress Agent's topic breakdown (covered / partial / remaining) delivered via SSE — without page reload.

**Independent Test**: Visit a module progress page. Loading skeleton appears instantly. Within ~15s it is replaced by the agent-generated topic breakdown sorted covered → remaining/partial alphabetically. If agent fails/times out, fallback message with retry button appears.

- [X] T023 [P] [US4] Add `get_module_detail_prompt(module_slug: str, mastery_context: str) -> str` to `backend/src/llm/prompts.py` — returns a system prompt instructing the Progress Agent to produce `TopicProgressItem` JSON objects for each topic in the given module, using the hardcoded per-module topic lists
- [X] T024 [P] [US4] Extend `get_progress_agent()` in `backend/src/services/agents/agents.py` to branch on `agent_mode == "module_detail"`, returning the module detail system prompt with `module_slug` and mastery context from `LearnPyByAIContext`
- [X] T025 [US4] Implement `GET /api/v1/module/{moduleId}/progress/stream` SSE endpoint in `backend/src/api/v1/dashboard.py` — validate `moduleId` against `MODULE_SLUG_MAP` (return 404 `{"detail": "Unknown module: '…'"}` on miss); build `LearnPyByAIContext(agent_mode="module_detail", module_slug=moduleId)` scoped to authenticated student's mastery scores; run Progress Agent; stream `event: topic` events then `event: done`; emits `event: error` on failure; 30s server timeout
- [X] T026 [P] [US4] Add `moduleProgressStreamUrl(moduleId: string)` helper to `frontend/src/lib/api/dashboard.ts`
- [X] T027 [US4] Create `use-module-progress-stream.ts` SSE hook — opens `EventSource` for the given `moduleId`; parses `topic` events into `TopicProgressItem[]`; on `done`, sorts topics: covered first then remaining/partial, alphabetically within each group; 30s client-side timeout; retry callback resets state and reopens connection in `frontend/src/hooks/use-module-progress-stream.ts`
- [X] T028 [US4] Create `topic-list.tsx` — uses `useModuleProgressStream`; shows `<TopicSkeleton />` while loading; renders sorted topic list with covered checkmark indicators and remaining/partial markers; fallback message + retry button on error/timeout in `frontend/src/components/module-progress/topic-list.tsx`
- [X] T029 [US4] Replace `<TopicSkeleton />` placeholder with `<TopicList moduleId={params.moduleId} />` in `frontend/src/app/(student)/module/[moduleId]/progress/page.tsx`

**Checkpoint**: US4 fully functional. Agent-generated topic breakdown loads asynchronously within the module progress page.

---

## Phase 7: User Story 5 — Remove Standalone /progress Page and Sidebar Link (Priority: P1)

**Goal**: `/progress` URL returns 404. Sidebar has no "Progress" link. Students use the new module-level experience exclusively.

**Independent Test**: Navigate directly to `/progress` — receive 404 (Next.js default). Confirm sidebar has no "Progress" link. Both checks pass without breaking any other navigation.

- [X] T030 [P] [US5] Delete `frontend/src/app/(student)/progress/page.tsx` (FR-016 — Next.js will return 404 automatically)
- [X] T031 [P] [US5] Remove the `{ label: 'Progress', href: '/progress' }` entry from `NAV_ITEMS` in `frontend/src/components/layout/nav-links.tsx`

**Checkpoint**: US5 complete. `/progress` returns 404; sidebar no longer shows the Progress link.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Production readiness, error resilience, and validation across all user stories.

- [X] T032 Run `alembic upgrade head` against Neon DB and verify `mastery_snapshots` table and both indexes exist (`\d mastery_snapshots` in psql)
- [X] T033 [P] Add React error boundaries wrapping `MasteryTimelineChart` and `ModuleMasteryChart` in `frontend/src/components/dashboard/dashboard-client.tsx` to prevent Recharts SSR/hydration crash from white-screening the dashboard
- [X] T034 Validate all scenarios in `specs/017-enhanced-dashboard/quickstart.md` in the dev environment: chart rendering (new + existing student), recommendations card lifecycle, "View Progress" navigation, module progress page skeleton → topic list, `/progress` → 404, sidebar link removal

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 — BLOCKS all user stories
- **US1 (Phase 3)**: Requires Phase 2 complete; no dependency on US2–US5
- **US2 (Phase 4)**: Requires Phase 2 complete; no dependency on US1 or US3–US5
- **US3 (Phase 5)**: Requires Phase 2 complete; no dependency on US1 or US2
- **US4 (Phase 6)**: Requires Phase 2 AND US3 complete (T029 extends the page created in T022)
- **US5 (Phase 7)**: Requires Phase 2 complete; fully independent
- **Polish (Phase 8)**: Requires Phase 1 (T032), and desired user stories complete

### User Story Dependencies

| Story | Depends on | Independent of |
|---|---|---|
| US1 (Charts) | Phase 1 + Phase 2 | US2, US3, US4, US5 |
| US2 (Recommendations) | Phase 2 | US1, US3, US4, US5 |
| US3 (Navigation) | Phase 2 | US1, US2, US4, US5 |
| US4 (Module Agent) | Phase 2 + US3 (T022 creates the page) | US1, US2, US5 |
| US5 (Removals) | Phase 2 | US1, US2, US3, US4 |

### Within Each User Story

- Repositories before endpoints (T006/T007 before T008)
- Endpoints before frontend integration (T008 before T012)
- Hooks before components that use them (T017 before T018; T027 before T028)
- Page scaffold before wiring live component (T022 before T029)

---

## Parallel Execution Examples

### Phase 2 (Foundational) — run T002, T003, T004 together

```
Task: T002 — Create backend/src/schemas/dashboard.py
Task: T003 — Extend LearnPyByAIContext in context.py
Task: T004 — Add frontend types to types/index.ts
```

### Phase 3 (US1) — run T006, T007, T009, T010, T011 together after T005

```
Task: T006 — MasterySnapshotRepository
Task: T007 — Extend ProgressRepository
Task: T009 — mastery-timeline-chart.tsx
Task: T010 — module-mastery-chart.tsx
Task: T011 — fetchMasteryHistory() helper
```

### Phase 4 (US2) — run T013, T014, T016 together after Phase 2

```
Task: T013 — get_recommendations_prompt() in prompts.py
Task: T014 — Progress Agent recommendations branching
Task: T016 — recommendationsStreamUrl() helper
```

### Phase 7 (US5) — run T030 and T031 together

```
Task: T030 — Delete progress/page.tsx
Task: T031 — Remove Progress nav item
```

---

## Implementation Strategy

### MVP First (US1 + US3 + US5 — no agent dependency)

1. Complete Phase 1: Setup (T001)
2. Complete Phase 2: Foundational (T002–T005)
3. Complete Phase 3: US1 — Charts (T006–T012)
4. Complete Phase 5: US3 — Navigation (T020–T022)
5. Complete Phase 7: US5 — Removals (T030–T031)
6. **STOP and VALIDATE**: Charts render, "View Progress" navigates correctly, `/progress` returns 404
7. Deploy/demo MVP if ready

### Incremental Delivery

1. Setup + Foundational → foundation ready
2. US1 → charts visible, test independently → demo
3. US3 + US5 → navigation change + cleanup, test independently → demo
4. US2 → recommendations card live, test independently → demo
5. US4 → module detail agent, test independently → full feature complete

### Parallel Team Strategy

With multiple developers, once Phase 2 is complete:

- **Developer A**: US1 (T006–T012) — all backend + frontend chart work
- **Developer B**: US2 (T013–T019) — recommendations SSE backend + frontend
- **Developer C**: US3 + US5 (T020–T022, T030–T031) — nav changes + removal
- Developer C also takes US4 (T023–T029) once US3 is complete

---

## Task Summary

| Phase | Stories | Task Count | Parallel Tasks |
|---|---|---|---|
| Phase 1: Setup | — | 1 | 0 |
| Phase 2: Foundational | — | 4 | 3 |
| Phase 3: US1 Charts | US1 (P1) | 7 | 5 |
| Phase 4: US2 Recommendations | US2 (P1) | 7 | 3 |
| Phase 5: US3 Navigation | US3 (P1) | 3 | 1 |
| Phase 6: US4 Module Agent | US4 (P2) | 7 | 2 |
| Phase 7: US5 Removals | US5 (P1) | 2 | 2 |
| Phase 8: Polish | — | 3 | 1 |
| **Total** | | **34** | |

---

## Notes

- `[P]` tasks = different files, no mutual dependencies — safe to run in parallel
- `[US#]` label maps each task to a specific user story for traceability
- US4 is the only story with a hard dependency on another story (US3 must create the page file first)
- Recharts is already installed — no package install step required
- No new environment variables are needed for this feature
- All SSE endpoints are read-only and stateless — they do not consume the chat quota from F15
- `mastery_snapshots` is append-only — no UPDATE or DELETE operations on this table
