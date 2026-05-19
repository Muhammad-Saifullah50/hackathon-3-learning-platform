---
id: "0009"
title: Fix Recommendations Progress Fingerprint Cache
stage: green
date: 2026-05-19
surface: agent
model: claude-sonnet-4-6
feature: 018-teacher-dashboard
branch: 018-teacher-dashboard
user: Muhammad
command: chat
labels: ["bugfix","dashboard","recommendations","caching","student"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - frontend/src/hooks/use-recommendations-stream.ts
  - frontend/src/components/dashboard/recommendations-panel.tsx
  - frontend/src/components/dashboard/dashboard-client.tsx
tests:
  - null
---

## Prompt

there is a problem with the student dashboard. It is that whenever the student refreshes the dashboard, a call goes to the recommendations agent. how should we fix that?

(follow-up) it should regenerate recommendations only if student has made some new progress. what is your take on that?

(follow-up) yes [implement it]

## Response snapshot

Implemented progress-fingerprint-based caching for the recommendations panel:

1. `use-recommendations-stream.ts` — added `sessionStorage` cache keyed by `progressKey`. On mount, reads cache; only fetches from agent if fingerprint differs. Writes cache on stream completion (both `done` event and natural stream end).
2. `recommendations-panel.tsx` — added `progressKey` prop, forwarded to hook.
3. `dashboard-client.tsx` — computes fingerprint as `overall_mastery|topic:score,...` from live progress data and passes it to `RecommendationsPanel`.

## Outcome

- ✅ Impact: Recommendations agent is no longer called on every page refresh; only fires when `overall_mastery` or any topic score changes.
- 🧪 Tests: TypeScript check passed (no errors in changed files).
- 📁 Files: 3 frontend files modified.
- 🔁 Next prompts: Could invalidate cache on explicit logout; could extend fingerprint to include streak if desired.
- 🧠 Reflection: sessionStorage is naturally scoped to the browser tab session, so the cache clears on tab close — a good default that avoids stale data across login sessions.

## Evaluation notes (flywheel)

- Failure modes observed: none
- Graders run and results (PASS/FAIL): tsc --noEmit PASS
- Prompt variant (if applicable): null
- Next experiment (smallest change to try): include streak days in fingerprint if streak-based recommendations are added
