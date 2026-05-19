---
id: "0006"
title: Redirect Teacher to Dashboard After Login
stage: green
date: 2026-05-19
surface: agent
model: claude-sonnet-4-6
feature: 018-teacher-dashboard
branch: 018-teacher-dashboard
user: Muhammad
command: /sp.phr
labels: ["teacher", "redirect", "auth", "coming-soon", "dashboard"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - frontend/src/components/auth/login-form.tsx
  - frontend/src/app/page.tsx
tests:
  - none
---

## Prompt

sincle the teacher system is ready remove the techer/coming soon page abnd redirect teacher to /dashbiard right after login

## Response snapshot

Removed the role-based branch in `login-form.tsx` that sent non-student users to `/teacher/coming-soon`, and removed the same guard in `page.tsx`. All authenticated users now redirect to `/dashboard` regardless of role.

## Outcome

- ✅ Impact: Teachers now land on `/dashboard` immediately after login; the coming-soon redirect is fully removed from both the login form and the landing page session guard.
- 🧪 Tests: none
- 📁 Files: `frontend/src/components/auth/login-form.tsx`, `frontend/src/app/page.tsx`
- 🔁 Next prompts: Optionally delete the `/teacher/coming-soon` page files if no longer needed.
- 🧠 Reflection: Two locations held the role-based redirect; both needed updating to fully remove the behaviour.

## Evaluation notes (flywheel)

- Failure modes observed: None — both redirect sites were straightforward to locate and patch.
- Graders run and results (PASS/FAIL): none
- Prompt variant (if applicable): none
- Next experiment (smallest change to try): Delete the coming-soon page/files to keep the repo clean.
