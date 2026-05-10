---
id: "0006"
title: Generate Tasks Frontend Foundation
stage: tasks
date: 2026-05-09
surface: agent
model: claude-sonnet-4-6
feature: 013-frontend-foundation
branch: 013-frontend-foundation
user: Muhammad
command: /sp.tasks
labels: ["tasks","frontend","nextjs","better-auth","dashboard","shadcn","tailwind","playwright","vitest"]
links:
  spec: specs/013-frontend-foundation/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/013-frontend-foundation/tasks.md
tests:
  - null
---

## Prompt

(empty — /sp.tasks invoked with no additional user input; auto-detects feature from branch `013-frontend-foundation`)

## Response snapshot

Generated `specs/013-frontend-foundation/tasks.md` — 70 tasks across 11 phases for the Frontend Foundation & Student Dashboard feature.

**Structure**:
- Phase 1 (Setup, T001–T005): Next.js 16 init, Tailwind CSS 4 + shadcn/ui, next.config.ts, tsconfig/prettier/eslint, root layout with fonts + ThemeProvider + FOUC-prevention script
- Phase 2 (Foundational, T006–T012): Alembic migration for Better Auth tables, TypeScript types, API fetch wrapper, Better Auth server + route handler + auth client, Next.js middleware
- Phase 3 (US1 P1, T013–T023): Register form/page, masteryColor/masteryLevel utils, ModuleCard/ModuleGrid/DashboardSkeleton, basic StudentSidebar + TopNav, student layout server component with role guard, Dashboard server page with Suspense
- Phase 4 (US2 P1, T024–T032): Login form/page, StreakBadge/MasteryOverview/WeakAreasPanel/RecommendationsPanel widgets, DashboardClient, useProgress/useProfile hooks
- Phase 5 (US3 P2, T033–T037): Enhanced sidebar with active states + hamburger drawer, enhanced TopNav with theme toggle, stub pages (chat, progress, quiz)
- Phase 6 (US4 P2, T038–T041): ForgotPasswordForm + page, ResetPasswordForm + page (async searchParams, no-enumeration)
- Phase 7 (US6 P2, T042–T051): Landing page root page, LandingNavbar, HeroSection, HowItWorksSection, CurriculumSection, FeaturesSection, StatsSection, CtaSection, LandingFooter, responsive validation
- Phase 8 (US5 P3, T052): ThemeProvider cookie-write sync
- Phase 9 (US7 P3, T053–T054): Teacher coming-soon page + role guard validation
- Phase 10 (Tests, T055–T067): Vitest config, Playwright config, 5 unit test suites, 6 E2E spec files
- Phase 11 (Polish, T068–T070): Quickstart verification, WCAG axe-core check, bundle size check

**MVP scope**: Phases 1–4 (38 tasks) — full auth + data-driven Student Dashboard.
**Parallel opportunities**: 24 tasks marked [P].

## Outcome

- ✅ Impact: `specs/013-frontend-foundation/tasks.md` created with 70 tasks covering all 7 user stories (US1–US7) from spec.md, organized for independent implementation and testing of each story
- 🧪 Tests: Included — Vitest (5 unit/component suites) + Playwright (6 E2E journeys): registration, login, password-reset, theme-toggle, route-protection, landing-page
- 📁 Files: specs/013-frontend-foundation/tasks.md (created)
- 🔁 Next prompts: `/sp.implement T001` to begin setup phase; or `/sp.implement T013-T023` to go straight to MVP US1 after foundational is done
- 🧠 Reflection: Tasks organized by user story with clear checkpoints and independent test criteria per phase; MVP scope clearly identified as Phases 1–4

## Evaluation notes (flywheel)

- Failure modes observed: none
- Graders run and results (PASS/FAIL): none
- Prompt variant (if applicable): null
- Next experiment (smallest change to try): null
