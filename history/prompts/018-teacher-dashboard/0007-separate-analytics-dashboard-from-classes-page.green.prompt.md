---
id: "0007"
title: Separate analytics dashboard from classes page
stage: green
date: 2026-05-19
surface: agent
model: claude-sonnet-4-6
feature: 018-teacher-dashboard
branch: 018-teacher-dashboard
user: Muhammad
command: user message
labels: [teacher-dashboard, analytics, recharts, classes, navigation]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - frontend/src/app/(teacher)/teacher/dashboard/page.tsx
  - frontend/src/app/(teacher)/teacher/classes/page.tsx
  - frontend/src/components/teacher/AnalyticsDashboard.tsx
tests:
  - none
---

## Prompt

put placeholder analytics chrts on the /teacher/dashboard page and put the allm classes srelated stuff in the /teacher/classes page

## Response snapshot

Created `/teacher/classes/page.tsx` with the ClassesPanel (class list, create class, invite students). Rewrote `/teacher/dashboard/page.tsx` to use a new `AnalyticsDashboard` component featuring: 4 stat cards (total students, active classes, avg mastery, open alerts), a recharts bar chart for module mastery, a recharts line chart for weekly activity, and a struggling students table — all with placeholder data.

## Outcome

- ✅ Impact: Dashboard now shows analytics overview; all class management moved to dedicated /teacher/classes route (already linked in nav)
- 🧪 Tests: none
- 📁 Files: 3 files created/modified
- 🔁 Next prompts: Wire analytics to real backend data; add struggle alert actions from dashboard
- 🧠 Reflection: Nav already had a "Classes" link pointing to /teacher/classes — the page just didn't exist yet

## Evaluation notes (flywheel)

- Failure modes observed: none
- Graders run and results (PASS/FAIL): TypeScript check — only pre-existing errors, no new errors introduced
- Prompt variant (if applicable): none
- Next experiment (smallest change to try): Connect stat cards to real API totals
