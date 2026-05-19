---
id: "0002"
title: Plan Class Analytics Feature
stage: plan
date: 2026-05-19
surface: agent
model: claude-sonnet-4-6
feature: 019-class-analytics
branch: master
user: Muhammad
command: /sp.plan
labels: ["planning", "analytics", "teacher-dashboard", "api-design", "no-migration"]
links:
  spec: specs/019-class-analytics/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/019-class-analytics/plan.md
  - specs/019-class-analytics/research.md
  - specs/019-class-analytics/data-model.md
  - specs/019-class-analytics/quickstart.md
  - specs/019-class-analytics/contracts/teacher-analytics.yaml
tests:
  - null
---

## Prompt

/sp.plan (no additional user input)

## Response snapshot

Generated full implementation plan for F019 Class Analytics across 5 artifacts:

1. **research.md** — Resolved 6 architectural unknowns: no `classes`/`class_memberships` tables exist (confirmed via Alembic migrations), so analytics scope to all platform students. `Active Classes` stat removed per FR-008. Weekly Activity chart deleted. Quiz scores sourced from `quiz_sessions` WHERE status='completed'. Module names from JOIN with `modules` table. Teacher analytics added to existing `dashboard.py` router under `/dashboard/teacher/analytics`.

2. **data-model.md** — Entities, SQL query patterns (DISTINCT ON for latest quiz per student, LEFT JOIN with COALESCE for module mastery), response shape, and index analysis. No new tables or migrations required.

3. **contracts/teacher-analytics.yaml** — Full OpenAPI 3.1 spec for `GET /api/v1/dashboard/teacher/analytics` returning `TeacherAnalyticsResponse` with total_students, avg_mastery, low_quiz_count, module_mastery, struggling_students. Auth: Bearer JWT, role guard (teacher/admin only → 403 for others).

4. **plan.md** — Complete implementation plan: AnalyticsRepository (4 async methods), 3 new Pydantic schemas, 1 new endpoint with asyncio.gather(), dependency factory registration, frontend fetch helper + useTeacherAnalytics hook, AnalyticsDashboard.tsx changes. Constitution check passed. Risk table included.

5. **quickstart.md** — Developer setup guide: no migrations, files to create/modify, manual test commands, seed SQL for local testing.

ADR surfaced: Classless analytics scope decision (aggregate all students, not per-teacher class).

## Outcome

- ✅ Impact: F019 planning complete. Ready to run /sp.tasks to generate implementation tasks.
- 🧪 Tests: No tests run (planning phase). Integration test file path specified in plan.
- 📁 Files: 5 new artifacts created under specs/019-class-analytics/
- 🔁 Next prompts: /sp.tasks to generate tasks.md; /sp.adr classless-analytics-scope to document the architecture decision
- 🧠 Reflection: Critical discovery — no class management infrastructure exists (F018 was never built). The "fast scope" description in the spec input correctly anticipated this; scoping to all platform students is the right pragmatic call for F019.

## Evaluation notes (flywheel)

- Failure modes observed: none
- Graders run and results (PASS/FAIL): none (planning phase)
- Prompt variant (if applicable): null
- Next experiment (smallest change to try): Run /sp.tasks to validate that the plan decomposes cleanly into testable tasks
