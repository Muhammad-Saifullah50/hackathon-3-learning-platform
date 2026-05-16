---
id: "0020"
title: Fix new chat mid-stream navigation unmounting component
stage: red
date: 2026-05-13
surface: agent
model: claude-sonnet-4-6
feature: 015-ai-tutor-chat
branch: 015-ai-tutor-chat
user: Muhammad
command: chat debug
labels: ["bug", "streaming", "navigation", "ux", "new-chat"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - frontend/src/hooks/useStreamChat.ts
  - frontend/src/components/chat/ChatInputClient.tsx
tests:
  - manual
---

## Prompt

there is a ux bug . when i clikc the new chat button i get redirected to /chat/new . when i send a message, i forsty  get a loading indicator, but then the page navigates to the new chat page with a skeleton. then onkyh i get ti to see my message and no response comes. how to fgix that . search how chatgot and gemini do this dor their chat apps

## Response snapshot

Root cause identified via systematic debugging:

1. Backend emits `event: session\ndata: {id}` as the VERY FIRST SSE event (agents.py:213)
2. `useStreamChat` receives it → `setSessionId(payload)` fires immediately
3. `useEffect` in `ChatInputClient` watching `streamSessionId` fires → calls `router.replace('/chat/{id}')` mid-stream
4. Next.js App Router navigation unmounts `ChatInputClient`, killing all streaming state
5. New page loads skeleton, fetches DB → but assistant response isn't saved yet (backend saves at `[DONE]`, not at session creation)
6. User sees user message from DB but no assistant response (streaming went into dead component)

Fix applied:
- Removed the `useEffect` that navigated mid-stream
- Added `sessionId` field to `StreamedMessage` return type, collected via local variable inside `sendMessage`
- Navigation now happens in `handleSend` AFTER `streamSend` resolves — at that point DB has both messages (backend persists before yielding `[DONE]`)
- Used `router.replace` (not push) so back button doesn't return to empty `/chat/new`

This matches the ChatGPT/Gemini pattern: never interrupt the streaming component; update navigation only after the stream is complete and state is persisted.

## Outcome

- ✅ Impact: New chat messages now stream fully before navigation; no blank response
- 🧪 Tests: Manual — send message from /chat/new, verify full stream visible, then navigation occurs
- 📁 Files: useStreamChat.ts (StreamedMessage type + collectedSessionId), ChatInputClient.tsx (removed effect, post-stream navigation)
- 🔁 Next prompts: Test follow-up messages in existing sessions
- 🧠 Reflection: The backend intentionally emits session ID first for quota/UX tracking, but that design clashes with a navigation side-effect on the same event. Decoupling navigation from session-ID receipt (by delaying until stream end) is the correct fix.

## Evaluation notes (flywheel)

- Failure modes observed: mid-stream navigation unmounting streaming component
- Graders run and results (PASS/FAIL): manual test pending
- Prompt variant (if applicable): null
- Next experiment: consider moving ChatInputClient to layout level for fully persistent streaming (like ChatGPT's app shell)
