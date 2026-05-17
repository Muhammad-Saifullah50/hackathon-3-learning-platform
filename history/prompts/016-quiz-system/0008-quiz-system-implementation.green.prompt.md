---
id: "0008"
title: Quiz System Implementation (F16)
stage: green
date: 2026-05-17
surface: agent
model: claude-sonnet-4-6
feature: 016-quiz-system
branch: 016-quiz-system
user: Muhammad
command: /sp.implement
labels: ["quiz", "implementation", "backend", "frontend", "migration", "agents"]
links:
  spec: specs/016-quiz-system/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - backend/alembic/versions/20260517_create_quiz_sessions_table.py
  - backend/src/models/quiz_session.py
  - backend/src/models/__init__.py
  - backend/src/repositories/quiz_session_repository.py
  - backend/src/schemas/quiz.py
  - backend/src/schemas/agent_responses.py
  - backend/src/api/v1/quiz.py
  - backend/src/api/v1/agents.py
  - backend/src/main.py
  - backend/src/services/agents/triage.py
  - backend/src/services/agents/agents.py
  - frontend/src/lib/api/quiz.ts
  - frontend/src/hooks/useQuizSession.ts
  - frontend/src/components/chat/quiz/MCQCard.tsx
  - frontend/src/components/chat/quiz/FlashCard.tsx
  - frontend/src/components/chat/quiz/QuizSummary.tsx
  - frontend/src/components/chat/quiz/QuizCard.tsx
  - frontend/src/components/chat/ChatMessage.tsx
  - frontend/src/components/quizzes/QuizHistoryList.tsx
  - frontend/src/app/quizzes/page.tsx
tests:
  - n/a (not requested in spec)
---

## Prompt

/sp.implement

## Response snapshot

Full implementation of the Quiz System (F16) across all phases:

**Phase 1 (Setup):** Alembic migration `20260517_create_quiz_sessions_table.py` created and applied to Neon PostgreSQL. `quiz_sessions` table live with all columns, constraints (status, score, module_slug CHECK), and 5 indexes.

**Phase 2 (Foundational):** `QuizSession` SQLAlchemy model, `QuizSessionRepository` (create/get_by_id/update_answers_and_grades/mark_completed/list_by_student), quiz Pydantic schemas (`QuizSessionState`, `GradeFlashcardRequest/Response`, `SubmitQuizRequest/Response`, `QuizListItem`), `QuizResponse` added to `agent_responses.py` with `MCQQuestion`/`FlashcardQuestion` sub-models and updated `TutorResponse` union, quiz router registered in `main.py`.

**Phase 3 Backend (US1):** `quiz-generation` intent patterns added to `triage.py` (priority over exercise-generation in dict order), `get_quiz_agent()` factory with constrained 8-slug prompt, quiz agent wired into `_agent_factory_map`, SSE handler extended to create `quiz_sessions` row and embed `quiz_session_id` in `QuizResponse` before emitting.

**Phase 4+5+6 Backend:** All endpoints implemented in `quiz.py`: `GET /api/v1/quiz` (list), `GET /api/v1/quiz/{id}` (state), `POST /{id}/grade-flashcard` (LLM grading via LlmClient), `POST /{id}/submit` (score computation, mastery update, struggle detection at score < 50).

**Phase 3 Frontend:** `quiz.ts` fetch helpers, `useQuizSession` hook (state machine + resume from server), `MCQCard` (option locking, correct/wrong highlights), `FlashCard` (CSS 3D flip, grade badge), `QuizSummary` (X/6 score, per-card breakdown, mastery badge), `QuizCard` orchestrator (progress dots, auto-submit after all 6 cards). `ChatMessage.tsx` updated to branch on `response_type === "quiz"` and render `QuizCard` outside the inner card wrapper.

**Phase 6 Frontend:** `QuizHistoryList` server component with deep-links to originating chat, `/quizzes` page (server-fetched, empty state).

All 31 implemented tasks marked [X] in tasks.md. Backend imports verified OK, TypeScript type-check exit 0.

## Outcome

- ✅ Impact: Full quiz system live — quiz generation via chat, MCQ + flashcard interaction, AI grading, mastery update, history page with deep-links
- 🧪 Tests: Not required per spec; backend imports and TS type-check pass; intent classification unit-tested inline
- 📁 Files: 20 files created/modified across backend and frontend
- 🔁 Next prompts: Run quickstart smoke test (T034); verify off-topic guard end-to-end (T033); add useChatSessions sidebar (T022); complete /chat page (T023)
- 🧠 Reflection: JSONB server_default requires `sa.text("'{}'")`; routing_decisions CHECK constraint safe because quiz is selected directly, not via triage handoffs; QuizCard rendered outside inner card wrapper to avoid double-border

## Evaluation notes (flywheel)

- Failure modes observed: JSONB default escaping bug (triple-quote) caught and fixed during migration; resolved by using `sa.text()`
- Graders run and results (PASS/FAIL): Backend import check PASS; TypeScript type-check PASS; intent classification PASS
- Prompt variant (if applicable): n/a
- Next experiment (smallest change to try): Run end-to-end quickstart smoke test with live backend
