---
id: "0001"
title: Quiz System Spec Written
stage: spec
date: 2026-05-12
surface: agent
model: claude-sonnet-4-6
feature: 016-quiz-system
branch: 016-quiz-system
user: Muhammad
command: /sp.specify 016-quiz-system
labels: ["spec", "quiz", "chat", "mcq", "flashcard", "mastery"]
links:
  spec: specs/016-quiz-system/spec.md
  ticket: "null"
  adr: "null"
  pr: "null"
files:
  - specs/016-quiz-system/spec.md
  - specs/016-quiz-system/checklists/requirements.md
  - history/prompts/016-quiz-system/0001-quiz-system-spec-written.spec.prompt.md
tests:
  - "null"
---

## Prompt

ok so lets discuss feature 16 from features.md. go through it and then discuss it with me and then we will write the spec. The ui should be 3 mcqs and 3 flashcards.

(Clarifications gathered via interview skill:)
- Flashcard type: Term → Definition (student types answer before card flips, AI grades)
- Entry point: From the AI Tutor Chat (F15) — quiz renders inline in chat feed
- Card order: MCQs first (3), then flashcards (3) — sequential
- Flashcard grading: AI-graded typed answer
- Topic source: Current chat topic (inferred from conversation context)
- Quiz surface: Inline in the chat window (no separate page)

Additional user note: The quiz agent needs to emit structured output for the quiz UI to be rendered.

## Response snapshot

Spec written for F16 Quiz System at specs/016-quiz-system/spec.md. Key decisions captured:
- Fixed 6-card deck: 3 MCQs (client-side graded) → 3 flashcards (AI-graded typed answers)
- Inline rendering in AI Tutor Chat feed using the existing `response_type` discriminated-output SSE pattern
- Quiz triggered by triage agent detecting quiz intent in chat messages
- Quiz generator emits `QuizAgentResponse` with `response_type: "quiz"` for frontend QuizCard rendering
- MCQ correct answers embedded in structured output (no round-trip); flashcard definitions also embedded (for flip reveal); only typed flashcard answers sent back for AI grading
- Mastery updated on submit (quizzes = 30% weight)
- New `ai_quiz_sessions` table for persistence (follows exercises_agent pattern)
- 4 user stories (P1–P4), 13 functional requirements, 6 success criteria, 8 assumptions, 4 dependencies

## Outcome

- ✅ Impact: Spec created for F16 Quiz System; branch 016-quiz-system created; ready for /sp.plan
- 🧪 Tests: No tests run (spec phase)
- 📁 Files: specs/016-quiz-system/spec.md, specs/016-quiz-system/checklists/requirements.md
- 🔁 Next prompts: /sp.plan 016-quiz-system, /sp.tasks 016-quiz-system
- 🧠 Reflection: Interview skill used to surface key decisions before spec writing; structured output requirement explicitly captured in FR-003

## Evaluation notes (flywheel)

- Failure modes observed: none
- Graders run and results (PASS/FAIL): quality checklist all pass
- Prompt variant (if applicable): none
- Next experiment (smallest change to try): run /sp.plan to architect the backend agent + frontend QuizCard
