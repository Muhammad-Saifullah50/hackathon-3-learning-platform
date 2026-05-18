---
id: "0004"
title: Generate Enhanced Dashboard Tasks
stage: tasks
date: 2026-05-18
surface: agent
model: claude-sonnet-4-6
feature: 017-enhanced-dashboard
branch: 017-enhanced-dashboard
user: Muhammad
command: /sp.tasks
labels: ["tasks", "dashboard", "recharts", "sse", "progress-agent", "mastery-snapshots"]
links:
  spec: specs/017-enhanced-dashboard/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/017-enhanced-dashboard/tasks.md
tests:
  - null
---

## Prompt

/sp.tasks

## Response snapshot

Generated `specs/017-enhanced-dashboard/tasks.md` with 34 tasks across 8 phases organised by user story.

**Phase structure**:
- Phase 1 (Setup, 1 task): Alembic migration for `mastery_snapshots` table
- Phase 2 (Foundational, 4 tasks): Pydantic schemas, LearnFlowContext extension, frontend TS types, router registration
- Phase 3 (US1 Charts P1, 7 tasks): MasterySnapshotRepository, ProgressRepository extension, mastery-history endpoint, Recharts charts, dashboard integration
- Phase 4 (US2 Recommendations P1, 7 tasks): Prompts, Progress Agent branching, recommendations SSE endpoint, SSE hook, RecommendationsPanel update, dashboard wiring
- Phase 5 (US3 Navigation P1, 3 tasks): module-card.tsx button change, topic-skeleton.tsx, module progress page scaffold
- Phase 6 (US4 Module Agent P2, 7 tasks): Module detail prompts, agent branching, module progress stream endpoint, SSE hook, topic-list.tsx, page wiring
- Phase 7 (US5 Removals P1, 2 tasks): Delete /progress page, remove nav link
- Phase 8 (Polish, 3 tasks): alembic upgrade head, error boundaries, quickstart validation

**MVP scope**: US1 + US3 + US5 (no agent dependency) — charts, navigation change, /progress removal.

## Outcome

- ✅ Impact: 34 actionable tasks generated covering all 5 user stories; every task has exact file path and is independently executable
- 🧪 Tests: No test tasks generated (not requested in spec)
- 📁 Files: specs/017-enhanced-dashboard/tasks.md created
- 🔁 Next prompts: `/sp.implement` to begin executing tasks; start with Phase 1 (T001 migration) then Phase 2 foundational tasks
- 🧠 Reflection: US4 (module detail agent) has a hard dependency on US3 (page scaffold) — this is the only cross-story dependency. All other user stories are independent and can proceed in parallel after Phase 2.

## Evaluation notes (flywheel)

- Failure modes observed: none
- Graders run and results (PASS/FAIL): n/a
- Prompt variant (if applicable): n/a
- Next experiment (smallest change to try): n/a
