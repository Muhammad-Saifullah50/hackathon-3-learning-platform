---
id: "0002"
title: Quiz System Spec Clarifications
stage: spec
date: 2026-05-17
surface: agent
model: claude-sonnet-4-6
feature: 016-quiz-system
branch: 016-quiz-system
user: Muhammad
command: /sp.clarify
labels: [clarification, quiz-system, spec, mastery, ux, retake, teacher-visibility]
links:
  spec: specs/016-quiz-system/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/016-quiz-system/spec.md
tests:
  - null
---

## Prompt

/sp.clarify (no additional user input — automated spec ambiguity scan on branch 016-quiz-system)

## Response snapshot

Ran structured ambiguity scan on `specs/016-quiz-system/spec.md`. Asked and resolved 5 clarification questions:

1. **Topic-to-module mapping for mastery**: Quiz agent maps inferred chat topic to the closest of the 8 curriculum module slugs at generation time; mastery update uses this slug.
2. **Quiz generation loading state**: Reuse existing `TypingIndicator` during generation; `QuizCard` replaces it on arrival.
3. **Quiz retake policy**: Unlimited retakes allowed; each stored as a new quiz session; mastery uses the most recent completed score.
4. **Teacher visibility**: Quiz sessions accessible to teachers via existing student monitoring view; no new teacher UI in this feature.
5. **Mid-quiz navigation / resume**: Incomplete `QuizCard` re-rendered at original position on chat session reload; already-answered cards locked; student can resume.

All 5 answers integrated into `spec.md` under FR-002, FR-009, FR-010, Assumptions, Edge Cases, and the new `## Clarifications / ### Session 2026-05-17` section.

## Outcome

- ✅ Impact: Resolved 5 high-impact ambiguities that would have caused downstream rework in data model (retake policy), mastery update logic (module slug mapping), frontend rendering (loading state, resume), and API design (teacher access).
- 🧪 Tests: No tests run — spec-stage clarification only.
- 📁 Files: specs/016-quiz-system/spec.md (updated)
- 🔁 Next prompts: /sp.plan
- 🧠 Reflection: All major ambiguities resolved. Spec is ready for planning.

## Evaluation notes (flywheel)

- Failure modes observed: none
- Graders run and results (PASS/FAIL): n/a
- Prompt variant (if applicable): n/a
- Next experiment (smallest change to try): n/a
