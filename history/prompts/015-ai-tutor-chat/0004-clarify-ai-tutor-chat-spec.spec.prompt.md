---
id: "0004"
title: Clarify AI Tutor Chat Spec
stage: spec
date: 2026-05-11
surface: agent
model: claude-sonnet-4-6
feature: 015-ai-tutor-chat
branch: 015-ai-tutor-chat
user: Muhammad
command: /sp.clarify
labels: ["clarification", "chat", "spec", "streaming", "rate-limit", "sessions", "accessibility"]
links:
  spec: specs/015-ai-tutor-chat/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/015-ai-tutor-chat/spec.md
tests:
  - null
---

## Prompt

/sp.clarify (no additional user input — invoked on 015-ai-tutor-chat spec)

## Response snapshot

Ran structured ambiguity scan across all taxonomy categories on the chat spec. Asked 5 targeted questions sequentially:

1. Streaming transport → SSE (A)
2. Per-student rate limit → 5 messages per day
3. Session model → multiple sessions, all saved
4. Quota storage → Database / Neon PostgreSQL (A)
5. Accessibility → Basic ARIA + Enter-to-send + aria-live (A)

Updated spec with: FR-003 (SSE), FR-020 (5/day quota), FR-007a/b (session list + new chat), FR-021 (accessibility), Chat Quota entity, corrected Assumptions section, and Clarifications section.

## Outcome

- ✅ Impact: 5 critical ambiguities resolved; spec now unambiguous enough to proceed to /sp.plan
- 🧪 Tests: none run (clarification session)
- 📁 Files: specs/015-ai-tutor-chat/spec.md
- 🔁 Next prompts: /sp.plan
- 🧠 Reflection: Rate limit of 5/day is very tight for a learning platform — worth flagging during planning to confirm this is intentional cost control

## Evaluation notes (flywheel)

- Failure modes observed: none
- Graders run and results (PASS/FAIL): none
- Prompt variant (if applicable): null
- Next experiment (smallest change to try): null
