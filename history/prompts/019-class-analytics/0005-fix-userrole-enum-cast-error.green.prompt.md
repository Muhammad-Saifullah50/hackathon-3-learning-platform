---
id: "0005"
title: Fix userrole enum cast error in analytics repository
stage: green
date: 2026-05-19
surface: agent
model: claude-sonnet-4-6
feature: 019-class-analytics
branch: master
user: Muhammad
command: debug
labels: ["bugfix","sqlalchemy","postgresql","enum","analytics"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - backend/src/repositories/analytics_repository.py
tests:
  - null
---

## Prompt

SQLAlchemy ProgrammingError on `get_total_students()`:
`operator does not exist: userrole = character varying`
`HINT: No operator matches the given name and argument types. You might need to add explicit type casts.`

The error occurs at `analytics_repository.py:23` when executing a COUNT query with `User.role == "student"`.

## Response snapshot

Root cause: `users.role` is a PostgreSQL `userrole` enum in the DB, but the SQLAlchemy model declares it as `String(20)`. When SQLAlchemy binds the literal `"student"` as a `character varying` parameter, PostgreSQL refuses the comparison without an explicit cast.

Fix: Added `cast(User.role, SAString)` in the WHERE clause of `get_total_students()`, generating `role::varchar = 'student'` SQL which PostgreSQL accepts.

Changed `analytics_repository.py`:
- Added `cast` and `SAString` imports from sqlalchemy
- Updated WHERE clause: `cast(User.role, SAString) == "student"`

## Outcome

- ✅ Impact: `GET /api/v1/dashboard/teacher` no longer raises ProgrammingError on total_students query
- 🧪 Tests: None added (runtime fix)
- 📁 Files: backend/src/repositories/analytics_repository.py
- 🔁 Next prompts: Consider aligning the SQLAlchemy model `User.role` type with the actual DB enum type to prevent future mismatches
- 🧠 Reflection: Model/DB type mismatch is a silent failure that only surfaces at query time. The `cast()` fix is minimal and non-breaking.

## Evaluation notes (flywheel)

- Failure modes observed: SQLAlchemy String(20) model type does not match PostgreSQL userrole enum — comparison fails without explicit cast
- Graders run and results (PASS/FAIL): N/A
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): Update User.role to use SQLAlchemy Enum type matching the DB schema to remove the need for the cast
