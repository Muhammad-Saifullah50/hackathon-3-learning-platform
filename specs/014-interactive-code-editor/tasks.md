# Tasks: Interactive Code Editor (014)

**Input**: Design documents from `/specs/014-interactive-code-editor/`
**Prerequisites**: plan.md ✅, spec.md ✅, data-model.md ✅, contracts/openapi.yaml ✅, quickstart.md ✅

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1–US5)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Install dependencies and scaffold new file paths before implementation begins.

- [X] T001 Install `@monaco-editor/react` v4.x in `frontend/` (`npm install @monaco-editor/react`)
- [X] T002 [P] Create backend file stubs: `backend/src/models/code_session.py`, `backend/src/repositories/code_session_repository.py`, `backend/src/schemas/code_editor.py`, `backend/src/services/code_session_service.py`, `backend/src/api/v1/code_editor.py`
- [X] T003 [P] Create frontend file stubs: `frontend/src/components/editor/CodeEditorPanel.tsx`, `frontend/src/components/editor/OutputPanel.tsx`, `frontend/src/components/editor/CodeFeedbackSection.tsx`, `frontend/src/components/editor/TutorPanel.tsx`, `frontend/src/hooks/useCodeSession.ts`, `frontend/src/hooks/useCodeExecution.ts`, `frontend/src/hooks/useCodeFeedback.ts`, `frontend/src/lib/code-editor-api.ts`, `frontend/src/app/(student)/playground/page.tsx`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Database migrations and shared service infrastructure that ALL user stories depend on.

**⚠️ CRITICAL**: No user story implementation can begin until this phase is complete.

- [X] T004 Add `user_daily = "user_daily"` to `IdentifierType` enum in `backend/src/auth/models.py`
- [X] T005 Create Alembic migration 1: add `user_daily` to `identifiertype` PostgreSQL enum (`alembic revision --autogenerate -m "add_user_daily_identifier_type"`) — verify it adds only the enum value, no table changes
- [X] T006 [P] Implement `CodeSession` SQLAlchemy model in `backend/src/models/code_session.py` — composite PK `(user_id, context_key)`, FK to `users.id` ON DELETE CASCADE, `code TEXT NOT NULL DEFAULT ''`, `created_at`/`updated_at` with timezone
- [X] T007 Create Alembic migration 2: create `code_sessions` table (`alembic revision --autogenerate -m "create_code_sessions_table"`) — verify composite PK and FK; depends on T006
- [X] T008 Apply both migrations: `alembic upgrade head` in `backend/` — verify `code_sessions` table and `user_daily` enum value exist in Neon; depends on T005, T007
- [X] T009 [P] Implement `CodeSessionRepository` in `backend/src/repositories/code_session_repository.py` — `async def upsert(db, user_id, context_key, code) -> CodeSession` using `pg_insert().on_conflict_do_update()` on composite PK; `async def get(db, user_id, context_key) -> CodeSession | None`
- [X] T010 [P] Implement Pydantic schemas in `backend/src/schemas/code_editor.py` — `SaveCodeRequest` (code: str, max_length=100000), `CodeSessionResponse` (context_key, code, updated_at)
- [X] T011 Implement `CodeSessionService` in `backend/src/services/code_session_service.py` — `async def save_code(db, user_id, context_key, code)` delegating to repo; `async def load_code(db, user_id, context_key)` returning None if not found; `async def check_and_increment_daily_limit(db, user_id, action, limit=3) -> bool` using `RateLimitCounter` with identifier format `"{user_id}:{action}:{YYYY-MM-DD}"` and `IdentifierType.user_daily`; depends on T009
- [X] T012 Add `get_code_session_repository` dependency factory in `backend/src/dependencies.py` returning `CodeSessionRepository` instance
- [X] T013 [P] Implement typed frontend API client in `frontend/src/lib/code-editor-api.ts` — `loadCodeSession(contextKey): Promise<CodeSessionResponse | null>` (GET, returns null on 404) and `saveCodeSession(contextKey, code): Promise<CodeSessionResponse>` (PUT); use `NEXT_PUBLIC_BACKEND_URL`

**Checkpoint**: Migrations applied, CodeSessionService with rate limit logic available, typed API client ready.

---

## Phase 3: User Story 1 — Write and Run Python Code (Priority: P1) 🎯 MVP

**Goal**: Student can write Python code in Monaco editor, click Run, and see stdout/stderr/execution time in the output panel. Error lines are highlighted in the editor. Daily run limit enforced.

**Independent Test**: Open Playground, type `print("hello")`, click Run → "hello" appears in output panel within 5s — no AI, no submission, no persistence required.

### TDD: Rate Limit Business Logic (required by plan.md §Constitution)

- [X] T014 [P] [US1] Write failing unit tests for `check_and_increment_daily_limit` in `backend/tests/unit/test_code_session_service.py` — cases: first request (counter=0→1, returns True), second request (counter=2→3, returns True), limit reached (counter=3, returns False), new calendar day creates new key; run `pytest backend/tests/unit/test_code_session_service.py` and confirm all fail

### Implementation for User Story 1

- [X] T015 [US1] Add `parse_error_line(stderr: str) -> int | None` utility in `backend/src/api/v1/code_execution.py` — regex `r'line (\d+)'`; add `error_line: int | None` to execution response dict (FR-004)
- [X] T016 [US1] Add daily run rate limit check in `backend/src/api/v1/code_execution.py` — call `code_session_service.check_and_increment_daily_limit(db, user.id, "run", limit=3)` before sandbox call; return HTTP 429 `RateLimitErrorResponse` with `retry_after` = next calendar day ISO string on False (FR-025); depends on T011, T015
- [X] T017 [P] [US1] Implement `OutputPanel` component in `frontend/src/components/editor/OutputPanel.tsx` — displays stdout (green), stderr (red), execution time, timeout message, 429 rate limit message; accepts `result: ExecutionResult | null` and `isLoading: boolean` props; monospace dark theme
- [X] T018 [US1] Implement `useCodeExecution` hook in `frontend/src/hooks/useCodeExecution.ts` — `runCode(code: string)` POSTs to `/api/v1/code-execution`, manages `isRunning` state (button disabled while in-flight, FR-027), handles 429 with user-friendly message, returns `ExecutionResult`; depends on T016
- [X] T019 [US1] Implement `CodeEditorPanel` component in `frontend/src/components/editor/CodeEditorPanel.tsx` — accepts `EditorConfig` prop (`mode`, `contextKey`, `starterCode?`, `exerciseId?`, `isGraded?`); renders Monaco via `next/dynamic({ ssr: false })`; Python language, syntax highlighting, line numbers, bracket matching; Run button wired to `useCodeExecution`; on error result, calls `monaco.editor.setModelMarkers` + `deltaDecorations` for `errorLine`; clears markers on next Run click (FR-001, FR-002, FR-003, FR-004, FR-005); depends on T017, T018
- [X] T020 [US1] Create Playground page in `frontend/src/app/(student)/playground/page.tsx` — renders `<CodeEditorPanel config={{ mode: "playground", contextKey: "playground" }} />`; protected route (student auth required) (FR-006)
- [X] T021 [US1] Add "Playground" nav item in `frontend/src/components/layout/student-sidebar.tsx` — links to `/playground`; appears for authenticated students (FR-006)

**Checkpoint**: Student can open Playground, write and run code, see output with error highlighting, and hit 429 after 3 runs. Fully testable without AI or persistence.

---

## Phase 4: User Story 2 — Get AI Feedback on Code (Priority: P2)

**Goal**: Student clicks "Review with Tutor", sees loading indicator, then structured AI feedback in a dedicated section below the editor. Can ask follow-up questions in that same section.

**Independent Test**: Write a function, click "Review with Tutor" → loading indicator appears in code feedback section → AI feedback renders below editor — no lesson context or submission needed.

### Implementation for User Story 2

- [X] T022 [US2] Add daily review rate limit check in `backend/src/api/v1/agents.py` — when `code_snippet` is present in request body, call `check_and_increment_daily_limit(db, user.id, "review", limit=3)` before routing to agent; return HTTP 429 `RateLimitErrorResponse` on False; general tutor messages without `code_snippet` are NOT rate limited (FR-026); depends on T011
- [X] T023 [P] [US2] Implement `CodeFeedbackSection` component in `frontend/src/components/editor/CodeFeedbackSection.tsx` — displays conversation messages (user + assistant turns); "Review with Tutor" button triggers review with current code snapshot; follow-up text input; loading indicator (spinner); error message on AI unavailability; monospace dark background, separated from editor by visible boundary line; styled to match editor (FR-011–FR-016)
- [X] T024 [US2] Implement `useCodeFeedback` hook in `frontend/src/hooks/useCodeFeedback.ts` — manages conversation messages array; `reviewCode(code, errorContext?)` POSTs to `/api/v1/agents/chat` with `code_snippet`, `session_id = "code-{contextKey}-{userId}"`; `sendFollowUp(message)` continues conversation; `isReviewing` state for button disable (FR-027); handles 429 with section-level message; cancels in-flight request on unmount (FR-018); depends on T022
- [X] T025 [US2] Wire `CodeFeedbackSection` and `useCodeFeedback` into `CodeEditorPanel.tsx` — "Review with Tutor" button appears above feedback section; on run+error, passes error context to review; depends on T019, T023, T024

**Checkpoint**: AI code review conversation fully functional below editor, rate-limited, conversation-isolated from general tutor.

---

## Phase 5: User Story 3 — General Tutor Chat Panel (Priority: P2)

**Goal**: Collapsible right-side panel for general Python questions, fully independent from code feedback, collapsed by default on viewports < 1024px.

**Independent Test**: Open Playground, expand right tutor panel, ask "what is a list comprehension?" → general answer appears in panel — no code execution or review involved.

### Implementation for User Story 3

- [X] T026 [US3] Implement `TutorPanel` component in `frontend/src/components/editor/TutorPanel.tsx` — collapsible right panel; toggle button (expand/collapse); conversation chat UI for general Python questions; POSTs to `/api/v1/agents/chat` with `session_id = "tutor-{userId}-{sessionUuid}"` (new UUID per page load, no code_snippet); default collapsed when `window.innerWidth < 1024` on mount; panel state via `useState` (session-only, not persisted); on collapse, editor area expands to fill space (FR-017–FR-020)
- [X] T027 [US3] Wire `TutorPanel` into `CodeEditorPanel.tsx` layout — render as right sibling; horizontal flex layout with editor taking remaining space; depends on T019, T026

**Checkpoint**: Right tutor panel works independently; conversations in panel and code feedback section never mix.

---

## Phase 6: User Story 4 — Submit a Graded Exercise (Priority: P3)

**Goal**: When `isGraded === true`, a Submit button appears. Student clicks Submit, code is evaluated against test cases, pass/fail result displays in output panel with failing test case details.

**Independent Test**: On a lesson exercise page with `isGraded=true`, write correct code, click Submit → output panel shows pass result with test details — testable without Playground or general chat.

### Implementation for User Story 4

- [X] T028 [US4] Add Submit button to `CodeEditorPanel.tsx` — visible only when `config.isGraded === true` (FR-021, FR-022); on click: save code via `useCodeSession.saveToBackend()` then POST to `/api/v1/agents/exercise-submit` with `{ exercise_id: config.exerciseId, code }`; `isSubmitting` state disables button during in-flight (FR-023); display `SubmissionResult` (pass/fail, failing test cases) in `OutputPanel` on response (FR-024); depends on T019
- [X] T029 [US4] Extend `OutputPanel.tsx` to render `SubmissionResult` — show pass/fail status, list failing test cases with input/expected/actual columns, timeout message on 5s exceeded (FR-024)

**Checkpoint**: Submit flow complete in embedded graded mode; standalone Playground has no Submit button.

---

## Phase 7: User Story 5 — Code Auto-Save and Persistence (Priority: P3)

**Goal**: Code auto-saves to localStorage (5s debounce) and to backend on Run/Submit/Review actions. Code restores on return, per-context (Playground vs lesson code never overwrite each other).

**Independent Test**: Write code in Playground, close browser, reopen → code restored exactly — testable without AI or submission features.

### Implementation for User Story 5

- [X] T030 [US5] Implement GET endpoint in `backend/src/api/v1/code_editor.py` — `GET /api/v1/code-sessions/{context_key}`: call `code_session_service.load_code(db, user.id, context_key)`; return `CodeSessionResponse` or 404 if not found (FR-009); depends on T011, T012, T013
- [X] T031 [US5] Implement PUT endpoint in `backend/src/api/v1/code_editor.py` — `PUT /api/v1/code-sessions/{context_key}`: validate `SaveCodeRequest` (max 100,000 chars); call `code_session_service.save_code(db, user.id, context_key, code)`; return `CodeSessionResponse` (FR-008, FR-010); depends on T030
- [X] T032 [US5] Implement `useCodeSession` hook in `frontend/src/hooks/useCodeSession.ts` — on editor mount: load from localStorage key `learnpybyai:code:{userId}:{contextKey}` first, then simultaneously fetch backend via `code-editor-api.ts`; if backend `updated_at` is newer, replace localStorage; `saveToLocalStorage(code)` debounced 5s (FR-007); `saveToBackend(code)` called on Run/Submit/Review actions (FR-008); handles localStorage unavailable gracefully (silently skip, FR edge case); handles backend save failure with silent retry + subtle indicator on repeated failure; depends on T013, T031
- [X] T033 [US5] Wire `useCodeSession` into `CodeEditorPanel.tsx` — on load: restore code from hook; on keystroke: trigger debounced local save; pass `saveToBackend` to `useCodeExecution`, `useCodeFeedback`, Submit handler so each calls it before its own request (FR-008, FR-010); depends on T019, T025, T028, T032

**Checkpoint**: Code persists across browser restarts and devices; Playground and lesson contexts never collide.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Validation, error path review, and quickstart verification.

- [X] T034 [P] Verify Monaco `next/dynamic` setup in `CodeEditorPanel.tsx` — confirm `ssr: false`, that Monaco is excluded from SSR bundle; run `next build` and check that no SSR errors appear (plan.md constraint)
- [X] T035 [P] Review 429 display paths end-to-end — run rate limit exceeded (T016): message in `OutputPanel`; review limit exceeded (T022): message in `CodeFeedbackSection`; confirm buttons re-enable after 429 (FR-027)
- [ ] T036 Run quickstart.md happy path — start backend + frontend, log in as student, execute all 8 steps in quickstart.md §5, verify each step completes without errors

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately; T002 and T003 are parallel
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all user stories
  - T004 → T005 (migration 1)
  - T006 → T007 (migration 2)
  - T005 + T007 → T008 (apply migrations)
  - T008 → T009, T010 (repo and schemas can be parallel after migrations)
  - T009 → T011 (service depends on repo)
  - T011 → T012 → T013 (dependency, router)
  - T013 → T013 (parallel with T013: frontend API client)
- **Phase 3 (US1)**: Depends on Foundational completion; T014 (TDD) parallel with T015
- **Phase 4 (US2)**: Depends on Foundational + Phase 3 (CodeEditorPanel exists); T022 parallel with T023
- **Phase 5 (US3)**: Depends on Phase 3 (CodeEditorPanel layout exists)
- **Phase 6 (US4)**: Depends on Phase 3 (CodeEditorPanel) + Phase 7 (useCodeSession.saveToBackend)
- **Phase 7 (US5)**: Depends on Foundational (endpoints depend on T011–T013); T030→T031→T032→T033
- **Phase 8 (Polish)**: Depends on all stories complete

### User Story Dependencies

| Story | Depends On | Notes |
|-------|-----------|-------|
| US1 (P1) | Phase 2 complete | Core — all others depend on CodeEditorPanel |
| US2 (P2) | Phase 2 + US1 (CodeEditorPanel) | Code feedback wired into panel |
| US3 (P2) | US1 (CodeEditorPanel layout) | TutorPanel is a sibling component |
| US4 (P3) | US1 + US5 (saveToBackend) | Submit flow saves code first |
| US5 (P3) | Phase 2 (endpoints) + US1 (wire into panel) | Persistence is layered onto existing panel |

### Parallel Opportunities Within Phases

- **Phase 1**: T002 ∥ T003
- **Phase 2**: T004 ∥ T006 (until migrations created); T009 ∥ T010 ∥ T013 (after T008)
- **Phase 3**: T014 ∥ T015; T017 ∥ T018 (different files)
- **Phase 4**: T022 ∥ T023 (backend vs frontend)
- **Phase 8**: T034 ∥ T035

---

## Parallel Example: Phase 2 Foundational

```bash
# Step A — parallel (different files, no deps):
Task T004: "Add user_daily to IdentifierType in backend/src/auth/models.py"
Task T006: "Implement CodeSession SQLAlchemy model in backend/src/models/code_session.py"

# Step B — sequential (migration depends on model code):
Task T005: "Create Alembic migration 1 (user_daily enum)"     # after T004
Task T007: "Create Alembic migration 2 (code_sessions table)" # after T006

# Step C — sequential (must apply after both migrations):
Task T008: "Run alembic upgrade head"                          # after T005 + T007

# Step D — parallel (after T008, different files):
Task T009: "Implement CodeSessionRepository"
Task T010: "Implement Pydantic schemas in code_editor.py"
Task T013: "Implement frontend code-editor-api.ts"
```

---

## Parallel Example: Phase 3 (US1)

```bash
# Can run in parallel — different files:
Task T014: "Write failing unit tests for rate limit logic"         # [P]
Task T015: "Add error_line parsing to code_execution.py"          # [P]

# Then:
Task T016: "Add daily run rate limit to code_execution.py"        # after T015
Task T017: "Implement OutputPanel.tsx"                            # [P] after T014 done
Task T018: "Implement useCodeExecution.ts"                        # after T016
Task T019: "Implement CodeEditorPanel.tsx"                        # after T017, T018
Task T020: "Create Playground page.tsx"                           # after T019
Task T021: "Add Playground nav item in student-sidebar.tsx"       # [P] after T019
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL — blocks all stories)
3. Complete Phase 3: User Story 1 (Write and Run Code)
4. **STOP and VALIDATE**: Open Playground, run `print("hello")`, confirm output
5. Demo — students can write and execute Python code

### Incremental Delivery

1. Setup + Foundational → migrations applied, services ready
2. US1 → Monaco editor + Run + output + error highlighting + rate limit (**MVP**)
3. US2 → AI code review in-editor (adds tutoring loop)
4. US3 → General tutor panel (adds general Q&A)
5. US5 → Auto-save + persistence (adds reliability)
6. US4 → Graded submission (closes the learning loop)

### Suggested MVP Scope

**Ship after T001–T021** (Phase 1 + Phase 2 + Phase 3): Students can write, run, and get error feedback on Python code. This is independently demonstrable with zero AI dependency.

---

## Summary

| Phase | User Story | Tasks | Parallelizable |
|-------|-----------|-------|----------------|
| Phase 1: Setup | — | T001–T003 | T002 ∥ T003 |
| Phase 2: Foundational | — | T004–T013 | T004∥T006, T009∥T010∥T013 |
| Phase 3: US1 (P1) | Write and Run Code | T014–T021 | T014∥T015, T017∥T018 |
| Phase 4: US2 (P2) | AI Code Feedback | T022–T025 | T022∥T023 |
| Phase 5: US3 (P2) | General Tutor Panel | T026–T027 | — |
| Phase 6: US4 (P3) | Graded Submission | T028–T029 | — |
| Phase 7: US5 (P3) | Auto-Save & Persistence | T030–T033 | — |
| Phase 8: Polish | — | T034–T036 | T034∥T035 |
| **Total** | | **36 tasks** | |

- [P] tasks in same phase = different files, no cross-task dependencies
- Each user story is independently testable after its phase completes
- Suggested MVP: Phases 1–3 (T001–T021, 21 tasks)
