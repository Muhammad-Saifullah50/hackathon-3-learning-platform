---
id: "0013"
title: Fix Exercise Generation Check Constraint Violation
stage: green
date: 2026-05-19
surface: agent
model: claude-sonnet-4-6
feature: 018-teacher-dashboard
branch: 018-teacher-dashboard
user: Muhammad
command: /sp.phr
labels: ["teacher-exercise","llm-output-validation","check-constraint","pydantic","error-handling"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - backend/src/services/teacher_exercise_service.py
tests:
  - none
---

## Prompt

got this erorr INFO:     127.0.0.1:37162 - "POST /api/v1/teacher/exercises/generate HTTP/1.1" 500 Internal Server Error
...
asyncpg.exceptions.CheckViolationError: new row for relation "teacher_generated_exercises" violates check constraint "ck_teacher_exercise_difficulty"
DETAIL:  Failing row contains (79815737-2ea4-4959-9845-5363854b78a5, : , : , : , : , create a beginner level exercise set on fastapi with starter cod..., [], ...)

## Response snapshot

Root cause: the LLM returned malformed output with all string fields set to ": " and an empty questions list. Fixed by adding Literal types to difficulty/target_module, field_validator guards for empty title/topic and empty questions, wrapping Runner.run in try-except, adding service-level sanity check before DB insert, and strengthening the agent prompt.

## Outcome

- ✅ Impact: 500 IntegrityError eliminated; bad LLM output now returns a clean 400 with a user-facing message
- 🧪 Tests: none
- 📁 Files: backend/src/services/teacher_exercise_service.py
- 🔁 Next prompts: Add retry logic — if generation fails validation, retry once with a stricter prompt
- 🧠 Reflection: Pydantic Literal types on structured output schemas are essential with openai-agents+LiteLLM to catch model hallucinations before they reach the DB

## Evaluation notes (flywheel)

- Failure modes observed: LLM returned YAML-like template output; Pydantic parsed ": " as the field value for all string fields
- Graders run and results (PASS/FAIL): n/a
- Prompt variant (if applicable): n/a
- Next experiment (smallest change to try): Add one retry on validation failure with explicit "previous attempt returned empty fields" message
