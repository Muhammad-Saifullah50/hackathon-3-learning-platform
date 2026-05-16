---
id: "0017"
title: Fix New Chat Button Routing
stage: red
date: 2026-05-13
surface: agent
model: claude-sonnet-4-6
feature: 015-ai-tutor-chat
branch: 015-ai-tutor-chat
user: Muhammad
command: /sp.phr
labels: ["bug", "routing", "chat", "new-chat", "session-sidebar"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - frontend/src/components/chat/SessionSidebarServer.tsx
tests:
  - none
---

## Prompt

the new chst button isnt starting a new chat, it just closes the existing chat

## Response snapshot

Identified that the "New Chat" button in `SessionSidebarServer.tsx` was linking to `/chat` (the index page showing "Select a session") instead of `/chat/new`. Fixed by changing `href="/chat"` to `href="/chat/new"`. The `/chat/new` route is already handled by `[chatid]/page.tsx` which detects `chatid === 'new'` and renders an empty chat with `sessionId={null}`.

## Outcome

- ✅ Impact: New chat button now navigates to `/chat/new`, opening a fresh chat window instead of the placeholder index page
- 🧪 Tests: none
- 📁 Files: `frontend/src/components/chat/SessionSidebarServer.tsx` — changed `href="/chat"` to `href="/chat/new"` on line 35
- 🔁 Next prompts: Verify the new chat flow end-to-end — send a message from `/chat/new` and confirm a session is created and the URL updates
- 🧠 Reflection: The `/chat` index route and the `/chat/new` chat route are easily confused; the sidebar should always link to `/chat/new` for new sessions

## Evaluation notes (flywheel)

- Failure modes observed: None — root cause was a simple wrong href value
- Graders run and results (PASS/FAIL): none
- Prompt variant (if applicable): none
- Next experiment (smallest change to try): Consider adding an active-link highlight to the sidebar so the currently-open session is visually indicated
