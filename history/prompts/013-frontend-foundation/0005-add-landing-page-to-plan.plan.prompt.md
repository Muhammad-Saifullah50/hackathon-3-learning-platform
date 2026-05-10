---
id: "0005"
title: Add Landing Page to Plan
stage: plan
date: 2026-05-09
surface: agent
model: claude-sonnet-4-6
feature: 013-frontend-foundation
branch: 013-frontend-foundation
user: Muhammad
command: ad-hoc (post-plan amendment)
labels: ["plan","landing-page","marketing","ux","frontend"]
links:
  spec: specs/013-frontend-foundation/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/013-frontend-foundation/spec.md
  - specs/013-frontend-foundation/plan.md
tests:
  - null
---

## Prompt

also add to the plan to build a perfect landing page for the app. i forgot. it must demonstrate the entire workflow of the app

## Response snapshot

Added landing page as User Story 6 (P2) in spec.md with 7 acceptance scenarios covering: hero + CTAs, workflow steps section, 8 module cards, features bento, authenticated redirect to /dashboard, mobile responsiveness. Added FR-023 through FR-029 (renumbered existing Theming FRs to FR-031–FR-033 to avoid clash). Added Phase 5 "Landing Page" (T148) to plan.md with detailed section breakdown: Navbar, Hero (animated mock terminal), How It Works (5-step flow), Curriculum Modules grid, Features bento, Stats row, Final CTA, Footer. Updated project structure tree. Renumbered Phase 6 (Stub Pages → T149–T150), Phase 7 (Tests → T151–T152) and added landing-page.spec.ts as 6th E2E journey.

## Outcome

- ✅ Impact: Landing page fully specced and planned; clear conversion funnel from anonymous visitor to registration established
- 🧪 Tests: T151 adds hero-section unit test; T152 adds landing-page.spec.ts E2E journey
- 📁 Files: specs/013-frontend-foundation/spec.md (US6, FR-023 to FR-033), specs/013-frontend-foundation/plan.md (Phase 5 T148, renumbered T149 to T152, project structure)
- 🔁 Next prompts: /sp.tasks
- 🧠 Reflection: Landing page properly placed at P2 priority — it is an entry point for new users but does not block core learning flows (P1). The mock AI terminal in the hero avoids any Monaco/Prism dependency and keeps the bundle clean.

## Evaluation notes (flywheel)

- Failure modes observed: none
- Graders run and results (PASS/FAIL): n/a
- Prompt variant (if applicable): n/a
- Next experiment (smallest change to try): n/a
