---
id: "0001"
title: Write F19 Class Analytics Spec
stage: spec
date: 2026-05-19
surface: agent
model: claude-sonnet-4-6
feature: 019-class-analytics
branch: 019-class-analytics
user: Muhammad
command: /sp.specify 019-class-analytics
labels: ["f19", "class-analytics", "spec", "teacher-dashboard"]
links:
  spec: specs/019-class-analytics/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/019-class-analytics/spec.md
  - specs/019-class-analytics/checklists/requirements.md
tests:
  - none
---

## Prompt

yes this scope is good. do you want any claifications to writge the spec

## Response snapshot

Asked two targeted questions (analytics scope: all classes combined vs per-class; struggling students data source: quiz < 50% vs keep hardcoded). User chose all-classes-combined and quiz < 50%. Wrote full spec covering 3 user stories, 7 functional requirements, 5 success criteria, edge cases, and assumptions. Weekly activity chart left as placeholder (out of scope). No NEEDS CLARIFICATION markers. All checklist items pass.

## Outcome

- ✅ Impact: Complete spec written for F19 Class Analytics, ready for /sp.plan
- 🧪 Tests: none
- 📁 Files: specs/019-class-analytics/spec.md, specs/019-class-analytics/checklists/requirements.md
- 🔁 Next prompts: /sp.plan 019-class-analytics
- 🧠 Reflection: Scoping out weekly activity chart and drill-down keeps this fast; the existing AnalyticsDashboard UI shell dramatically reduces frontend work

## Evaluation notes (flywheel)

- Failure modes observed: none
- Graders run and results (PASS/FAIL): all checklist items PASS
- Prompt variant (if applicable): n/a
- Next experiment (smallest change to try): n/a
