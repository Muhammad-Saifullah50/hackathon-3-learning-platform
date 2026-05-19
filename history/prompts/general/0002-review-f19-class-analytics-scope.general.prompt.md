---
id: "0002"
title: Review F19 Class Analytics Scope
stage: general
date: 2026-05-19
surface: agent
model: claude-sonnet-4-6
feature: none
branch: 018-teacher-dashboard
user: Muhammad
command: user message
labels: ["f19", "class-analytics", "teacher-dashboard", "scoping"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - none
tests:
  - none
---

## Prompt

ok so now lets focus on feture 19. go through it and then we eill discuss it . i just want basuc analytics n the dashbiard. and want to finish this feature fast and quick.

## Response snapshot

Reviewed F19 (Class Analytics) from FEATURES.md and existing codebase. Found that AnalyticsDashboard.tsx already has the full UI shell with hardcoded placeholder data. Backend has no analytics endpoints. Proposed minimal scope: one backend analytics endpoint returning real DB data, wiring existing UI to it. Recommended skipping CSV export and individual drill-down for speed.

## Outcome

- ✅ Impact: Scoped F19 to minimal viable implementation — replace hardcoded placeholders with real data
- 🧪 Tests: none
- 📁 Files: none
- 🔁 Next prompts: User to confirm scope, then implement analytics API endpoint and wire frontend
- 🧠 Reflection: F18 already built the UI shell; F19 is mostly a backend data layer + frontend wiring task

## Evaluation notes (flywheel)

- Failure modes observed: none
- Graders run and results (PASS/FAIL): n/a
- Prompt variant (if applicable): n/a
- Next experiment (smallest change to try): Confirm user scope agreement before implementation
