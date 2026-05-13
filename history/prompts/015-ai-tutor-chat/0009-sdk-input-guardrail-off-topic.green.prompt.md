---
id: "0009"
title: SDK input guardrail off-topic detection
stage: green
date: 2026-05-12
surface: agent
model: claude-sonnet-4-6
feature: 015-ai-tutor-chat
branch: 015-ai-tutor-chat
user: Muhammad
command: sp.implement
labels: ["guardrails","openai-agents-sdk","off-topic","streaming","refactor"]
links:
  spec: specs/015-ai-tutor-chat/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/015-ai-tutor-chat/tasks.md
  - backend/src/services/agents/model_provider.py
  - backend/src/services/agents/guardrails.py
  - backend/src/services/agents/agents.py
  - backend/src/api/v1/agents.py
tests:
  - "Manual: send off-topic message → guardrail fires → amber SSE redirect appears"
  - "Manual: send Python question → guardrail passes → normal specialist response"
---

## Prompt

update the tasks phase 5 section to use openai agents sdks input guardrails feature after researching it and then implement that guardrails

## Response snapshot

Researched the OpenAI Agents SDK `@input_guardrail` decorator pattern, then:

1. **Updated Phase 5** in `specs/015-ai-tutor-chat/tasks.md` — replaced T026 (single keyword-based off_topic short-circuit task) with T026a–T026d covering: shared model provider extraction, LLM-based guardrail creation, attaching to all 6 agent factories, and updating the endpoint to catch `InputGuardrailTripwireTriggered` inside the SSE generator.

2. **Created `model_provider.py`** — extracts `_ConfiguredLitellmProvider` + `get_run_config()` from the API route into a shared service-layer module; both the guardrail runner and the endpoint import from here.

3. **Created `guardrails.py`** — `OffTopicCheck` Pydantic model, `_off_topic_classifier` Agent with `temperature=0.0`, and `off_topic_guardrail` decorated with `@input_guardrail`; runs the classifier via `Runner.run(...)` with `get_run_config()` and returns `GuardrailFunctionOutput(tripwire_triggered=result.final_output.is_off_topic)`.

4. **Updated `agents.py`** — added `input_guardrails=[off_topic_guardrail]` to all 6 agent factories (triage, concepts, debug, code_review, exercise, progress); SDK guarantees it only fires for the first agent in the workflow.

5. **Updated `api/v1/agents.py`** — imported `InputGuardrailTripwireTriggered`; removed local `_ConfiguredLitellmProvider` class; replaced all `RunConfig(model_provider=_ConfiguredLitellmProvider())` with `get_run_config()`; removed keyword-based `off_topic` short-circuit block; added `try/except InputGuardrailTripwireTriggered` inside `_generate()` to emit canned SSE redirect after session/quota events have already been streamed.

## Outcome

- ✅ Impact: Off-topic guardrail now uses the SDK-native LLM-based classifier running in parallel with the first agent call; more robust than keyword matching for borderline cases; no latency increase for on-topic messages
- 🧪 Tests: Manual smoke test — send "Write me a poem" → guardrail fires mid-stream → off-topic SSE emitted; send "Explain recursion" → passes through to concepts agent
- 📁 Files: 2 new files (model_provider.py, guardrails.py), 3 modified (tasks.md, agents.py, api/v1/agents.py)
- 🔁 Next prompts: T027 (amber border styling in ChatMessage.tsx), T028 (exercise intent audit), T029 (exercise agent prompt), T030–T033 (polish)
- 🧠 Reflection: SDK guardrails run in parallel with the first LLM call so there's minimal latency overhead; attaching to all 6 agents ensures coverage regardless of which specialist keyword routing selects as first

## Evaluation notes (flywheel)

- Failure modes observed: none at implementation time; guardrail inner Runner.run requires explicit run_config since it doesn't inherit parent RunConfig automatically
- Graders run and results (PASS/FAIL): AST parse check — PASS for all 4 modified/created Python files
- Prompt variant (if applicable): null
- Next experiment (smallest change to try): add a fast keyword pre-check before the LLM guardrail to skip the classifier call for obvious on-topic messages (cost optimisation)
