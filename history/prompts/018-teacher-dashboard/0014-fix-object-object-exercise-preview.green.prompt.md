---
id: "0014"
title: Fix [object Object] in Exercise Preview
stage: green
date: 2026-05-19
surface: agent
model: claude-sonnet-4-6
feature: 018-teacher-dashboard
branch: 018-teacher-dashboard
user: Muhammad
command: chat
labels: ["bugfix", "teacher-dashboard", "exercise-generation", "guardrail"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - frontend/src/lib/api/teacher.ts
  - frontend/src/hooks/useExerciseGeneration.ts
tests:
  - manual: generate exercise with invalid prompt (guardrail fires) → confirm proper message shown
  - manual: generate exercise with valid prompt → confirm preview renders correctly
---

## Prompt

when a teacher generates an exercise i see [object obnject] in place of the preview of the generated exercise. correct ths erorr

## Response snapshot

Root cause traced: when the guardrail rejects a prompt (or generation fails), the backend raises `HTTPException(400, detail=result)` where `detail` is a dict. In `apiFetch`, `new Error(body.detail)` is called with an object, causing `.toString()` → `"[object Object]"`. The hook stores this via `setError(e.message)` and it renders in the exercise preview area.

Two-file fix:
1. `apiFetch` in `teacher.ts`: extract a human-readable string from non-string `detail` objects (checks `.message` then `.detail` keys)
2. `useExerciseGeneration.ts` catch block: detect guardrail rejections via `body.detail.code` and route them to `setGuardrailError` (renders the styled rejection UI) instead of the generic `error` state

## Outcome

- ✅ Impact: [object Object] no longer appears; guardrail rejections show the proper styled error UI in the form; generation failures show a real error message
- 🧪 Tests: manual testing of invalid and valid prompts
- 📁 Files: 2 files modified
- 🔁 Next prompts: none identified
- 🧠 Reflection: The HTTPException detail being a dict (not a string) was the source; the type annotation `{ detail?: string }` in apiFetch masked the mismatch at compile time

## Evaluation notes (flywheel)

- Failure modes observed: passing object to Error() constructor produces [object Object] message; HTTPException detail can be any JSON-serializable type
- Graders run and results (PASS/FAIL): manual
- Prompt variant (if applicable): null
- Next experiment (smallest change to try): add a shared `parseErrorDetail` utility in `api/index.ts` to avoid repeating the logic across API files
