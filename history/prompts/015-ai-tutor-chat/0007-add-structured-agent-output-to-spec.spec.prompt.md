---
id: "0007"
title: Add Structured Agent Output to Spec
stage: spec
date: 2026-05-11
surface: agent
model: claude-sonnet-4-6
feature: 015-ai-tutor-chat
branch: 015-ai-tutor-chat
user: Muhammad
command: /sp.specify (amendment)
labels: ["spec", "structured-output", "output-type", "send-to-editor", "pydantic", "openai-agents"]
links:
  spec: specs/015-ai-tutor-chat/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/015-ai-tutor-chat/spec.md
  - specs/015-ai-tutor-chat/research.md
  - specs/015-ai-tutor-chat/data-model.md
  - specs/015-ai-tutor-chat/contracts/chat-api.yaml
  - specs/015-ai-tutor-chat/tasks.md
tests:
  - none (spec amendment)
---

## Prompt

add to the spec that the agent will output will generate structured output using openai-agents features to render ui correctly, for codeblocks, code in embedded editor, exercises etc

## Response snapshot

Amended spec.md and all downstream artifacts (research.md, data-model.md, contracts/chat-api.yaml, tasks.md) to add structured agent output via OpenAI Agents SDK `output_type`:

**New FR-022 to FR-027 added to spec.md**:
- FR-022: Each specialist agent returns a typed Pydantic response via `output_type`
- FR-023: Backend streams text tokens then emits `event: structured` SSE with full JSON
- FR-024: Responses with `send_to_editor` field display "Load in Editor" button
- FR-025: ExerciseResponse with structured title/description/difficulty/starter_code; starter always has "Load Starter Code in Editor"
- FR-026: DebugResponse with error_identified, hint, optional fix_code + "Apply Fix in Editor"
- FR-027: CodeReviewResponse with score, issues list, optional improved_code + "Load Improved Code in Editor"

**New Key Entities**: CodeBlock, ConceptResponse, DebugResponse, ExerciseResponse, CodeReviewResponse, ProgressResponse

**New SC-008, SC-009**: 100% structured payload coverage; single-click editor loading for all 3 agent types

**New tasks**: T005b (define Pydantic response schemas), T010b (wire output_type to each agent factory)

**Updated tasks**: T011 stores structured JSON in history; T015 (useStreamChat) handles `event: structured`; T019 (ChatMessage) renders 5 card variants; T024 (TutorPanel) wires "Load in Editor" to Monaco model.setValue(); T025 passes editorRef

## Outcome

- ✅ Impact: All planning artifacts updated; structured output is now a first-class requirement with typed schemas for all 5 specialist agents
- 🧪 Tests: No tests (spec phase)
- 📁 Files: 5 artifacts updated
- 🔁 Next prompts: /sp.implement or begin T001 implementation
- 🧠 Reflection: Structured output eliminates brittle markdown parsing; the `send_to_editor` convention is a clean abstraction that works identically across standalone and embedded surfaces (navigation vs. model.setValue())

## Evaluation notes (flywheel)

- Failure modes observed: none
- Graders run and results (PASS/FAIL): N/A
- Prompt variant (if applicable): null
- Next experiment (smallest change to try): Implement T005b (agent_responses.py schemas) first to validate the Pydantic models compile correctly before wiring to agents
