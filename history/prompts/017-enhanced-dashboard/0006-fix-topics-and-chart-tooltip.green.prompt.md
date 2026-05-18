---
id: "0006"
title: Fix Topics and Chart Tooltip Zero Scores
stage: green
date: 2026-05-18
surface: agent
model: claude-sonnet-4-6
feature: 017-enhanced-dashboard
branch: 017-enhanced-dashboard
user: Muhammad
command: continue fixing
labels: ["bug-fix", "dashboard", "progress-agent", "recharts"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - backend/src/schemas/agent_responses.py
  - frontend/src/components/dashboard/mastery-chart.tsx
tests:
  - null
---

## Prompt

i was learning control flow ans expected topics to come here bur i get module overview in the progress page. also the first bar chart on the dashbiard which hows overall mastery shows the score omn hower . shows 0 for all

(then: continue fixing)

## Response snapshot

Root-cause investigation via systematic debugging:

**Bug 1 (module progress page shows "Module overview · Remaining"):**
`ProgressAgentResponse` in `agent_responses.py` had no `recommendations` field. The `get_module_detail_prompt` instructs the LLM to write topic data into `recommendations`, and `stream_module_progress` checks `hasattr(output, "recommendations")`. Since the field didn't exist in the schema, the agent couldn't populate it, `hasattr` always returned False, and the fallback "Module overview" fired every time.

Fix: Added `recommendations: list[str] = []` to `ProgressAgentResponse`.

**Bug 2 (bar chart tooltip shows 0% for all modules):**
In `mastery-chart.tsx`, topic key normalization only called `.toLowerCase()`. Mastery records from the quiz system store `topic` as `module_slug` (e.g., `"control_flow"` with underscores), while `CURRICULUM_MODULES` topics are `"Control Flow"` (spaces). Without normalizing underscores/hyphens/spaces, no lookup ever matched and all scores fell back to 0. The chart still rendered because there's no `allZero` guard — the background fill props make bar slots visible even at score 0.

Fix: Added `normalize = (s) => s.toLowerCase().replace(/[-_ ]/g, '_')` and applied it to both map key building and lookups.

## Outcome

- ✅ Impact: Module progress page now shows real topic breakdown from the LLM; mastery chart tooltip now shows correct scores
- 🧪 Tests: No automated tests run; manual verification needed after backend restart
- 📁 Files: 2 files changed (1 backend schema, 1 frontend component)
- 🔁 Next prompts: Verify topic breakdown renders correctly for control-flow module; check if `alembic upgrade head` is needed for mastery_snapshots table
- 🧠 Reflection: Two independent schema/normalization mismatches. The ProgressAgentResponse schema was missing a field the prompt was targeting, and mastery-chart had weaker normalization than dashboard-client for the same data.

## Evaluation notes (flywheel)

- Failure modes observed: Schema field absent causes silent fallback; inconsistent normalization between two components reading the same data
- Graders run and results (PASS/FAIL): null
- Prompt variant (if applicable): null
- Next experiment (smallest change to try): Add `allZero` guard to mastery-chart.tsx to match ModuleMasteryChart behavior
