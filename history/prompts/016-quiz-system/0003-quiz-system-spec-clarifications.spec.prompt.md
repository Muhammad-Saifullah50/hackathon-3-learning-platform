---
id: "0003"
title: Quiz System Spec Clarifications
stage: spec
date: 2026-05-17
surface: agent
model: claude-sonnet-4-6
feature: 016-quiz-system
branch: 016-quiz-system
user: Muhammad
command: /sp.clarify
labels: [clarification, quiz-system, api-design, data-model, security, error-handling]
links:
  spec: specs/016-quiz-system/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/016-quiz-system/spec.md
tests:
  - null
---

## Prompt

/sp.clarify (no additional user input — interactive clarification session for feature 016-quiz-system)

## Response snapshot

Ran structured ambiguity scan across all taxonomy categories on the 016-quiz-system spec. Found 5 unresolved areas and conducted a 5-question interactive clarification session. All 5 questions answered and encoded into the spec.

Q1: API pattern for quiz actions → Dedicated quiz endpoints (`/api/v1/quiz/...`) for grading/submission; generation via existing chat triage route.

Q2: Quiz generation failure handling → Inline error in chat feed with a retry button ("Couldn't generate a quiz right now — try again").

Q3: DB storage format for questions/answers/grades → JSONB columns on a single `quiz_sessions` row (`questions`, `student_answers`, `grades`).

Q4: Quiz session lifecycle states → Three states: `generated` → `in_progress` → `completed`, stored as `status` VARCHAR.

Q5: Cross-student authorization rule → Ownership check on every quiz endpoint; `student_id` must match JWT `user_id`; HTTP 403 on mismatch.

Added FR-014 and FR-015 to Functional Requirements. Updated Key Entities with full schema detail. Added generation failure edge case. Updated Clarifications section.

## Outcome

- ✅ Impact: 5 high-impact ambiguities resolved — API contract, DB schema, state machine, error paths, and AuthZ all now specified
- 🧪 Tests: No tests run (spec-only change)
- 📁 Files: specs/016-quiz-system/spec.md
- 🔁 Next prompts: /sp.plan
- 🧠 Reflection: All major architectural decision points for the quiz system are now resolved; spec is ready for planning

## Evaluation notes (flywheel)

- Failure modes observed: none
- Graders run and results (PASS/FAIL): n/a
- Prompt variant (if applicable): n/a
- Next experiment (smallest change to try): n/a
