---
id: "0018"
title: Increase chat limit to 15
stage: green
date: 2026-05-13
surface: agent
model: claude-sonnet-4-6
feature: 015-ai-tutor-chat
branch: 015-ai-tutor-chat
user: Muhammad
command: /sp.phr
labels: ["chat-quota", "ui", "frontend", "daily-limit"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - frontend/src/components/chat/ChatInput.tsx
tests:
  - none
---

## Prompt

increease the chat limit shows 5 right now

## Response snapshot

Found that the backend already had `DAILY_LIMIT = 15` in `chat_quota_service.py`, but the frontend `ChatInput.tsx` had the value hardcoded as 5 in two places (the exhausted message and the quota badge). Updated both occurrences to 15 to match the backend.

## Outcome

- ✅ Impact: Chat quota display now correctly shows 15 messages/day, matching the backend `DAILY_LIMIT = 15` constant.
- 🧪 Tests: none
- 📁 Files: frontend/src/components/chat/ChatInput.tsx (lines 45 and 84-86)
- 🔁 Next prompts: Continue with T022 SessionSidebar or T023 full /chat page
- 🧠 Reflection: Frontend and backend quota constants were out of sync; backend was already correct at 15 — only the UI display strings needed updating.

## Evaluation notes (flywheel)

- Failure modes observed: None — straightforward hardcoded string fix.
- Graders run and results (PASS/FAIL): none
- Prompt variant (if applicable): none
- Next experiment (smallest change to try): Consider deriving the displayed limit from the quota API response (`data.daily_limit`) rather than hardcoding it in the frontend, so they can never drift apart again.
