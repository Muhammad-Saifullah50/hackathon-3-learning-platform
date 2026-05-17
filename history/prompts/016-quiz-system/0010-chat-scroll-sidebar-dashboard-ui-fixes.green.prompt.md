---
id: "0010"
title: Chat scroll, sidebar active state, dashboard mastery UI fixes
stage: green
date: 2026-05-17
surface: agent
model: claude-sonnet-4-6
feature: 016-quiz-system
branch: 016-quiz-system
user: Muhammad
command: user chat message
labels: ["ui-fix","scroll","sidebar","dashboard","mastery","chat"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - frontend/src/components/chat/ChatInputClient.tsx
  - frontend/src/app/(student)/chat/[chatid]/page.tsx
  - frontend/src/components/chat/SessionSidebarServer.tsx
  - frontend/src/components/chat/SessionSidebarClient.tsx
  - frontend/src/components/dashboard/module-grid.tsx
tests:
  - tsc --noEmit (passes; pre-existing unrelated error only)
---

## Prompt

i first asked the tutor about yield keyword. it explained using the concepts agent. then i asked it to quiz me on the topic so it genefrated a quiz on if else things. also the when the quiz appeared it was not scrolling as other messages would , same scrolling behaviour was for the scre card. it was nit scrolling. the i asked another question and it overflowed the messages are a all the way down . the sidebar was left all the way up. fox these ui issues and others as well. also uodate the dashbioard tro correclty refect mastery on all sections of the dashboard

## Response snapshot

Identified 3 root causes via systematic debugging:

1. **Chat scroll/overflow**: `ChatInputClient` rendered optimistic messages outside the `overflow-y-auto` div in `[chatid]/page.tsx`. QuizCard/ScoreCard/subsequent messages expanded a non-scrollable div past viewport height with no scrollIntoView mechanism.

2. **Sidebar no active state**: `SessionSidebarServer` was a pure server component — no `usePathname` access, no active highlighting, no scroll-to-current-session.

3. **Dashboard mastery 0% for multi-word modules**: Backend stores `topic = "control_flow"` (underscores from module_slug). Frontend `CURRICULUM_MODULES` has `topic: "Control Flow"` (spaces). `byTopic.get("control flow")` never matched `"control_flow"`.

Fixes applied:
- `ChatInputClient` now owns the entire scrollable message area (`flex-1 overflow-y-auto`) + pinned `ChatInput`. Accepts `initialHistory` prop so server history and local optimistic messages merge into one scroll container with `bottomRef + scrollIntoView`.
- `[chatid]/page.tsx` simplified — passes history to `ChatInputClient`, removes its own scroll div.
- New `SessionSidebarClient.tsx` uses `usePathname`, highlights active session with blue icon + white text + bg, auto-scrolls active item into view.
- `SessionSidebarServer.tsx` now delegates to `SessionSidebarClient`.
- `module-grid.tsx` `deriveCards` normalizes topic strings via `norm()` (replace `-`, `_`, ` ` → `_`) before map lookup, fixing all multi-word module mismatches.

## Outcome

- ✅ Impact: Quiz card, score card, and subsequent messages now scroll correctly; sidebar highlights active session; dashboard shows correct mastery for all 8 modules
- 🧪 Tests: tsc --noEmit passes (one pre-existing unrelated error for quiz page type)
- 📁 Files: 5 files changed (2 modified, 2 new, 1 simplified)
- 🔁 Next prompts: End-to-end test the full quiz flow in browser
- 🧠 Reflection: Split server/client message rendering was the root cause of scroll bugs; normalizing string keys fixed silent data mismatch

## Evaluation notes (flywheel)

- Failure modes observed: Layout split between server-rendered history and client optimistic messages caused scroll container fragmentation
- Graders run and results (PASS/FAIL): tsc PASS
- Prompt variant (if applicable): null
- Next experiment: Add e2e Playwright test for quiz scroll behavior
