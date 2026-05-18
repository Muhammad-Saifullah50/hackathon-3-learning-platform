---
id: "0002"
title: Clarify Enhanced Dashboard Spec
stage: spec
date: 2026-05-18
surface: agent
model: claude-sonnet-4-6
feature: 017-enhanced-dashboard
branch: 017-enhanced-dashboard
user: Muhammad
command: /sp.clarify
labels: ["clarification", "sse", "progress-agent", "dashboard"]
links:
  spec: specs/017-enhanced-dashboard/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/017-enhanced-dashboard/spec.md
tests:
  - null
---

## Prompt

/sp.clarify (invoked on feature 017-enhanced-dashboard)

## Response snapshot

Ran structured ambiguity scan against the 017-enhanced-dashboard spec. Two Partial categories identified and resolved via two clarification questions:

1. SSE endpoint structure: new dedicated endpoints (`GET /api/v1/dashboard/recommendations/stream` and `GET /api/v1/module/{moduleId}/progress/stream`) rather than extending the F15 chat stream endpoint.
2. Progress Agent context data: mastery scores only (all modules from `mastery_records`) — no code submissions or quiz attempts.

Both answers written into the Clarifications section and propagated to the Assumptions (SSE) and FR-011 (agent context).

## Outcome

- ✅ Impact: Two integration ambiguities resolved — SSE endpoint structure and Progress Agent payload defined; downstream plan/tasks can now be produced without rework risk on these points.
- 🧪 Tests: No tests run — clarification session only.
- 📁 Files: specs/017-enhanced-dashboard/spec.md updated (Clarifications section + Assumptions + FR-011).
- 🔁 Next prompts: `/sp.plan` to produce architecture plan; `/sp.tasks` to generate task list.
- 🧠 Reflection: Spec was already very complete from prior session; only 2 high-impact gaps remained. Keeping agent context minimal (mastery scores only) reduces backend complexity and payload size.

## Evaluation notes (flywheel)

- Failure modes observed: none
- Graders run and results (PASS/FAIL): n/a
- Prompt variant (if applicable): n/a
- Next experiment (smallest change to try): n/a
