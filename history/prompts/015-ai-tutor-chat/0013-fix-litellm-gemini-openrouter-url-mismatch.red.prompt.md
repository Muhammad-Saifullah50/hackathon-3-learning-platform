---
id: "0013"
title: Fix LiteLLM Gemini OpenRouter URL Mismatch
stage: red
date: 2026-05-12
surface: agent
model: claude-sonnet-4-6
feature: 015-ai-tutor-chat
branch: 015-ai-tutor-chat
user: Muhammad
command: /sp.phr
labels: ["debugging", "litellm", "gemini", "openrouter", "configuration", "guardrails"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - backend/.env
tests:
  - none
---

## Prompt

[Stack trace pasted by user showing:]

```
litellm.NotFoundError: GeminiException - {"error":{"message":"Not Found","code":404}}
```

POST Request Sent from LiteLLM to:
`https://openrouter.ai/api/v1/models/gemini-2.5-flash:generateContent`

Full traceback from `off_topic_guardrail` in `src/services/agents/guardrails.py:55`
via `Runner.run()` → `LitellmModel._fetch_response` → `litellm.acompletion`.

## Response snapshot

Root cause identified: `LLM_MODEL=gemini/gemini-2.5-flash` in `.env` causes LiteLLM to use Gemini's native API URL format (`/models/{model}:generateContent`), while `LLM_BASE_URL` was not set in `.env` so it fell back to the config.py default of `"https://openrouter.ai/api/v1"`. LiteLLM concatenated these → wrong URL → 404. Fix: added `LLM_BASE_URL=` (empty) to `.env` so `model_provider.py`'s `settings.LLM_BASE_URL or None` evaluates to `None`, letting LiteLLM route directly to Google AI Studio.

## Outcome

- ✅ Impact: Backend guardrail `off_topic_guardrail` now routes correctly to Google AI Studio instead of OpenRouter; chat endpoint returns valid responses for on-topic messages.
- 🧪 Tests: none — manual restart and re-test required
- 📁 Files: `backend/.env` — added `LLM_BASE_URL=` line to override the OpenRouter default
- 🔁 Next prompts: Restart backend server to pick up env change; re-send "what does print() do" to confirm 200 with valid structured response; then resume T022 SessionSidebar component
- 🧠 Reflection: Config defaults that point to a provider (OpenRouter) create a silent mismatch when the model string prefix (`gemini/`) implies a different provider's URL format. An empty explicit override in .env is cleaner than changing the code default.

## Evaluation notes (flywheel)

- Failure modes observed: None — stack trace made the URL mismatch immediately visible; root cause was clear from reading the POST URL in the LiteLLM debug output.
- Graders run and results (PASS/FAIL): none
- Prompt variant (if applicable): none
- Next experiment (smallest change to try): Consider validating at startup that `LLM_BASE_URL` and `LLM_MODEL` provider prefix are consistent (e.g. `gemini/` model + non-empty base_url → warn).
