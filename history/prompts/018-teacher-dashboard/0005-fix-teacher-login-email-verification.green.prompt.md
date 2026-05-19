---
id: "0005"
title: Fix Teacher Login Email Verification Block
stage: green
date: 2026-05-19
surface: agent
model: claude-sonnet-4-6
feature: 018-teacher-dashboard
branch: 018-teacher-dashboard
user: Muhammad
command: user message
labels: ["bugfix", "auth", "teacher", "403"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - backend/src/auth/service.py
tests:
  - manual: teacher login no longer returns 403 after registration
---

## Prompt

i cant see any sort of charts on the teacher dashboard for teacher analytics. didnt i ?
i got npt authenticated error when trying to create a class
INFO:     127.0.0.1:54634 - "POST /api/auth/login HTTP/1.1" 403 Forbidden
INFO:     127.0.0.1:53542 - "GET /api/v1/teacher/classes HTTP/1.1" 403 Forbidden
...
bypass like it is for students

## Response snapshot

Identified root cause: `backend/src/auth/service.py` had an email verification gate for `role in ["teacher", "admin"]` before issuing JWT. Teachers without verified emails received 403 on login, which meant no FastAPI token was ever attached to the Better Auth session, causing all subsequent teacher API calls to also return 403.

Fix: changed the check to only apply to `role == "admin"`, matching student behaviour.

## Outcome

- ✅ Impact: Teachers can now log in and access `/api/v1/teacher/*` endpoints without email verification, same as students.
- 🧪 Tests: Manual — register as teacher, log in, POST /api/v1/teacher/classes should return 201.
- 📁 Files: backend/src/auth/service.py (1 line changed)
- 🔁 Next prompts: Restart backend and retest class creation flow.
- 🧠 Reflection: The login 403 masked the real auth issue — the fastApiToken was never stored in the Better Auth session, so every downstream API call failed with 403 too.

## Evaluation notes (flywheel)

- Failure modes observed: Email verification gate on teachers blocked login entirely; cascading 403s on all teacher API routes.
- Graders run and results (PASS/FAIL): none automated
- Prompt variant (if applicable): null
- Next experiment: Add an integration test that registers a teacher without email verification and asserts login succeeds.
