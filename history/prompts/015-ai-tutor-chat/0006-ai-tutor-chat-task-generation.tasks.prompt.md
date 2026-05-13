---
id: "0006"
title: AI Tutor Chat Task Generation
stage: tasks
date: 2026-05-11
surface: agent
model: claude-sonnet-4-6
feature: 015-ai-tutor-chat
branch: 015-ai-tutor-chat
user: Muhammad
command: /sp.tasks
labels: ["tasks", "chat", "streaming", "sse", "quota", "sessions", "frontend", "backend", "agent-routing"]
links:
  spec: specs/015-ai-tutor-chat/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/015-ai-tutor-chat/tasks.md
tests:
  - none (task generation phase)
---

## Prompt

/sp.tasks (no additional user input)

## Response snapshot

Generated `specs/015-ai-tutor-chat/tasks.md` with 33 tasks across 7 phases for feature 015 AI Tutor Chat.

**Summary**:
- Total tasks: 33
- Phase 1 Setup: 2 tasks (openai-agents upgrade, npm install)
- Phase 2 Foundational: 8 tasks (migration, model, schemas, ChatQuotaService, repo methods, deps, triage off_topic, TS client)
- Phase 3 US1 (P1 MVP): 13 tasks (4 backend endpoints + 9 frontend components/hooks)
- Phase 4 US2 (P2): 2 tasks (TutorPanel upgrade + CodeEditorPanel props)
- Phase 5 US3 (P3): 2 tasks (off_topic endpoint handling + visual style)
- Phase 6 US4 (P3): 2 tasks (triage pattern audit + ExerciseAgent prompt verify)
- Phase 7 Polish: 4 tasks (a11y audit, error handling, bundle check, quickstart smoke test)

**Key dependency**: T001 (openai-agents v0.13) must precede T011 (Runner.run_streamed); T015 (useStreamChat) must precede T021 (ChatWindow) and T024 (TutorPanel upgrade).

## Outcome

- ✅ Impact: 33 immediately-executable tasks generated; all follow checklist format with IDs, [P], [US] labels, and file paths
- 🧪 Tests: No test tasks (spec does not request TDD; test-after per constitution for UI components)
- 📁 Files: specs/015-ai-tutor-chat/tasks.md
- 🔁 Next prompts: /sp.implement or begin manual execution starting with T001 + T002 in parallel
- 🧠 Reflection: Existing F07 agent infrastructure drastically reduces backend work; F15 is primarily a frontend build with thin backend additions (quota, session listing, schema extension)

## Evaluation notes (flywheel)

- Failure modes observed: none
- Graders run and results (PASS/FAIL): N/A
- Prompt variant (if applicable): null
- Next experiment (smallest change to try): Start T001 + T002 in parallel, then T003/T004 migration
