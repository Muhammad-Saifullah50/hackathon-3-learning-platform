---
id: 0009
title: Fix chat always routing through triage agent
stage: red
date: 2026-05-11
surface: agent
model: claude-sonnet-4-6
feature: 014-interactive-code-editor
branch: 014-interactive-code-editor
user: Muhammad
command: chat
labels: ["bug", "agents", "routing", "code-review"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - backend/src/api/v1/agents.py
tests:
  - null
---

## Prompt

i asked for a review of muy code and i got this and no review. I think the request didnt go direclty to the code review agent. It should go directly to the code review agent and no handoffs are required here

## Response snapshot

Found the root cause: the `/chat` endpoint in `backend/src/api/v1/agents.py` (lines 140-181) classified the intent correctly via `classify_intent()` and stored `agent_name = "code_review"` in the session, but then **always started the runner with `get_triage_agent()`**, ignoring the classification. The triage agent then had to re-classify and perform a handoff, causing the extra round-trip.

Fix applied:
1. Added `get_progress_agent` to imports (was missing).
2. Replaced the hardcoded `get_triage_agent()` call with a dispatch map keyed on `agent_name`. When intent is classified as `code_review`, the runner now starts directly with `get_code_review_agent()` — no handoff needed.

## Outcome

- ✅ Impact: Code review requests via `/chat` now go directly to `code_review` agent; same for concepts, debug, exercise, and progress intents. Only truly ambiguous ("general") queries fall back to triage.
- 🧪 Tests: No automated tests changed; routing logic is covered by integration-level chat tests.
- 📁 Files: backend/src/api/v1/agents.py
- 🔁 Next prompts: Verify with a live code review request through `/chat`.
- 🧠 Reflection: The intent classification was already correct — the bug was that its output was never used to select the agent.

## Evaluation notes (flywheel)

- Failure modes observed: Triage agent doing redundant LLM call + handoff on every classified request.
- Graders run and results (PASS/FAIL): manual inspection PASS
- Prompt variant (if applicable): null
- Next experiment: Add a structured test that asserts `result.last_agent.name == "code_review"` when message contains "review".
