---
id: "0003"
title: Generate Teacher Dashboard Tasks
stage: tasks
date: 2026-05-18
surface: agent
model: claude-sonnet-4-6
feature: 018-teacher-dashboard
branch: 018-teacher-dashboard
user: Muhammad
command: /sp.tasks
labels: ["tasks", "teacher-dashboard", "planning", "f18"]
links:
  spec: specs/018-teacher-dashboard/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/018-teacher-dashboard/tasks.md
tests:
  - none
---

## Prompt

/sp.tasks

(invoked on branch 018-teacher-dashboard with empty user input — generates tasks.md from all available design artifacts in specs/018-teacher-dashboard/)

## Response snapshot

Generated `specs/018-teacher-dashboard/tasks.md` with 51 tasks across 8 phases covering all 5 user stories (US1–US5) for F18 Teacher Dashboard. Tasks are organized by user story (P1→P2→P3 priority order) with parallel execution opportunities marked. Full backend + frontend coverage including Alembic migration, 7 SQLAlchemy models, 4 repositories, 4 services, 2 API routers, teacher shell layout, exercise generation page, student sidebar extensions, and student exercise completion view.

## Outcome

- ✅ Impact: tasks.md created at specs/018-teacher-dashboard/tasks.md; 51 tasks across 8 phases; all 5 user stories have independent test criteria
- 🧪 Tests: no test tasks generated (not requested in spec)
- 📁 Files: specs/018-teacher-dashboard/tasks.md (created)
- 🔁 Next prompts: /sp.implement to begin executing tasks; start with T001 (migration) and T002 (router registration)
- 🧠 Reflection: US3 depends on US2 (classes must exist before assignment); US4 depends on US3 (exercises must exist to complete); T029 and T043 both modify NavLinks.tsx — flagged as sequential dependency in notes

## Evaluation notes (flywheel)

- Failure modes observed: none
- Graders run and results (PASS/FAIL): none
- Prompt variant (if applicable): null
- Next experiment (smallest change to try): null
