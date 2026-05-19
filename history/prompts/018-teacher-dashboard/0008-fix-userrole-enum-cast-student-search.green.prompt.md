---
id: "0008"
title: Fix userrole enum cast in student search
stage: green
date: 2026-05-19
surface: agent
model: claude-sonnet-4-6
feature: 018-teacher-dashboard
branch: 018-teacher-dashboard
user: Muhammad
command: debug
labels: ["bug", "sqlalchemy", "postgresql", "enum", "student-search"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - backend/src/services/class_service.py
  - backend/src/repositories/user_repository.py
  - backend/src/services/user_profile_service.py
  - frontend/src/hooks/useTeacherClasses.ts
  - frontend/src/components/teacher/StudentSearchModal.tsx
tests:
  - null
---

## Prompt

the ass studets to clss feature is not working. the application is unable to search studens with their name or email. t says no students found. correct this issue

## Response snapshot

Root cause: the `users.role` column in Neon PostgreSQL is a custom enum type (`userrole`), not `VARCHAR`. asyncpg's prepared-statement engine raises `operator does not exist: userrole = character varying` when SQLAlchemy tries `WHERE users.role = $1::VARCHAR`.

Fix: wrap all `User.role ==` comparisons used via the async session with `cast(User.role, String)` so PostgreSQL casts the enum to text before comparing.

Three files patched:
- `class_service.search_students` — the immediate crash site
- `user_repository.get_by_role` — same pattern
- `user_profile_service` admin list — same pattern

Frontend: added `error` state to `useStudentSearch` and surfaced it in `StudentSearchModal` so future backend errors are visible rather than silently showing "No students found."
