---
id: "0011"
title: MCQ code block formatting fix
stage: green
date: 2026-05-17
surface: agent
model: claude-sonnet-4-6
feature: 016-quiz-system
branch: 016-quiz-system
user: Muhammad
command: bug fix
labels: ["quiz","mcq","markdown","code-formatting","flashcard"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - frontend/src/components/chat/MarkdownBody.tsx (created)
  - frontend/src/components/chat/quiz/MCQCard.tsx (modified)
  - frontend/src/components/chat/quiz/FlashCard.tsx (modified)
  - frontend/src/components/chat/ChatMessage.tsx (modified)
tests:
  - tsc --noEmit passes with no errors in edited files
---

## Prompt

aqlso if any code block is present in the mcq querstion , iot is nit formatted as it is in the concets agent answer

## Response snapshot

Root cause: `MCQCard.tsx` rendered `question.question` and each `option` as raw JSX strings (`{question.question}`, `{option}`), bypassing all markdown/code formatting. The concepts agent used `<MarkdownBody>` (ReactMarkdown + SyntaxHighlighter) defined inside `ChatMessage.tsx`.

Fix:
1. Extracted `MarkdownBody` into a shared `frontend/src/components/chat/MarkdownBody.tsx`
2. Updated `ChatMessage.tsx` to import from the shared file and removed the inline definition
3. Updated `MCQCard.tsx` to wrap `question.question` and each option's text in `<MarkdownBody>`
4. Also fixed `FlashCard.tsx` (same raw-text bug for `question.term` and `question.definition`)

TypeScript check: no errors in edited files.

## Outcome

- ✅ Impact: Code blocks in MCQ questions and options now render with syntax highlighting, matching the concepts agent output
- 🧪 Tests: tsc --noEmit passes with no errors in edited files
- 📁 Files: 4 files changed (1 created, 3 modified)
- 🔁 Next prompts: visual smoke test in browser with a quiz that has code in questions/options
- 🧠 Reflection: Pattern was clear — `MarkdownBody` was not shared. Extracting it to a dedicated file is the minimal correct fix.

## Evaluation notes (flywheel)

- Failure modes observed: none
- Graders run and results (PASS/FAIL): tsc PASS
- Prompt variant (if applicable): null
- Next experiment (smallest change to try): add prose-sm class to MarkdownBody if font sizes feel inconsistent inside option buttons
