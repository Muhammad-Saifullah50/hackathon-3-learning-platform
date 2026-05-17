---
id: "0009"
title: Quiz MCQ Auto-Select Bug Fix
stage: green
date: 2026-05-17
surface: agent
model: claude-sonnet-4-6
feature: 016-quiz-system
branch: 016-quiz-system
user: Muhammad
command: chat
labels: ["bug", "quiz", "react", "key-prop", "mcq", "flashcard"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - frontend/src/components/chat/quiz/QuizCard.tsx
tests:
  - null
---

## Prompt

i requesgted a quiz and got one generated. i clicked an option and clicked it. up;on clicking it, the next question appeared and autimTICALLY SELECTED OPTION AND IS NOT GOING TO THE THIRD QUESTRION

## Response snapshot

Root cause identified via systematic debugging: `MCQCard` was rendered in `QuizCard.tsx` without a `key` prop. React reuses the same component instance across question changes (0→1→2), so the `selected` local state from question 1 persists into question 2. This causes: (1) the UI to show question 2 with an option visually "auto-selected", and (2) the `if (selected !== null) return` guard in `handleSelect` to block all clicks on question 2, preventing advancement to question 3.

Fix applied: Added `key={currentMCQIndex}` to `MCQCard` and `key={currentFlashcardIndex}` to `FlashCard` in `QuizCard.tsx`. This forces React to unmount/remount each card on index change, resetting all local state cleanly.

## Outcome

- ✅ Impact: MCQ questions now correctly reset selected state between questions; all 3 MCQ questions are answerable
- 🧪 Tests: Manual — request quiz, answer Q1, verify Q2 appears fresh with no auto-selection, answer Q2, verify Q3 appears
- 📁 Files: frontend/src/components/chat/quiz/QuizCard.tsx (2 lines changed: added key props)
- 🔁 Next prompts: Test the full quiz flow end-to-end
- 🧠 Reflection: Classic React key-prop bug — stateful child component reused across data changes without a reset mechanism

## Evaluation notes (flywheel)

- Failure modes observed: Missing `key` prop on stateful list-like child components causes state leakage between items
- Graders run and results (PASS/FAIL): Manual inspection PASS
- Prompt variant (if applicable): null
- Next experiment: Add automated test for quiz flow state transitions
