---
id: "0001"
title: specify-015-chat-interface-spec
stage: spec
date: 2026-05-11
surface: agent
model: claude-sonnet-4-6
feature: 015-ai-tutor-chat
branch: 015-ai-tutor-chat
user: Muhammad
command: /sp.specify 015-chat-interface
labels: ["chat", "ai-tutor", "streaming", "triage-agent", "guardrails", "spec"]
links:
  spec: specs/015-ai-tutor-chat/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/015-ai-tutor-chat/spec.md
  - specs/015-ai-tutor-chat/checklists/requirements.md
  - CLAUDE.md
tests:
  - null
---

## Prompt

ok, so now I have to build feature 15 from the FEATURES.md file. Go through that feature, and then we will write the specifications after discussing it.

[Discussion followed — user confirmed:]
- Both standalone /chat page and embedded panel in code editor
- Database-persisted chat history
- Fix backend SSE streaming (OpenAI Agents SDK native streaming)
- Last 5 messages as conversation history context
- Context includes: current code, execution output, current lesson/module, mastery level
- Standalone /chat is general — no required lesson context, but Python-only guardrails
- No teacher access
- Triage Agent routes every message to specialist agents (Concepts / Debug / Exercise / Code Review / Progress)

Also: "mark F14 as complete in CLAUDE.md"

## Response snapshot

Created feature branch `015-ai-tutor-chat` and wrote spec at `specs/015-ai-tutor-chat/spec.md`.

Spec covers:
- 4 user stories: standalone chat (P1), embedded debug panel (P2), off-topic guardrail (P3), exercise request (P3)
- 19 functional requirements across chat core, agent routing, context, guardrails, and input constraints
- 3 key entities: Chat Session, Chat Message, Agent Routing Decision
- 7 measurable success criteria (streaming latency, routing accuracy, guardrail coverage, history durability)
- Edge cases: network failure, empty input, oversized code context, DB save failure, long messages
- Assumptions: streaming fix in scope, F14 exposes editor state via shared context, one session per student
- Out of scope: teacher access, multi-modal, export, F22 notifications

CLAUDE.md updated to mark F13 and F14 complete.

## Outcome

- ✅ Impact: Full feature specification created for F15 Chat Interface with AI Tutor
- 🧪 Tests: No tests run (spec phase)
- 📁 Files: specs/015-ai-tutor-chat/spec.md, specs/015-ai-tutor-chat/checklists/requirements.md, CLAUDE.md
- 🔁 Next prompts: /sp.plan 015-ai-tutor-chat, /sp.tasks 015-ai-tutor-chat
- 🧠 Reflection: Triage → specialist agent routing is a critical architectural detail that must be captured in plan.md; streaming fix is a prerequisite backend task that should be its own task in tasks.md

## Evaluation notes (flywheel)

- Failure modes observed: none
- Graders run and results (PASS/FAIL): checklist validation — all items PASS
- Prompt variant (if applicable): null
- Next experiment: null
