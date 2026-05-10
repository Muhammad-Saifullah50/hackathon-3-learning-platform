---
id: "0004"
title: Frontend Foundation Implementation Plan
stage: plan
date: 2026-05-09
surface: agent
model: claude-sonnet-4-6
feature: 013-frontend-foundation
branch: 013-frontend-foundation
user: Muhammad
command: /sp.plan
labels: ["plan","frontend","next.js","better-auth","dashboard","tailwind","shadcn","ssr","suspense"]
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
  - CLAUDE.md
tests:
  - null
---

## Prompt

/sp.plan — generate the full implementation plan for the 013-frontend-foundation feature (Next.js frontend scaffold, Better Auth, student dashboard, auth pages, design system, stub pages, theme system).

## Response snapshot

Reconstructed and wrote full plan.md after setup-plan.sh overwrote the existing file. Plan covers 6 phases (T131–T151): (1) Next.js 16 scaffold + design system, (2) Better Auth + Alembic migration, (3) middleware + auth pages, (4) student layout + data-driven dashboard with Suspense skeleton streaming, (5) stub pages + teacher placeholder, (6) unit + E2E tests. All 5 clarification decisions integrated: SSR/RSC data fetching, HTTP cookie theme persistence, WCAG 2.1 AA, mobile hamburger drawer < 768 px, Suspense skeleton screens. Constitution check passed. Agent context updated (CLAUDE.md). 4 ADR suggestions surfaced.

## Outcome

- ✅ Impact: Complete, executable implementation plan for the frontend foundation; all architectural decisions locked and documented
- 🧪 Tests: T150 (Vitest unit/component), T151 (Playwright E2E — 5 journeys) planned in Phase 6
- 📁 Files: specs/013-frontend-foundation/plan.md (full rewrite), CLAUDE.md (tech stack updated)
- 🔁 Next prompts: /sp.tasks
- 🧠 Reflection: setup-plan.sh overwrote the existing plan — should check for existing content before copying template. Plan reconstruction from memory of already-loaded docs was successful.

## Evaluation notes (flywheel)

- Failure modes observed: setup-plan.sh unconditionally overwrites plan.md even when it already contains content — data loss risk
- Graders run and results (PASS/FAIL): n/a
- Prompt variant (if applicable): n/a
- Next experiment (smallest change to try): add --skip-if-exists flag to setup-plan.sh
