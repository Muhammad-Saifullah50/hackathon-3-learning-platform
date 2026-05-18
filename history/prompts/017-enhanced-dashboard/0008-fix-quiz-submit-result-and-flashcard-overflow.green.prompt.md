---
id: "0008"
title: Fix quiz submit result display and flashcard overflow
stage: green
date: 2026-05-18
surface: agent
model: claude-sonnet-4-6
feature: 017-enhanced-dashboard
branch: 017-enhanced-dashboard
user: Muhammad
command: chat
labels: ["bug-fix","quiz","flashcard","overflow","race-condition"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - frontend/src/components/chat/quiz/QuizSummary.tsx
  - frontend/src/components/chat/quiz/FlashCard.tsx
tests:
  - null
---

## Prompt

the quiz submit route gave 200 but did not show the result. also the flashcards should have all available height so that the content does not overflow

## Response snapshot

Investigated both bugs systematically.

**Bug 1 — Quiz result not shown:** `QuizSummary` renders immediately when `phase` transitions to `'summary'`, but `submitResult` is `null` until the async `submitAll` resolves. The component showed "0.0/6" with no breakdown, giving the user no indication that results were loading. Fixed by adding an explicit loading state (spinner + "Calculating your results…") when `submitResult` is null and no `scoreOutOf6` fallback is passed.

**Bug 2 — Flashcard overflow:** Both flip faces used `absolute inset-0`, which means they only fill the parent's explicit height (`minHeight: 200px`). Content taller than 200px (e.g., a long definition on the back face) was clipped/hidden. Fixed by replacing the CSS 3D flip card with conditional rendering (`!flipped ? front : back`). Each face is now in normal document flow and expands to its natural content height. Also bumped `rows` on the textarea from 2 to 3 for a bit more breathing room.

## Outcome

- ✅ Impact: Quiz summary now shows a loading spinner while awaiting the submit response, then displays the full result. Flashcard faces expand to fit any content length.
- 🧪 Tests: No automated tests added; visual behaviour verified by code trace.
- 📁 Files: QuizSummary.tsx (loading guard), FlashCard.tsx (replace 3D flip with conditional render).
- 🔁 Next prompts: Consider stabilising ChatWindow message keys (currently `key={i}`) to prevent QuizCard state loss on new messages.
- 🧠 Reflection: The race condition between phase transition and async submit was the core of Bug 1. The absolute-positioning CSS pattern for flip cards is the classic culprit for Bug 2.

## Evaluation notes (flywheel)

- Failure modes observed: Race condition between React state update and async fetch; CSS 3D flip cards don't expand to content height.
- Graders run and results (PASS/FAIL): null
- Prompt variant (if applicable): null
- Next experiment (smallest change to try): Stabilise message keys in ChatWindow with a stable ID to prevent QuizCard remount on new chat messages.
