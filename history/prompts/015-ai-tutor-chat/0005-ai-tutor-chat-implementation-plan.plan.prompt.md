---
id: "0005"
title: AI Tutor Chat Implementation Plan
stage: plan
date: 2026-05-11
surface: agent
model: claude-sonnet-4-6
feature: 015-ai-tutor-chat
branch: 015-ai-tutor-chat
user: Muhammad
command: /sp.plan
labels: ["chat", "streaming", "sse", "agent-routing", "quota", "sessions", "frontend", "backend"]
links:
  spec: specs/015-ai-tutor-chat/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/015-ai-tutor-chat/plan.md
  - specs/015-ai-tutor-chat/research.md
  - specs/015-ai-tutor-chat/data-model.md
  - specs/015-ai-tutor-chat/quickstart.md
  - specs/015-ai-tutor-chat/contracts/chat-api.yaml
tests:
  - none (planning phase)
---

## Prompt

/sp.plan (no additional user input)

## Response snapshot

Executed full `/sp.plan` workflow for feature 015-ai-tutor-chat (Chat Interface with AI Tutor). Generated all Phase 0 and Phase 1 artifacts:

**Key decisions made:**
1. SSE streaming: Keep `Runner.run` + word-drip SSE generator (workaround for openai-agents-python#601); true streaming deferred until upstream fixed
2. Chat quota: Reuse `RateLimitCounter` with `{user_id}:chat:{date}` identifier (limit=5/day) — no new table needed
3. Session schema: Add `title TEXT` + `surface VARCHAR(20)` to `agent_sessions` via Alembic migration
4. Code block rendering: `react-markdown` + `react-syntax-highlighter` (Prism, Python only, dynamic import)
5. Off-topic guardrail: `off_topic` intent in triage + canned response, no specialist agent invoked
6. Session listing: `GET /agents/sessions` returns 20 most recent by `updated_at DESC`
7. Embedded panel context: Props from `CodeEditorPanel` to `TutorPanel` (code + lastOutput)

**Artifacts generated:**
- `plan.md` — Technical Context, Constitution Check (PASS), Project Structure
- `research.md` — 10 research decisions resolving all unknowns
- `data-model.md` — Modified `agent_sessions` entity + JSONB conversation schema + API response shapes + migration plan
- `contracts/chat-api.yaml` — OpenAPI 3.1 spec for POST /chat, GET /sessions, GET /sessions/{id}, GET /quota
- `quickstart.md` — Local dev setup, smoke tests, common issues

## Outcome

- ✅ Impact: Full architectural plan for F15 AI Tutor Chat; no code written yet; ready for /sp.tasks
- 🧪 Tests: No tests run (planning phase)
- 📁 Files: 5 artifacts created under specs/015-ai-tutor-chat/
- 🔁 Next prompts: /sp.tasks to generate implementation task list
- 🧠 Reflection: The existing F07 infrastructure (AgentSession, RoutingDecision, agent chat endpoint) provides a strong foundation; F15 is primarily a frontend build + thin backend additions (quota, session listing, schema extensions)

## Evaluation notes (flywheel)

- Failure modes observed: none
- Graders run and results (PASS/FAIL): N/A (planning phase)
- Prompt variant (if applicable): null
- Next experiment (smallest change to try): Run /sp.tasks to validate task breakdown matches the architectural plan
