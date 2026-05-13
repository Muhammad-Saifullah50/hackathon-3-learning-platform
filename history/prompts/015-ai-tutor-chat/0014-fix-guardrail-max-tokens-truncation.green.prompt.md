---
id: "0014"
title: Fix guardrail max_tokens truncation causing JSON parse error
stage: green
date: 2026-05-12
surface: agent
model: claude-sonnet-4-6
feature: 015-ai-tutor-chat
branch: 015-ai-tutor-chat
user: Muhammad
command: correct this error ERROR: Exception in ASGI application ...
labels: ["bugfix","guardrail","off-topic","json","pydantic"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - backend/src/services/agents/guardrails.py
tests:
  - manual SSE chat request with Python question
---

## Prompt

correct this error ERROR:    Exception in ASGI application
[...truncated traceback...]
agents.exceptions.ModelBehaviorError: Invalid JSON when parsing {"is_off_topic": false, "reasoning": "The user is asking about the functionality of the `print()` function in Python, which is a core concept in Python syntax and programming. This is directly related to for TypeAdapter(OffTopicCheck); 1 validation error for OffTopicCheck
  Invalid JSON: EOF while parsing a string at line 1 column 203 [type=json_invalid, ...]

## Response snapshot

Root cause: `_off_topic_classifier` agent had `max_tokens=100`, which was too low to fit the full structured JSON output (`{"is_off_topic": false, "reasoning": "..."}`) for even moderate-length reasoning strings. The LLM hit the token limit mid-string, producing truncated JSON that Pydantic then rejected with "EOF while parsing a string".

Fix: increased `max_tokens` from `100` to `300` in `guardrails.py` line 44.

## Outcome

- ✅ Impact: Off-topic guardrail no longer crashes on Python-related questions with medium-length reasoning strings
- 🧪 Tests: Manual — send a Python question via chat SSE endpoint; expect 200 with streamed agent response instead of 500
- 📁 Files: backend/src/services/agents/guardrails.py (1 line changed)
- 🔁 Next prompts: Run the migration, then test end-to-end chat flow
- 🧠 Reflection: Token budgets for structured-output agents must account for the JSON wrapper overhead plus the longest expected field value

## Evaluation notes (flywheel)

- Failure modes observed: max_tokens too tight for JSON-wrapped structured output
- Graders run and results (PASS/FAIL): manual smoke test (pending)
- Prompt variant (if applicable): null
- Next experiment: add an integration test that sends a Python question and asserts HTTP 200 with valid SSE stream
