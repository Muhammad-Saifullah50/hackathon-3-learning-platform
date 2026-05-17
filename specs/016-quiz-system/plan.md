# Implementation Plan: Quiz System

**Branch**: `016-quiz-system` | **Date**: 2026-05-17 | **Spec**: `specs/016-quiz-system/spec.md`
**Input**: Feature specification from `/specs/016-quiz-system/spec.md`

---

## Summary

The Quiz System (F16) adds an inline, AI-generated 6-card quiz (3 MCQ + 3 flashcard) to the AI Tutor Chat feed. Quiz generation is triggered via the existing triage route and returns a new `quiz` structured-output type. Post-generation interactions (flashcard AI grading, session submission, state retrieval for resume) run through three dedicated quiz endpoints that bypass the 15 msg/day chat quota. A new `QuizAgent` follows the same OpenAI Agents SDK pattern as all other specialist agents. Quiz completion updates the student's mastery record (30% quiz weight) and persists the full session to a new `quiz_sessions` table.

---

## Technical Context

**Language/Version**: Python 3.13 (backend) · TypeScript 5+ / React 19 (frontend)
**Primary Dependencies**: FastAPI, openai-agents ≥0.13, SQLAlchemy 2.0+, Pydantic 2.0+, Alembic 1.13+, Next.js 14+, Tailwind CSS, LiteLLM via existing `LlmClient`
**Storage**: Neon PostgreSQL — new `quiz_sessions` table (JSONB `questions`, `student_answers`, `grades`); existing `mastery_records` table updated on submit
**Testing**: pytest + httpx (backend); vitest + @testing-library/react (frontend)
**Target Platform**: Linux server (FastAPI on Railway) · Vercel (Next.js frontend)
**Project Type**: Web application (backend + frontend — Option 2)
**Performance Goals**: Flashcard AI grading < 5 s P95; mastery update within 10 s of submission; quiz generation first token < 1.2 s (SSE, existing budget)
**Constraints**: Quiz endpoints excluded from 15 msg/day chat quota; JWT ownership enforcement (403 on mismatch); quiz interaction is inline in chat feed; quiz history page navigates back to the originating chat session (no standalone quiz replay UI)

---

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-checked after Phase 1 design.*

| Gate | Status | Note |
|------|--------|------|
| Code formatting automated (black/isort + prettier/eslint) | ✅ PASS | Existing tooling applies unchanged |
| All FastAPI routes require `get_current_user` | ✅ PASS | New quiz router inherits same dependency pattern |
| Repository pattern for all DB access | ✅ PASS | New `QuizSessionRepository` follows existing repo pattern |
| LLM calls streamed or async (no sync blocking) | ✅ PASS | Flashcard grading uses async `LlmClient`; generation is SSE |
| No `exec()` / `eval()` on server | ✅ PASS | Quiz does not execute code |
| Alembic migration for all schema changes | ✅ PASS | New migration for `quiz_sessions` table |
| Mastery formula unchanged (quizzes = 30%) | ✅ PASS | Spec explicitly preserves the existing formula |
| Struggle detection: quiz score < 50% triggers alert | ✅ PASS | Handled in submit endpoint post-mastery update |
| Agent output_type discriminated-union pattern | ✅ PASS | `QuizResponse` added to `TutorResponse` union |
| DB indexes on user_id, created_at | ✅ PASS | Specified in data-model |
| Tests: 80% route coverage, 85% repo coverage | ✅ PASS | Tracked in tasks |
| No hardcoded secrets | ✅ PASS | All LLM keys via `settings` / env |

**Result**: All gates PASS. No complexity violations.

---

## Project Structure

### Documentation (this feature)

```text
specs/016-quiz-system/
├── plan.md              # This file (/sp.plan command output)
├── research.md          # Phase 0 output (/sp.plan command)
├── data-model.md        # Phase 1 output (/sp.plan command)
├── quickstart.md        # Phase 1 output (/sp.plan command)
├── contracts/           # Phase 1 output (/sp.plan command)
│   ├── quiz-session.yaml
│   ├── grade-flashcard.yaml
│   └── submit-quiz.yaml
└── tasks.md             # Phase 2 output (/sp.tasks command - NOT created by /sp.plan)
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── models/
│   │   └── quiz_session.py            # NEW: QuizSession SQLAlchemy model
│   ├── repositories/
│   │   └── quiz_session_repository.py # NEW: CRUD for quiz_sessions
│   ├── schemas/
│   │   ├── agent_responses.py         # MODIFY: add QuizResponse, update TutorResponse union
│   │   └── quiz.py                    # NEW: request/response schemas for quiz endpoints
│   ├── services/
│   │   └── agents/
│   │       ├── agents.py              # MODIFY: add get_quiz_agent()
│   │       └── triage.py              # MODIFY: add quiz-generation intent patterns
│   └── api/
│       └── v1/
│           ├── agents.py              # MODIFY: wire quiz agent into _agent_factory_map
│           └── quiz.py                # NEW: quiz router (GET state, POST grade, POST submit)
├── alembic/
│   └── versions/
│       └── 20260517_create_quiz_sessions_table.py  # NEW: migration
└── tests/
    ├── unit/
    │   └── test_quiz_triage.py        # NEW
    ├── integration/
    │   ├── test_quiz_endpoints.py     # NEW
    │   └── test_quiz_mastery.py       # NEW
    └── contract/
        └── test_quiz_agent_output.py  # NEW: shape test for QuizResponse

frontend/
├── src/
│   ├── app/
│   │   └── quizzes/
│   │       └── page.tsx               # NEW: server component — fetches completed quiz_sessions server-side, passes list to QuizHistoryList
│   ├── components/
│   │   ├── chat/
│   │   │   ├── quiz/
│   │   │   │   ├── QuizCard.tsx       # NEW: outer state-machine container
│   │   │   │   ├── MCQCard.tsx        # NEW: single MCQ question UI
│   │   │   │   ├── FlashCard.tsx      # NEW: single flashcard with flip animation
│   │   │   │   └── QuizSummary.tsx    # NEW: final score + per-card breakdown
│   │   │   └── ChatMessage.tsx        # MODIFY: add quiz branch to renderer
│   │   └── quizzes/
│   │       └── QuizHistoryList.tsx    # NEW: server component — renders past-attempt cards (score, module, date); each card links to /chat?session={agent_session_id}
│   ├── hooks/
│   │   └── useQuizSession.ts          # NEW: quiz state + API calls hook
│   └── lib/
│       └── api/
│           └── quiz.ts                # NEW: typed fetch helpers for quiz endpoints
└── tests/
    └── components/
        └── quiz/
            ├── QuizCard.test.tsx      # NEW
            ├── MCQCard.test.tsx       # NEW
            └── QuizHistoryList.test.tsx # NEW
```

**Structure Decision**: Web application layout (backend + frontend). All new quiz files follow existing naming and directory conventions; no new top-level directories created.

---

## Architecture Overview

### Data Flow

```
Student types "give me a quiz"
  │
  ▼
POST /api/v1/agents/chat  (existing triage route)
  │  triage classifies → "quiz-generation" intent
  │  selects get_quiz_agent()
  │  Runner.run_streamed → emits event: structured (QuizResponse)
  │  quiz_sessions row created with status=generated
  ▼
Frontend receives event: structured {response_type: "quiz", session_id: ..., questions: [...]}
  │  ChatMessage renderer branches on response_type === "quiz"
  │  renders QuizCard (MCQ × 3, then Flashcard × 3)
  ▼
Student answers MCQ (client-side grading, no network call)
  │  card locked, correct=green / wrong=red
  ▼
Student types flashcard answer → clicks "Check"
  │
  ▼
POST /api/v1/quiz/{session_id}/grade-flashcard
  │  LlmClient grading call → returns grade + feedback
  │  stores answer + grade in quiz_sessions.student_answers / .grades
  ▼
All 6 cards answered → "Submit" auto-triggered
  │
  ▼
POST /api/v1/quiz/{session_id}/submit
  │  computes score (MCQ=1/0, Flashcard=1/0.5/0) → maps to 0-100
  │  updates quiz_sessions.status=completed, .score
  │  updates mastery_records (quizzes component, most-recent strategy)
  │  checks struggle (score < 50%)
  ▼
Frontend renders QuizSummary (X/6, per-card breakdown, "Continue Learning")
```

### Quiz History Page Flow

```
Student navigates to /quizzes
  │
  ▼
page.tsx (server component) fetches GET /api/v1/quiz (student's completed quiz_sessions)
  │  returns list: [{quiz_session_id, agent_session_id, module_slug, score, created_at}, ...]
  ▼
QuizHistoryList.tsx (server component) renders one card per attempt
  │  each card shows: module name, score (X/6), date
  │  card is a link → /chat?session={agent_session_id}
  ▼
Student clicks a card → navigated to /chat page
  │  chat page loads agent_session_id from query param
  │  existing session messages rendered (including inline QuizCard in completed state)
```

**Backend requirement**: `GET /api/v1/quiz` (list endpoint) — returns all `quiz_sessions` for the authenticated student, ordered by `created_at DESC`. Each row must include `agent_session_id` so the frontend can link back to the originating chat session.

### Resume Flow

```
Student returns to chat with in-progress quiz
  │
  ▼
GET /api/v1/agents/sessions/{session_id}  (existing endpoint)
  │  returns conversation_history; message with response_type="quiz" contains quiz_session_id
  ▼
Frontend reads quiz_session_id from message content
  │
  ▼
GET /api/v1/quiz/{session_id}
  │  returns full current state (questions, student_answers, grades, status)
  ▼
QuizCard re-renders with already-answered cards locked in completed state
Student resumes from first unanswered card
```

### Key Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Quiz generation trigger | Existing `POST /api/v1/agents/chat` SSE route | Preserves quota, triage, session creation without new SSE endpoint |
| Post-generation quiz API | Separate `/api/v1/quiz/*` router | Keeps quota exclusion clean; semantically distinct from chat flow |
| Flashcard grading | Async `LlmClient` call (not SDK Agent) | Lightweight, no handoff overhead; single structured call < 5s |
| Question storage | JSONB on `quiz_sessions` row | Avoids normalized question/answer tables; simpler for this scale |
| Mastery update strategy | Most-recent completed quiz score per module | Spec mandates this; avoids average/max complexity |
| Module slug selection | Constrained in quiz agent system prompt | Agent selects from 8 slugs at generation time; no post-hoc mapping |
| MCQ grading | Client-side only | Answers sent at generation time; no server round-trip needed |
| Card flip animation | CSS 3D transform + Tailwind | No extra library; consistent with existing Tailwind-first UI |
| Quiz history page | Server component at `/quizzes`; links back to originating chat session | No replay UI needed — existing chat session already holds the completed QuizCard in locked state |
| Quiz list endpoint | `GET /api/v1/quiz` returns `agent_session_id` per row | Enables deep-link from quiz history card directly into the correct chat session |

---

## Complexity Tracking

> No constitution violations detected. No entry required.
