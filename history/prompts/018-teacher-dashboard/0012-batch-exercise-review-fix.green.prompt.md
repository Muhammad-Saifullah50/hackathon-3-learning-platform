---
id: "0012"
title: Batch Exercise Review Fix
stage: green
date: 2026-05-19
surface: agent
model: claude-sonnet-4-6
feature: 018-teacher-dashboard
branch: 018-teacher-dashboard
user: Muhammad
command: /sp.phr
labels: ["exercise-review","batch-requests","promise-all","ux","teacher-dashboard"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - frontend/src/hooks/useAssignedExercises.ts
  - frontend/src/components/student/ExerciseWorkspace.tsx
  - frontend/src/components/student/ExerciseQuestionView.tsx
tests:
  - none
---

## Prompt

the final question did nit have a review and score display although it was generated =. also i want all these questions to go all at once in one request . the loader doesnt need to show which question is r=bting reviewewdand also subnmit them to the teacyher and show thst it is submitted

## Response snapshot

Identified root cause: `ExerciseQuestionView` hid the review for a question whenever `reviewingThis=true`, so the last question's review was blocked until the next render cycle. Changed sequential per-question review loop to concurrent `Promise.all` across all questions. All reviews now fire simultaneously, results are applied in a single state update, and every question's AI review card appears together. Removed `reviewingThis` prop entirely and simplified the button label to a generic "Reviewing…" spinner.

## Outcome

- ✅ Impact: All exercise questions reviewed concurrently; last question now shows AI review and score; button shows a plain spinner instead of "Reviewing question X of Y"
- 🧪 Tests: none
- 📁 Files: useAssignedExercises.ts (Promise.all, isReviewing bool), ExerciseWorkspace.tsx (remove reviewingIndex/reviewingThis), ExerciseQuestionView.tsx (remove reviewingThis prop, simplify condition)
- 🔁 Next prompts: Consider adding error-per-question recovery if one concurrent review fails
- 🧠 Reflection: The `!reviewingThis` guard was meant to avoid a flash of stale content but actually permanently hid the last question's review during the submit flow; removing per-question tracking entirely was the cleaner fix

## Evaluation notes (flywheel)

- Failure modes observed: none
- Graders run and results (PASS/FAIL): n/a
- Prompt variant (if applicable): n/a
- Next experiment (smallest change to try): Add per-question error state so a single failed concurrent review doesn't block the others
