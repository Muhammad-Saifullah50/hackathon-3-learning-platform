---
id: "0010"
title: Fix Recommendations Panel Hydration Mismatch
stage: green
date: 2026-05-19
surface: agent
model: claude-sonnet-4-6
feature: 018-teacher-dashboard
branch: 018-teacher-dashboard
user: Muhammad
command: fix hydration error in recommendations panel
labels: ["hydration", "ssr", "sessionStorage", "react", "bugfix"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - frontend/src/hooks/use-recommendations-stream.ts
tests:
  - manual browser verification (no hydration error in console)
---

## Prompt

corrcet this ## Error Type
Recoverable Error

## Error Message
Hydration failed because the server rendered HTML didn't match the client. As a result this tree will be regenerated on the client. This can happen if a SSR-ed Client Component used:

- A server/client branch `if (typeof window !== 'undefined')`.
- Variable input such as `Date.now()` or `Math.random()` which changes each time it's called.
- Date formatting in a user's locale which doesn't match the server.
- External changing data without sending a snapshot of it along with the HTML.
- Invalid HTML tag nesting.

...at RecommendationsPanel (src/components/dashboard/recommendations-panel.tsx:42:11)

## Response snapshot

Root cause: `use-recommendations-stream.ts` called `readCache()` (which reads `sessionStorage`) during initial render to compute `hasFreshCache`, then passed the result as the initial value to `useState`. On the server, `sessionStorage` doesn't exist so `hasFreshCache = false` → `state='idle'`, `recommendations=[]`. On the client, a cache hit could produce `state='loaded'` with data — causing a mismatch.

Fix: Always initialize `useState` with `[]` and `'idle'` (matching server), then check the cache inside a `useEffect` after mount (client-only). If a fresh cache entry exists, update state there; otherwise call `open()` to start the fetch stream. Also removed unused `url` variable that was a leftover.

## Outcome

- ✅ Impact: Eliminates the React hydration mismatch error in the dashboard; SSR output now consistently matches client initial render
- 🧪 Tests: Manual — load the dashboard and confirm no hydration warning in the browser console
- 📁 Files: frontend/src/hooks/use-recommendations-stream.ts
- 🔁 Next prompts: Continue 015-ai-tutor-chat T022 SessionSidebar or other pending tasks
- 🧠 Reflection: Classic SSR pitfall — browser-only APIs (sessionStorage, localStorage) must never be called during the render phase of a component or hook; always defer to useEffect

## Evaluation notes (flywheel)

- Failure modes observed: sessionStorage read during render phase causing server/client state divergence
- Graders run and results (PASS/FAIL): n/a
- Prompt variant (if applicable): n/a
- Next experiment (smallest change to try): n/a
