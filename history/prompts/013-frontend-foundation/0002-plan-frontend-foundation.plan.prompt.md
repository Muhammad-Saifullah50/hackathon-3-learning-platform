---
id: "0002"
title: plan frontend foundation
stage: plan
date: 2026-05-09
surface: agent
model: claude-sonnet-4-6
feature: 013-frontend-foundation
branch: 013-frontend-foundation
user: Muhammad
command: /sp.plan
labels: ["plan","frontend","next.js-16","better-auth","shadcn-ui","dashboard","design-system"]
links:
  spec: specs/013-frontend-foundation/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/013-frontend-foundation/plan.md
  - specs/013-frontend-foundation/research.md
  - specs/013-frontend-foundation/data-model.md
  - specs/013-frontend-foundation/quickstart.md
  - specs/013-frontend-foundation/contracts/frontend-backend.md
tests:
  - null
---

## Prompt

/sp.plan (for feature 013-frontend-foundation). User clarified during planning: use Next.js 16.

## Response snapshot

Full planning artifacts created across 6 phases (T131–T151):
- research.md: Next.js 16 confirmed (Turbopack default, async cookies/params); Better Auth uses pg.Pool natively with custom password.verify proxy to FastAPI; FOUC prevention pattern; Warm Code Scholar color palette with Fraunces+Outfit+JetBrains Mono fonts.
- data-model.md: TypeScript types, Better Auth DB tables, mastery color mappings.
- contracts/frontend-backend.md: All FastAPI endpoints with request/response shapes.
- quickstart.md: Dev setup from scratch.
- plan.md: 21 tasks across 6 phases — scaffold, Better Auth+migration, middleware+auth pages, student layout+dashboard, stubs, tests.
- 2 ADR suggestions: Better Auth session proxy pattern; Server Component + React Query hybrid.
- Agent context (CLAUDE.md) updated with TypeScript 5+/React 19 + Neon PostgreSQL.

## Outcome

- ✅ Impact: Complete implementation plan for the entire frontend foundation — every spec acceptance criterion mapped to a concrete task.
- 🧪 Tests: No tests run (plan stage). Test tasks T150–T151 defined.
- 📁 Files: plan.md, research.md, data-model.md, quickstart.md, contracts/frontend-backend.md
- 🔁 Next prompts: /sp.tasks 013-frontend-foundation
- 🧠 Reflection: Background research agents lacked WebSearch; fetch-library-docs skill was the reliable source for Next.js 16 and Better Auth confirmation. Lesson: use fetch-library-docs first for library questions.

## Evaluation notes (flywheel)

- Failure modes observed: 3/4 background agents had no WebSearch — mitigated by fetch-library-docs skill
- Graders run and results (PASS/FAIL): Constitution check all PASS or targeted
- Prompt variant (if applicable): null
- Next experiment (smallest change to try): Invoke fetch-library-docs before spawning background agents for library-specific research
