---
id: "0012"
title: Register GPT-OSS-120b Model Cost in LiteLLM
stage: green
date: 2026-05-12
surface: agent
model: claude-sonnet-4-6
feature: 015-ai-tutor-chat
branch: 015-ai-tutor-chat
user: Muhammad
command: add this model cost before the call to litellm
labels: ["litellm","model-cost","openrouter","config"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - backend/src/llm/client.py
  - backend/src/services/agents/model_provider.py
tests:
  - null
---

## Prompt

add this model cost before the call to litellm
litellm.model_cost["openai/gpt-oss-120b:free"] = {"max_tokens": 131072, "input_cost_per_token": 0, "output_cost_per_token": 0, "lite_llm_provider": "openrouter", "mode": "chat"}

## Response snapshot

Added the `litellm.model_cost` registration at module level in both litellm entry points:
- `backend/src/llm/client.py` — after `import litellm`, before `acompletion` is called
- `backend/src/services/agents/model_provider.py` — after adding `import litellm`, before `LitellmModel` is instantiated

## Outcome

- ✅ Impact: `openai/gpt-oss-120b:free` is now recognized by LiteLLM as a valid model with zero-cost tokens via OpenRouter
- 🧪 Tests: No tests changed; registration is idempotent module-level assignment
- 📁 Files: backend/src/llm/client.py, backend/src/services/agents/model_provider.py
- 🔁 Next prompts: None
- 🧠 Reflection: Registered in both call paths so the model is available regardless of which code path is taken

## Evaluation notes (flywheel)

- Failure modes observed: none
- Graders run and results (PASS/FAIL): n/a
- Prompt variant (if applicable): n/a
- Next experiment (smallest change to try): n/a
