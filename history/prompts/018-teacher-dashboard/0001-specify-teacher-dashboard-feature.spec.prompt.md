---
id: "0001"
title: Specify Teacher Dashboard Feature
stage: spec
date: 2026-05-18
surface: agent
model: claude-sonnet-4-6
feature: 018-teacher-dashboard
branch: 018-teacher-dashboard
user: Muhammad
command: /sp.specify 018-teacher-dashboard
labels: ["spec", "teacher-dashboard", "class-management", "exercise-assignment", "invitations"]
links:
  spec: specs/018-teacher-dashboard/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/018-teacher-dashboard/spec.md
  - specs/018-teacher-dashboard/checklists/requirements.md
tests:
  - null
---

## Prompt

User described feature 18 across multiple turns of a discovery interview:

"yes there will be a teacher dashboard. Teacher will be able to see a list of all students and search through them. They will be able to add students to a class and assign exercises. These exercises will be designed by the exercise agent. once the exercise is generated, the teacher will have a button to assign it to the class. Each student will have a assigned tab in the left sidebar where they will be able to see the assigned exercises. They should also be able to see their teacher name and the class they belong to. Based on student progress, the teacher will see class analytics and get notifications. We will implement the analytics and notifications in the next feature. for now also add a role field in the signup form with options of a student and teacher. When a teacher adds a student to a class, the student should get an invitation to accept or decline the class. these invitations will be shown to the user in another tab in the left sidebar for invitations."

Further clarifications:
- Teacher can have multiple classes; student can be in multiple classes
- Teacher generates exercise via free-form input directly to Exercise Agent (no Triage), with guardrail: if topic/difficulty/module missing, show friendly inline message — no chat UI
- Preview exercise, regenerate if unsatisfied, assign to entire class
- Assigned + Invitations tabs added to existing left sidebar
- Exercise view: description + Monaco editor per question, AI review per question, submit enabled only when all reviewed
- Student sees teacher name and class name on dashboard
- Teacher notification on submit deferred to F22
- /teacher/* routes protected (teacher role only)
- Role selector in signup form must not break existing backend functionality

## Response snapshot

Created `specs/018-teacher-dashboard/spec.md` with:
- 5 prioritized user stories (P1: role selection, P1: class + invitation flow, P2: exercise generation + assignment, P2: student exercise completion, P3: class/teacher info display)
- 28 functional requirements across Auth, Class Management, Exercise Generation, Exercise Assignment, Student Exercise View, and Student Dashboard Additions
- 5 key entities: Class, ClassMembership, ClassExercise, ExerciseSubmission, QuestionReview
- 7 measurable success criteria
- Clear scope boundaries (F19/F20/F22 deferred)
- Dependencies on F01, F07/F11, F13, F14
- All checklist items pass; no NEEDS CLARIFICATION markers

## Outcome

- ✅ Impact: Complete spec for F18 Teacher Dashboard; unblocks /sp.plan
- 🧪 Tests: No tests (spec phase)
- 📁 Files: specs/018-teacher-dashboard/spec.md, specs/018-teacher-dashboard/checklists/requirements.md
- 🔁 Next prompts: /sp.plan 018-teacher-dashboard
- 🧠 Reflection: Conducted full interview before spec to clarify all ambiguities; no NEEDS CLARIFICATION markers needed in final spec

## Evaluation notes (flywheel)

- Failure modes observed: none
- Graders run and results (PASS/FAIL): spec quality checklist — all PASS
- Prompt variant (if applicable): null
- Next experiment (smallest change to try): null
