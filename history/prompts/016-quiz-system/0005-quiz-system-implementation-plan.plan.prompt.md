---
id: "0005"
title: "Quiz System Implementation Plan"
stage: plan
date: 2026-05-17
surface: agent
model: claude-sonnet-4-6
feature: 016-quiz-system
branch: 016-quiz-system
user: Muhammad
command: /sp.plan
labels: ["quiz", "plan", "agent-layer", "frontend", "data-model", "mastery"]
links:
  spec: specs/016-quiz-system/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/016-quiz-system/plan.md
  - specs/016-quiz-system/research.md
  - specs/016-quiz-system/data-model.md
  - specs/016-quiz-system/quickstart.md
  - specs/016-quiz-system/contracts/quiz-session.yaml
  - specs/016-quiz-system/contracts/grade-flashcard.yaml
  - specs/016-quiz-system/contracts/submit-quiz.yaml
tests:
  - null
---

## Prompt

/sp.plan

## Response snapshot

Ran `/sp.plan` for the Quiz System (F16). Executed the full planning workflow:

**Phase 0 — Research**: Analysed the existing codebase (agent layer, triage, mastery repo, agent_exercise model, chat SSE endpoint, ChatMessage renderer). Resolved 7 research questions covering quiz intent detection, QuizResponse schema design, flashcard grading approach (direct LlmClient call not SDK), JSONB session storage, mastery update strategy (most-recent score), frontend state machine, and CSS card flip animation.

**Phase 1 — Design**: Generated:
- `plan.md` — Technical Context, Constitution Check (all 12 gates pass), Architecture Overview with data flow diagrams and design decision table
- `research.md` — 7 research decisions with rationale and rejected alternatives
- `data-model.md` — Full `quiz_sessions` table schema (JSONB `questions`/`student_answers`/`grades`), Alembic migration skeleton, SQLAlchemy model, state machine diagram, scoring formula
- `contracts/quiz-session.yaml` — `GET /api/v1/quiz/{session_id}` OpenAPI spec
- `contracts/grade-flashcard.yaml` — `POST /api/v1/quiz/{session_id}/grade-flashcard` OpenAPI spec
- `contracts/submit-quiz.yaml` — `POST /api/v1/quiz/{session_id}/submit` OpenAPI spec
- `quickstart.md` — Step-by-step manual test guide (migration → curl tests → frontend smoke test)

**Agent context updated** via `update-agent-context.sh claude`.

Key architectural decisions:
- Quiz generation via existing `POST /api/v1/agents/chat` triage route (new `quiz-generation` intent, new `quiz` agent, `QuizResponse` added to `TutorResponse` union)
- 3 dedicated quiz endpoints outside chat quota for post-generation interactions
- Flashcard grading uses direct `LlmClient` call (not SDK Agent) for < 5 s P95
- Single `quiz_sessions` row with JSONB columns (no normalized question tables)
- Mastery update: most-recent quiz score per module, full formula recompute on submit
- Frontend: `useQuizSession` hook + `QuizCard`/`MCQCard`/`FlashCard`/`QuizSummary` components + CSS 3D flip

## Outcome

- ✅ Impact: Complete implementation plan ready for /sp.tasks; all design unknowns resolved
- 🧪 Tests: No tests written in this phase; test strategy defined in plan.md
- 📁 Files: 7 planning artifacts created under specs/016-quiz-system/
- 🔁 Next prompts: /sp.tasks to generate actionable implementation tasks
- 🧠 Reflection: All 7 research questions resolved from codebase analysis alone — no external research needed; existing patterns (agent output_type, repository pattern, JSONB storage) directly applicable

## Evaluation notes (flywheel)

- Failure modes observed: none
- Graders run and results (PASS/FAIL): n/a (planning phase)
- Prompt variant (if applicable): null
- Next experiment (smallest change to try): Consider adding a `quiz-session-id` field directly to the AgentSession message model rather than embedding in the message content JSON, for cleaner resume-state lookup
