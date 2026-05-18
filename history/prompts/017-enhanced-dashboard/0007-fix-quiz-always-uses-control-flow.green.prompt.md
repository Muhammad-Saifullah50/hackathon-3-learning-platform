---
id: "0007"
title: Fix Quiz Always Uses Control Flow Topic
stage: green
date: 2026-05-18
surface: agent
model: claude-sonnet-4-6
feature: 017-enhanced-dashboard
branch: 017-enhanced-dashboard
user: Muhammad
command: chat
labels: ["bug-fix", "quiz", "topic-inference", "agents"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - backend/src/api/v1/agents.py
tests:
  - manual: quiz after a concept explanation now uses the discussed topic
---

## Prompt

there is another bug,

what is fastmcp library ?
[agent responds about FastMCP]
quiz me on this topic
[quiz shows "Quiz: If-Else Statements / control_flow" instead of FastMCP/libraries]

why does this always quiz me on control flow

## Response snapshot

Root cause: when user says "quiz me on this topic", the frontend sends no `topic` field to the backend. The backend passed `topic=None` to the quiz agent. With no topic hint, the LLM defaulted to `control_flow`.

Fix in `backend/src/api/v1/agents.py`: when quiz agent is selected and `request.topic` is None, walk backwards through the session's conversation history to find the most recent previous user message and use it as the inferred topic context. That inferred topic is set in `LearnFlowContext` (used by the system prompt's `topic_hint`) AND appended to the agent input with a `[Context: ...]` annotation.

## Outcome

- ✅ Impact: Quiz agent now picks topic from conversation history when none is explicitly provided
- 🧪 Tests: Manual — quiz after FastMCP discussion should produce a libraries/MCP quiz, not control_flow
- 📁 Files: backend/src/api/v1/agents.py (topic inference block + agent_input enrichment)
- 🔁 Next prompts: test the fix end-to-end
- 🧠 Reflection: The frontend could also be improved to pass the active module/topic, but the backend inference is the minimal fix

## Evaluation notes (flywheel)

- Failure modes observed: LLM defaulted to control_flow when no topic context given
- Graders run and results (PASS/FAIL): manual only
- Prompt variant (if applicable): null
- Next experiment: have frontend pass the module_slug of the currently-viewed module as topic
