---
id: "0003"
title: Enhanced Dashboard Implementation Plan
stage: plan
date: 2026-05-18
surface: agent
model: claude-sonnet-4-6
feature: 017-enhanced-dashboard
branch: 017-enhanced-dashboard
user: Muhammad
command: /sp.plan
labels: [dashboard, charts, recharts, sse, progress-agent, mastery-snapshots]
links:
  spec: specs/017-enhanced-dashboard/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/017-enhanced-dashboard/plan.md
  - specs/017-enhanced-dashboard/research.md
  - specs/017-enhanced-dashboard/data-model.md
  - specs/017-enhanced-dashboard/quickstart.md
  - specs/017-enhanced-dashboard/contracts/openapi.yaml
tests:
  - null
---

## Prompt

/sp.plan (no additional user input — auto-invoked on branch 017-enhanced-dashboard)

## Response snapshot

Generated full architectural plan for Feature 017 (Enhanced Student Dashboard & Module Progress Detail). Key findings:

1. `user_module_mastery` is a single-row-per-user-per-module table — cannot serve as a time-series. A new `mastery_snapshots` append-only table is required for the "Mastery Over Time" chart.
2. `recharts@^2.15.0` is already installed in the frontend.
3. Two new dedicated SSE endpoints planned (`GET /api/v1/dashboard/recommendations/stream` and `GET /api/v1/module/{moduleId}/progress/stream`), separate from the chat SSE to avoid quota/session entanglement.
4. Progress Agent extended with `agent_mode` branching via `LearnPyByAIContext`.
5. `/progress` page is a trivial `ComingSoonPanel` — delete and return 404.
6. Sidebar `NAV_ITEMS` contains `Progress` link — remove.

## Outcome

- ✅ Impact: Full 8-phase implementation plan with file-level specificity; identified spec assumption gap (mastery history table)
- 🧪 Tests: Not yet — tasks phase will define test tasks
- 📁 Files: plan.md, research.md, data-model.md, quickstart.md, contracts/openapi.yaml
- 🔁 Next prompts: /sp.tasks to generate implementation task list
- 🧠 Reflection: Spec assumption about existing timestamped mastery records was incorrect — the actual DB only stores current score. Identified and documented a new table requirement.

## Evaluation notes (flywheel)

- Failure modes observed: none
- Graders run and results (PASS/FAIL): none yet
- Prompt variant (if applicable): null
- Next experiment (smallest change to try): run /sp.tasks to validate phase breakdown
