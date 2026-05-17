# Tasks: Quiz System (F16)

**Input**: Design documents from `/specs/016-quiz-system/`
**Branch**: `016-quiz-system` | **Date**: 2026-05-17
**Prerequisites**: plan.md ✅ · spec.md ✅ · research.md ✅ · data-model.md ✅ · contracts/ ✅

**Tests**: Not included by default (not requested in spec). Add if TDD approach is adopted.

**Organization**: Tasks grouped by user story to enable independent implementation and testing.

---

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no shared dependencies)
- **[Story]**: Which user story this task belongs to (US1–US4)
- File paths are relative to repository root

---

## Phase 1: Setup (Database Migration)

**Purpose**: Apply schema changes before any code that reads/writes quiz sessions can run.

- [X] T001 Create Alembic migration file `backend/alembic/versions/20260517_create_quiz_sessions_table.py` (full content specified in data-model.md — creates `quiz_sessions` table with all columns, constraints, and 5 indexes)
- [X] T002 Run `alembic upgrade head` in `backend/` to apply the migration and verify `quiz_sessions` table exists with all columns

**Checkpoint**: `quiz_sessions` table live in Neon PostgreSQL — all subsequent phases can now run against the schema.

---

## Phase 2: Foundational (Core Data & Schema Layer)

**Purpose**: Backend data layer that MUST exist before any quiz endpoint or agent code can be implemented.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [X] T003 Create `QuizSession` SQLAlchemy model in `backend/src/models/quiz_session.py` (columns, CheckConstraints, Indexes, TimestampMixin — exact model specified in data-model.md)
- [X] T004 Register `QuizSession` in `backend/src/models/__init__.py` so Alembic autogenerate discovers it
- [X] T005 [P] Create `QuizSessionRepository` in `backend/src/repositories/quiz_session_repository.py` with async methods: `create()`, `get_by_id()`, `update_answers_and_grades()`, `mark_completed()`, `list_by_student()` (returns rows ordered by `created_at DESC`)
- [X] T006 [P] Create quiz Pydantic schemas in `backend/src/schemas/quiz.py`: `QuizSessionState`, `GradeFlashcardRequest`, `GradeFlashcardResponse`, `SubmitQuizRequest` (with `MCQAnswerItem`), `SubmitQuizResponse` (with `PerCardResult`), `QuizListItem` (includes `agent_session_id` for deep-link)
- [X] T007 [P] Add `QuizResponse` dataclass to `backend/src/schemas/agent_responses.py` (fields: `response_type="quiz"`, `module_slug`, `topic_label`, `mcq_questions`, `flashcard_questions`, `quiz_session_id`) and add `QuizResponse` branch to the `TutorResponse` discriminated union
- [X] T008 Create quiz router skeleton in `backend/src/api/v1/quiz.py` (empty `APIRouter(prefix="/api/v1/quiz", tags=["quiz"])`) and include it in the main FastAPI app (modify `backend/src/api/v1/router.py` or `backend/src/main.py`)

**Checkpoint**: Foundation ready — model, repository, schemas, and router scaffold exist. User story implementation can now begin.

---

## Phase 3: User Story 1 — Student Takes a Quiz from Chat (Priority: P1) 🎯 MVP

**Goal**: A student types "give me a quiz", a `QuizCard` appears inline in the chat feed with 3 MCQ cards followed by 3 flashcard cards, and a score summary renders when all 6 are answered.

**Independent Test**: Trigger quiz via chat → `QuizCard` renders with 3 MCQ + 3 flashcard cards → MCQ options lock with correct/wrong highlights on tap (client-side) → flashcards render with term + answer input. Full end-to-end test (including grading) requires Phase 4 (US2) complete.

### Backend — Quiz Agent & Generation

- [X] T009 [P] [US1] Add `"quiz-generation"` intent patterns to `INTENT_PATTERNS` in `backend/src/services/agents/triage.py` (patterns: `r"\bgive me a quiz\b"`, `r"\bquiz\b"`, `r"\btest my knowledge\b"`, `r"\bflashcard(s)?\b"`, `r"\bquick quiz\b"`, `r"\bchallenge me\b"`) and map `"quiz-generation"` → `"quiz"` in `INTENT_TO_AGENT`; ensure it takes priority over `"exercise-generation"` in pattern matching order
- [X] T010 [P] [US1] Create `get_quiz_agent()` factory function in `backend/src/services/agents/agents.py` using the same `openai-agents` SDK pattern as other specialist agents; system prompt MUST list all 8 curriculum slugs (`basics`, `control_flow`, `data_structures`, `functions`, `oop`, `files`, `errors`, `libraries`) as constrained choices; `output_type=QuizResponse`
- [X] T011 [US1] Wire `"quiz"` agent key into `_agent_factory_map` in `backend/src/api/v1/agents.py` and extend the SSE stream handler to: (a) create a `quiz_sessions` row via `QuizSessionRepository.create()` when the structured `QuizResponse` arrives, (b) emit `event: structured` with the full `QuizResponse` payload including the new `quiz_session_id`

### Frontend — Quiz UI Components

- [X] T012 [P] [US1] Create typed fetch helpers in `frontend/src/lib/api/quiz.ts`: `getQuizSession(sessionId)`, `gradeFlashcard(sessionId, req)`, `submitQuiz(sessionId, req)`, `listQuizSessions()` — all using existing auth headers from the chat API pattern
- [X] T013 [P] [US1] Create `useQuizSession` hook in `frontend/src/hooks/useQuizSession.ts` managing quiz state machine (`generated` → `in_progress` → `completed`), local `studentAnswers` map, `grades` map, current card index, and expose `answerMCQ()`, `submitFlashcard()`, `submitAll()` actions
- [X] T014 [P] [US1] Create `MCQCard` component in `frontend/src/components/chat/quiz/MCQCard.tsx`: renders question text, 4 option buttons; on option tap locks selection, highlights correct option green and wrong option red (using `correct_index` from questions data), shows "Next" button
- [X] T015 [P] [US1] Create `FlashCard` component in `frontend/src/components/chat/quiz/FlashCard.tsx`: front shows term + answer `<textarea>`; "Check" button disabled until ≥1 char typed; on submit triggers CSS 3D flip (Tailwind `rotateY-180` + backface-hidden) revealing definition + grade badge placeholder (`Checking…` until API responds)
- [X] T016 [P] [US1] Create `QuizSummary` component in `frontend/src/components/chat/quiz/QuizSummary.tsx`: displays "You scored X/6", per-card result row (card index, type, grade, points), "Continue Learning" button that returns focus to chat input via callback
- [X] T017 [US1] Create `QuizCard` outer container in `frontend/src/components/chat/quiz/QuizCard.tsx`: state-machine orchestrator rendering `MCQCard` × 3 sequentially → `FlashCard` × 3 sequentially → `QuizSummary`; receives `QuizResponse` payload + `quizSessionId` as props; uses `useQuizSession` hook
- [X] T018 [US1] Add quiz branch to `ChatMessage.tsx` renderer in `frontend/src/components/chat/ChatMessage.tsx`: detect `message.content.response_type === "quiz"` and render `<QuizCard>` instead of the text/structured card renderers

**Checkpoint**: Student can trigger a quiz, see the `QuizCard` inline in chat, click through MCQ cards with immediate correct/wrong feedback. Flashcard input UI renders. Score summary renders after all cards.

---

## Phase 4: User Story 2 — Flashcard AI Grading (Priority: P2)

**Goal**: When a student types a flashcard answer and clicks "Check", the AI grades it as Correct / Partial / Wrong with a one-line feedback, displayed on the flipped card.

**Independent Test**: `POST /api/v1/quiz/{session_id}/grade-flashcard` with a known answer → returns accurate `grade` + `feedback` within 5 s.

### Backend — Grade Endpoint

- [X] T019 [US2] Implement `POST /api/v1/quiz/{session_id}/grade-flashcard` in `backend/src/api/v1/quiz.py`: (a) validate ownership (`quiz_sessions.student_id == current_user.id`, else 403); (b) validate `card_index` is 3–5 and card type is `flashcard`; (c) call `LlmClient` with a structured grading prompt comparing `student_answer` to `questions[card_index].definition`; (d) persist answer + grade via `QuizSessionRepository.update_answers_and_grades()`; (e) transition status `generated → in_progress` on first call; (f) return `GradeFlashcardResponse` (grade enum: Correct/Partial/Wrong + feedback string + session_status)

### Frontend — Grade Display

- [X] T020 [P] [US2] Update `FlashCard.tsx` in `frontend/src/components/chat/quiz/FlashCard.tsx` to call `useQuizSession.submitFlashcard()` on "Check" → await `gradeFlashcard()` API → display grade badge (green=Correct, yellow=Partial, red=Wrong) + feedback text inside the flipped card face; show "Could not grade — try again" retry on API failure without clearing the typed answer
- [X] T021 [P] [US2] Update `useQuizSession.ts` in `frontend/src/hooks/useQuizSession.ts` to store per-card `grades` from `GradeFlashcardResponse` and expose loading state per card index so `FlashCard` can show a spinner during the grading call

**Checkpoint**: Flashcard answers are AI-graded, grade + feedback appear on card flip, errors are recoverable.

---

## Phase 5: User Story 3 — Mastery Score Updated After Quiz (Priority: P3)

**Goal**: After completing all 6 cards, the submit endpoint finalises the score, updates the student's `mastery_records` for the module, and triggers struggle detection if score < 50.

**Independent Test**: Complete a quiz → `POST /submit` returns `mastery_updated: true` and the student's `mastery_records` row for `module_slug` shows an updated `component_breakdown.quizzes` value.

### Backend — Submit Endpoint & Mastery

- [X] T022 [US3] Implement `POST /api/v1/quiz/{session_id}/submit` in `backend/src/api/v1/quiz.py`: (a) validate ownership (403 on mismatch); (b) reject if `status == "completed"` (400); (c) validate all 3 MCQ answers present in `mcq_answers`; (d) compute raw score (MCQ=1/0, Flashcard=1/0.5/0 from stored grades); (e) map raw/6 → 0–100; (f) persist MCQ grades + final score, set `status = "completed"`, `completed_at = now()` via `QuizSessionRepository.mark_completed()`; (g) return `SubmitQuizResponse` with `per_card_results`, `score`, `score_out_of_6`, `module_slug`, `struggle_flagged`
- [X] T023 [US3] Integrate mastery update in the submit handler in `backend/src/api/v1/quiz.py`: call `MasteryRepository.update_mastery()` for `(student_id, module_slug)` — update `component_breakdown["quizzes"]` to the new quiz score (0–100), recompute total using formula `exercises×0.4 + quizzes×0.3 + code_quality×0.2 + streak×0.1`; use most-recent-quiz strategy (overwrite, not average); set `mastery_updated = True` in response
- [X] T024 [US3] Add struggle detection in the submit handler in `backend/src/api/v1/quiz.py`: if `score < 50`, trigger the existing struggle-detection mechanism (flag `struggle_flagged = True` in response and call existing alert/logging path)

### Frontend — Submit Flow & Score Display

- [X] T025 [US3] Wire auto-submit in `QuizCard.tsx` (`frontend/src/components/chat/quiz/QuizCard.tsx`): after the 6th card is answered, call `useQuizSession.submitAll()` which calls `submitQuiz()` with the 3 MCQ answers; pass `SubmitQuizResponse` to `QuizSummary`
- [X] T026 [US3] Update `QuizSummary.tsx` (`frontend/src/components/chat/quiz/QuizSummary.tsx`) to accept and display the `SubmitQuizResponse`: show `score_out_of_6` as "X/6", render `per_card_results` rows with correct point values, show mastery update confirmation if `mastery_updated === true`

**Checkpoint**: Quiz completion updates mastery, flags struggle when appropriate, and QuizSummary shows the server-computed score breakdown.

---

## Phase 6: User Story 4 — Quiz History Persisted (Priority: P4)

**Goal**: Completed quiz sessions are retrievable via API and shown on a `/quizzes` history page; in-progress quizzes are resumable from their originating chat session.

**Independent Test**: Complete a quiz → `GET /api/v1/quiz` returns a list entry with the quiz's `quiz_session_id`, `agent_session_id`, `module_slug`, `score`, `created_at`. Navigate to `/quizzes` → history card renders with module name, score, date and links back to the originating chat.

### Backend — State & List Endpoints

- [X] T027 [P] [US4] Implement `GET /api/v1/quiz/{session_id}` in `backend/src/api/v1/quiz.py`: validate ownership (403); call `QuizSessionRepository.get_by_id()`; return full `QuizSessionState` (questions, student_answers, grades, status, score, completed_at, etc.) per the `quiz-session.yaml` contract
- [X] T028 [P] [US4] Implement `GET /api/v1/quiz` in `backend/src/api/v1/quiz.py`: return `list[QuizListItem]` for the authenticated student ordered by `created_at DESC`; each `QuizListItem` includes `quiz_session_id`, `agent_session_id`, `module_slug`, `topic_label`, `score`, `status`, `created_at`

### Frontend — History Page & Resume

- [X] T029 [P] [US4] Create `QuizHistoryList` server component in `frontend/src/components/quizzes/QuizHistoryList.tsx`: accepts `QuizListItem[]` prop; renders one card per attempt showing module name, score (X/6 formatted from 0–100), date; each card is a `<Link href="/chat?session={agent_session_id}">` for deep-link back to originating chat
- [X] T030 [P] [US4] Create `/quizzes` server component page in `frontend/src/app/quizzes/page.tsx`: fetch `GET /api/v1/quiz` server-side using the session cookie; pass result to `<QuizHistoryList>`; show empty state ("No quizzes yet — start a chat and request one!") if list is empty
- [X] T031 [US4] Update `useQuizSession.ts` (`frontend/src/hooks/useQuizSession.ts`) to support resume flow: on mount, if a `quizSessionId` prop is provided and the component is rendering into an existing chat session, call `getQuizSession()` and restore `studentAnswers`, `grades`, `currentCardIndex` from the returned state so already-answered cards render in their locked completed state

**Checkpoint**: Quiz history is browsable at `/quizzes`; incomplete quizzes resume seamlessly from the originating chat.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Error handling, edge cases, and end-to-end validation.

- [X] T032 [P] Add inline error state to `QuizCard.tsx` (`frontend/src/components/chat/quiz/QuizCard.tsx`) for failed quiz generation: if the SSE stream delivers an error event instead of a `structured` quiz event, render "Couldn't generate a quiz right now — try again" with a retry button that re-sends the original quiz message via the chat input
- [ ] T033 [P] Add off-topic guard integration to `ChatMessage.tsx` (`frontend/src/components/chat/ChatMessage.tsx`): if triage returns `response_type === "off_topic"` in response to a quiz request, the existing off-topic amber bubble renders (no special handling needed — verify this path works end-to-end with a non-Python topic quiz request)
- [ ] T034 Run the full quickstart.md smoke test: apply migration → trigger quiz via curl → grade a flashcard → submit → verify mastery update → navigate to `/quizzes` page

---

## Dependencies & Execution Order

### Phase Dependencies

```
Phase 1 (Setup)
  └─► Phase 2 (Foundational)  ← BLOCKS all user stories
        ├─► Phase 3 (US1 P1) — 🎯 MVP
        │     └─► Phase 4 (US2 P2)
        │           └─► Phase 5 (US3 P3)
        └─► Phase 6 (US4 P4)  ← can start after Foundational; independent of US1–US3
              └─► Phase 7 (Polish)
```

### User Story Dependencies

| Story | Depends On | Independent Test Possible |
|-------|-----------|--------------------------|
| **US1 (P1)** | Foundational (Phase 2) | ✅ After US2 (grading needed) |
| **US2 (P2)** | US1 backend (T011) for `quiz_session_id` | ✅ Independently testable via curl |
| **US3 (P3)** | US2 (flashcard grades must exist before submit) | ✅ Independently testable via curl |
| **US4 (P4)** | Foundational (Phase 2) only | ✅ Fully independent of US1–US3 |

### Within Each Phase

- Backend tasks before corresponding frontend tasks (API must exist before client calls it)
- Models before repositories before endpoints
- Repository before agent wiring (T011 calls repository)
- All `[P]`-marked tasks can execute in parallel

---

## Parallel Execution Examples

### Phase 2 (Foundational) Parallel Tasks

```
Parallel group A (after T003):
  T005 — QuizSessionRepository
  T006 — Quiz Pydantic schemas
  T007 — QuizResponse schema
  T008 — Quiz router skeleton (register in app)
```

### Phase 3 (US1) Parallel Tasks

```
Parallel group B (after T008):
  Backend: T009 (triage intent) + T010 (quiz agent factory)
    → T011 (wire into factory map + SSE handler) — sequential after T009 + T010

Parallel group C (after T011):
  Frontend: T012 (quiz.ts helpers)
           T013 (useQuizSession hook)
           T014 (MCQCard component)
           T015 (FlashCard component shell)
           T016 (QuizSummary component)
    → T017 (QuizCard outer container) — after T014 + T015 + T016
    → T018 (ChatMessage quiz branch) — after T017
```

### Phase 6 (US4) Parallel Tasks

```
Parallel group D (after Phase 2):
  Backend: T027 (GET state endpoint) + T028 (GET list endpoint)
  Frontend: T029 (QuizHistoryList) + T030 (/quizzes page)
    → T031 (resume flow in useQuizSession) — after T027
```

---

## Implementation Strategy

### MVP First (US1 + US2 — Minimum Playable Quiz)

1. Complete **Phase 1** (migration)
2. Complete **Phase 2** (data layer)
3. Complete **Phase 3** (quiz generation + full frontend UI)
4. Complete **Phase 4** (flashcard grading)
5. **STOP and VALIDATE**: Student can trigger quiz, answer all 6 cards with AI grading, see score summary (even if score not yet persisted to mastery)
6. Demo / deploy if ready

### Incremental Delivery

- **After Phase 4**: Fully playable quiz — generation, MCQ, flashcard grading ✅
- **After Phase 5**: Mastery integration — quiz score affects student's learning trajectory ✅
- **After Phase 6**: History + resume — students can review past quizzes and resume incomplete ones ✅
- **After Phase 7**: Production-grade error handling ✅

---

## Notes

- `[P]` tasks = different files, no shared state, safe to run in parallel
- `[Story]` maps each task to a user story for traceability and independent testing
- Quiz endpoints (`GET state`, `POST grade`, `POST submit`, `GET list`) are quota-exempt — do NOT wire them through `ChatQuotaService`
- All quiz endpoints MUST use `get_current_user` dependency (existing pattern) and enforce `quiz_sessions.student_id == current_user.id` (403 on mismatch)
- The `quiz_session_id` is created server-side when the `QuizResponse` structured event arrives in the SSE handler (T011); the frontend never generates this ID
- MCQ grading is entirely client-side; only the MCQ `is_correct` boolean is sent to `POST /submit` — the server does not re-verify MCQ correctness
- The `agent_session_id` stored in each `QuizListItem` enables the `/quizzes` page to deep-link back to the originating chat session without a standalone quiz replay UI
