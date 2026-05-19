---
id: "0002"
title: Teacher Dashboard Implementation Plan
stage: plan
date: 2026-05-18
surface: agent
model: claude-sonnet-4-6
feature: 018-teacher-dashboard
branch: 018-teacher-dashboard
user: Muhammad
command: /sp.plan
labels: ["plan", "teacher-dashboard", "class-management", "exercise-generation", "multi-agent"]
links:
  spec: specs/018-teacher-dashboard/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/018-teacher-dashboard/plan.md
  - specs/018-teacher-dashboard/research.md
  - specs/018-teacher-dashboard/data-model.md
  - specs/018-teacher-dashboard/quickstart.md
  - specs/018-teacher-dashboard/contracts/teacher-api.yaml
  - specs/018-teacher-dashboard/contracts/student-classes-api.yaml
tests:
  - none (planning phase — tests defined in /sp.tasks)
---

## Prompt

/sp.plan

## Response snapshot

Generated full implementation plan for F18 Teacher Dashboard. Phase 0 research resolved 8 unknowns (exercise agent invocation, multi-question exercise structure, teacher prompt guardrail mechanism, per-question AI review pattern, role-based route protection, frontend teacher shell, student sidebar extension, duplicate prevention). Phase 1 produced: data-model.md (7 new tables), teacher-api.yaml (7 endpoints), student-classes-api.yaml (7 endpoints), quickstart.md (full E2E smoke test flow). Agent context updated via update-agent-context.sh.

## Outcome

- ✅ Impact: Full architectural plan for F18 covering DB schema, API contracts, service logic, and frontend structure
- 🧪 Tests: No tests created (planning phase); test targets defined as 80% route coverage, 85% repo coverage
- 📁 Files: 6 new spec artifacts in specs/018-teacher-dashboard/
- 🔁 Next prompts: /sp.tasks to generate implementation task list; /sp.adr teacher-exercise-table-separation
- 🧠 Reflection: Separate teacher_generated_exercises table (vs extending exercises_agent) is the key architectural decision — keeps auto-graded and AI-reviewed exercise types cleanly separated

## Evaluation notes (flywheel)

- Failure modes observed: none
- Graders run and results (PASS/FAIL): N/A (planning phase)
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): Validate TeacherExerciseResponse schema against openai-agents SDK output_type before implementing
