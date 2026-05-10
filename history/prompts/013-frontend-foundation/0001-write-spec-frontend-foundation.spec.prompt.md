---
id: "0001"
title: write spec frontend foundation
stage: spec
date: 2026-05-09
surface: agent
model: claude-sonnet-4-6
feature: 013-frontend-foundation
branch: 013-frontend-foundation
user: Muhammad
command: /sp.specify 013-frontend-foundation
labels: ["spec","frontend","auth","dashboard","better-auth","design-system"]
links:
  spec: specs/013-frontend-foundation/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/013-frontend-foundation/spec.md
  - specs/013-frontend-foundation/checklists/requirements.md
tests:
  - null
---

## Prompt

scaffold the entire nextjs frontend. with all user-facing pages including auth pages etc in addition to the current dashboard. Configure better auth and ensure it works. Develop the frontend with real data and proper designed ui using the frontend design skill. Must support both light and dark modes and default to the system.

Follow-up clarifications agreed during discovery:
- Scope: Next.js project setup + design system + Better Auth + auth pages (login, register, forgot-password, reset-password) + student layout/sidebar + Student Dashboard (full real data from backend) + stub pages for /chat, /progress, /quiz/[lessonId] + teacher "coming soon" placeholder.
- No teacher pages (F18–F21) in this spec.
- Better Auth: share the existing Neon PostgreSQL DB, map to existing users table.
- Component library: shadcn/ui on top of Tailwind CSS.
- Extra student pages (/chat, /progress, /quiz) are empty stubs with full layout wired up.
- After login: students → /dashboard, teachers → /teacher/coming-soon.

## Response snapshot

Created `specs/013-frontend-foundation/spec.md` with:
- 6 prioritised user stories covering registration, login+dashboard, navigation, password reset, dark/light mode, and teacher placeholder.
- 26 functional requirements across auth, dashboard, navigation, stub pages, and theming.
- 5 key entities: Student Session, Module Progress Card, Learning Streak, Weak Area, Recommendation.
- 7 assumptions documented (self-registration = student role, email verification optional in MVP, etc.).
- 8 measurable, technology-agnostic success criteria.
- Full edge case coverage (expired token, backend unavailable, HIBP rejection, malformed reset link).
- Quality checklist created and all items pass.

## Outcome

- ✅ Impact: Spec fully defines the frontend foundation scope, auth flows, dashboard data requirements, and theming — ready for /sp.plan.
- 🧪 Tests: No tests run (spec stage).
- 📁 Files: specs/013-frontend-foundation/spec.md, specs/013-frontend-foundation/checklists/requirements.md
- 🔁 Next prompts: /sp.plan 013-frontend-foundation
- 🧠 Reflection: Discovery session upfront (interview skill) clarified 4 key decisions (project scope, auth DB strategy, component library, stub vs full pages) that would have caused rework if assumed incorrectly.

## Evaluation notes (flywheel)

- Failure modes observed: none
- Graders run and results (PASS/FAIL): quality checklist — all 14 items PASS
- Prompt variant (if applicable): null
- Next experiment (smallest change to try): null
