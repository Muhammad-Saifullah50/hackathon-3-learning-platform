---
id: "0019"
title: Fix Markdown Hydration Error p Cannot Contain div
stage: red
date: 2026-05-13
surface: agent
model: claude-sonnet-4-6
feature: 015-ai-tutor-chat
branch: 015-ai-tutor-chat
user: Muhammad
command: correct this hydration error
labels: ["hydration","markdown","react","bugfix"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - frontend/src/components/chat/ChatMessage.tsx
tests:
  - manual browser verification
---

## Prompt

correct tghus hydration error [browser console output showing]:
- `<pre> cannot be a descendant of <p>`
- `<div> cannot be a descendant of <p>`
- Hydration failed because the server rendered HTML didn't match the client
The error traced to `MarkdownBody` in `ChatMessage.tsx` where the `p` renderer wraps content in `<p>`, but the `code` renderer returns a `<div>/<pre>` for block code — invalid HTML nesting.

## Response snapshot

Changed `MarkdownBody`'s `p` component from `<p>` to `<div>` in `frontend/src/components/chat/ChatMessage.tsx:97`. This resolves the invalid HTML nesting that caused hydration mismatches when react-markdown placed code blocks inside paragraph elements.

## Outcome

- ✅ Impact: Hydration errors eliminated; `<p>` → `<div>` wrapper allows block-level children from code renderer
- 🧪 Tests: Manual browser test — reload chat session page and confirm no hydration errors in console
- 📁 Files: frontend/src/components/chat/ChatMessage.tsx (1 line changed)
- 🔁 Next prompts: Continue with T022 SessionSidebar or T023 full /chat page
- 🧠 Reflection: react-markdown wraps block code nodes inside `<p>` which conflicts with block-level custom renderers; always use `<div>` for paragraph wrappers in markdown contexts that may contain code blocks

## Evaluation notes (flywheel)

- Failure modes observed: Invalid HTML nesting causing React hydration mismatch on SSR pages
- Graders run and results (PASS/FAIL): manual — PASS (no console errors after fix)
- Prompt variant (if applicable): null
- Next experiment: null
