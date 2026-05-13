---
id: "0015"
title: Fix ExerciseAgentResponse Missing Fields
stage: red
date: 2026-05-13
surface: agent
model: claude-sonnet-4-6
feature: 015-ai-tutor-chat
branch: 015-ai-tutor-chat
user: Muhammad
command: /sp.phr
labels: ["exercise-agent", "pydantic", "structured-output", "bug-fix", "llm-prompt"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - backend/src/llm/prompts.py
  - backend/src/services/agents/agents.py
tests:
  - none
---

## Prompt

when i asked the aghent to quiz me i got this error. if this is due to ma max tioken restrivction remove it 
ERROR:    Exception in ASGI application
Traceback (most recent call last):
  File "...agents/util/_json.py", line 21, in validate_json
    validated = type_adapter.validate_json(json_str, experimental_allow_partial=partial_setting)
pydantic_core._pydantic_core.ValidationError: 3 validation errors for ExerciseAgentResponse
title
  Field required [type=missing, ...]
difficulty
  Field required [type=missing, ...]
starter_code
  Field required [type=missing, ...]

agents.exceptions.ModelBehaviorError: Invalid JSON when parsing {"description": "### Exercise: Mastering the `print()` Function\n\n..."} for TypeAdapter(ExerciseAgentResponse); 3 validation errors for ExerciseAgentResponse

## Response snapshot

Identified root cause: the Exercise Agent LLM was returning only a `description` field (embedding title, difficulty, and starter_code as markdown within it) instead of the required structured JSON. Fixed by rewriting `get_exercise_agent_prompt()` in `prompts.py` to explicitly enumerate all required fields and their types, and reinforcing in the dynamic instructions in `agents.py`. No token restriction was involved — this was a prompt engineering issue.

## Outcome

- ✅ Impact: Exercise agent now receives explicit field-by-field instructions; LLM will output `title`, `difficulty`, and `starter_code` as separate top-level JSON keys, resolving the ValidationError.
- 🧪 Tests: none — manual re-test by asking the agent to generate an exercise
- 📁 Files: backend/src/llm/prompts.py, backend/src/services/agents/agents.py
- 🔁 Next prompts: Restart backend and ask "quiz me on print()" to verify fix; consider adding a fallback/retry in the SSE generator for structured output failures
- 🧠 Reflection: When an LLM ignores a structured output schema and embeds all content in one field, the fix is almost always prompt-side: enumerate every required field explicitly with name, type, and "do NOT omit" emphasis.

## Evaluation notes (flywheel)

- Failure modes observed: LLM treated `ExerciseAgentResponse` as a free-text markdown document and stuffed everything into `description`, ignoring `title`, `difficulty`, and `starter_code` as separate fields. The original prompt didn't enumerate required fields explicitly.
- Graders run and results (PASS/FAIL): none — manual validation pending
- Prompt variant (if applicable): v2 — added explicit field enumeration with types and "CRITICAL: do NOT omit" guard
- Next experiment (smallest change to try): If the model still misbehaves, add a one-shot example JSON object to the prompt showing the exact expected structure.
