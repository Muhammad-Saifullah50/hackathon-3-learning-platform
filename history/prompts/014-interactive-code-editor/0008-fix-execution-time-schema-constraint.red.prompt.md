---
id: "0008"
title: Fix execution_time_ms Schema Upper Bound
stage: red
date: 2026-05-10
surface: agent
model: claude-sonnet-4-6
feature: 014-interactive-code-editor
branch: 014-interactive-code-editor
user: Muhammad
command: chat
labels: ["debugging","pydantic","schema","code-execution","docker"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - backend/src/schemas/code_execution.py
tests:
  - null
---

## Prompt

[User pasted backend logs showing Docker image pull succeeded but endpoint returned 500:]
```
ValidationError: 1 validation error for CodeExecutionResponse
execution_time_ms
  Input should be less than or equal to 8000 [input_value=12744]
```

## Response snapshot

Root cause: `CodeExecutionResponse.execution_time_ms` had `le=8000` constraint. First run took 12744ms due to Docker pulling `python:3.11-alpine`. The Pydantic constraint rejects valid responses when Docker image pull overhead exceeds 8000ms. This constraint is incorrect on a response schema — the 5s sandbox timeout already bounds actual Python execution; total elapsed time including Docker overhead is a legitimate measurement.

Fix: removed `le=8000` from `execution_time_ms` field in `CodeExecutionResponse`, keeping `ge=0` intact.

## Outcome

- ✅ Impact: First-run Docker image pulls no longer cause 500s; all subsequent runs will be fast (image cached)
- 🧪 Tests: None added
- 📁 Files: backend/src/schemas/code_execution.py
- 🔁 Next prompts: Verify execution succeeds on retry
- 🧠 Reflection: Upper-bound constraints belong on user inputs, not on outgoing measurements — timing fields in response schemas should only have ge=0

## Evaluation notes (flywheel)

- Failure modes observed: le= constraint on response field rejecting valid cold-start timings
- Graders run and results (PASS/FAIL): manual trace
- Prompt variant (if applicable): null
- Next experiment: null
