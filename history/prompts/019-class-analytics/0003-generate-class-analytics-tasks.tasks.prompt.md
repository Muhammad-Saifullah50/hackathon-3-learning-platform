---
id: "0003"
title: Generate Class Analytics Tasks
stage: tasks
date: 2026-05-19
surface: agent
model: claude-sonnet-4-6
feature: 019-class-analytics
branch: master
user: Muhammad
command: /sp.tasks
labels: ["tasks","class-analytics","teacher-dashboard","analytics"]
links:
  spec: specs/019-class-analytics/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/019-class-analytics/tasks.md
tests:
  - null
---

## Prompt

/sp.tasks (no additional arguments — invoked against 019-class-analytics feature context)

## Response snapshot

Generated `specs/019-class-analytics/tasks.md` with 14 tasks across 6 phases:
- Phase 1 (Setup): T001 — verify alembic at head, no migrations needed
- Phase 2 (Foundational): T002–T007 — Pydantic schemas, AnalyticsRepository (4 async methods), dependency factory, GET endpoint with asyncio.gather(), TypeScript fetch helper, useTeacherAnalytics hook
- Phase 3 (US1 P1): T008–T009 — wire useTeacherAnalytics in AnalyticsDashboard.tsx, render 3 live stat cards (Total Students, Avg Mastery, Open Alerts), remove STAT_CARDS constant and Active Classes card, add loading/error states
- Phase 4 (US2 P1): T010 — remove MODULE_MASTERY constant, feed live module_mastery into BarChart with red/amber/green color coding
- Phase 5 (US3 P2): T011 — remove STRUGGLING_STUDENTS constant, render live list with empty state
- Phase 6 (Polish): T012–T014 — remove WEEKLY_ACTIVITY LineChart, integration tests (teacher 200, student 403, no-auth 401, score boundary 49/50), quickstart acceptance checks

## Outcome

- ✅ Impact: tasks.md created at specs/019-class-analytics/tasks.md — 14 tasks organized by user story; immediately executable
- 🧪 Tests: Integration tests scoped to T013 (backend); no TDD approach requested
- 📁 Files: specs/019-class-analytics/tasks.md (created)
- 🔁 Next prompts: /sp.implement to begin T001 execution
- 🧠 Reflection: All 3 US share one endpoint — foundational phase correctly captures all backend + hook wiring; story phases are frontend-only for independent testability

## Evaluation notes (flywheel)

- Failure modes observed: none
- Graders run and results (PASS/FAIL): none
- Prompt variant (if applicable): null
- Next experiment (smallest change to try): null
