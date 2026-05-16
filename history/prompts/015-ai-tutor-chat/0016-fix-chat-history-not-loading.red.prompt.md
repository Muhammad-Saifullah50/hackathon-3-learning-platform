---
id: "0016"
title: Fix chat history not loading on session click
stage: red
date: 2026-05-13
surface: agent
model: claude-sonnet-4-6
feature: 015-ai-tutor-chat
branch: 015-ai-tutor-chat
user: Muhammad
command: user message
labels: ["bug", "persistence", "sse", "streaming", "conversation-history", "agent-sessions"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - backend/src/api/v1/agents.py
  - backend/src/repositories/agent_session_repository.py
  - backend/src/schemas/agents.py
  - backend/src/services/agents/hooks.py
tests:
  - none
---

## Prompt

i am unable to retrieve my previous messaghes wheni click on a specific chat

## Response snapshot

Diagnosed and fixed two bugs: (1) assistant messages were never persisted to the DB because `_generate()` saved after yielding `[DONE]` — when the client disconnects on receiving `[DONE]`, that final `__anext__()` call may be skipped; (2) `on_agent_end` hook was saving `str(output)` (Python repr, not JSON). Fix: inlined the streaming generator so the assistant message is saved BEFORE yielding `[DONE]`, added `agent_type` to stored messages, updated `ConversationMessage` schema to include `agent_type`, removed duplicate save from `on_agent_end`.

## Outcome

- ✅ Impact: Assistant responses are now persisted to DB before the SSE stream closes; agent_type is stored and returned for badge display on reload
- 🧪 Tests: none run (manual verification required against live server)
- 📁 Files: agents.py, agent_session_repository.py, schemas/agents.py, hooks.py
- 🔁 Next prompts: Restart backend server and test by sending a message, navigating away, clicking back on the session
- 🧠 Reflection: Async generator persistence after final yield is unreliable when the client disconnects; always persist side effects BEFORE the last yield in a streaming endpoint

## Evaluation notes (flywheel)

- Failure modes observed: Root cause was subtle — saving after the final `yield` in an async generator is not guaranteed when client disconnects after `[DONE]`. The `on_agent_end` hook also saved wrong format (Python repr instead of JSON), causing a separate duplicate-but-incorrect save path.
- Graders run and results (PASS/FAIL): none
- Prompt variant (if applicable): none
- Next experiment (smallest change to try): Add backend logging to confirm `add_message_to_history` completes successfully and check session row after a chat turn
