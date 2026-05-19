---
id: "0004"
title: Implement Teacher Dashboard Feature
stage: green
date: 2026-05-18
surface: agent
model: claude-sonnet-4-6
feature: 018-teacher-dashboard
branch: 018-teacher-dashboard
user: Muhammad
command: /sp.implement
labels: ["implementation","backend","frontend","teacher-dashboard","server-components"]
links:
  spec: specs/018-teacher-dashboard/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - backend/alembic/versions/20260518_teacher_dashboard.py
  - backend/src/models/teacher_classes.py
  - backend/src/schemas/teacher.py
  - backend/src/schemas/student_classes.py
  - backend/src/repositories/class_repository.py
  - backend/src/repositories/class_membership_repository.py
  - backend/src/repositories/class_exercise_repository.py
  - backend/src/repositories/teacher_exercise_repository.py
  - backend/src/dependencies.py
  - backend/src/main.py
  - backend/src/api/v1/teacher.py
  - backend/src/api/v1/student_classes.py
  - backend/src/services/class_service.py
  - backend/src/services/invitation_service.py
  - backend/src/services/teacher_exercise_service.py
  - backend/src/services/student_assignment_service.py
  - backend/src/services/agents/guardrails.py
  - frontend/src/middleware.ts
  - frontend/src/components/auth/register-form.tsx
  - frontend/src/components/teacher/TeacherNavLinks.tsx
  - frontend/src/components/teacher/ClassCard.tsx
  - frontend/src/components/teacher/ClassesPanel.tsx
  - frontend/src/components/teacher/ClassDetailPanel.tsx
  - frontend/src/components/teacher/StudentSearchModal.tsx
  - frontend/src/components/teacher/ExerciseGeneratorForm.tsx
  - frontend/src/components/teacher/ExercisePreview.tsx
  - frontend/src/components/teacher/AssignClassModal.tsx
  - frontend/src/components/teacher/ExerciseGenerationWorkflow.tsx
  - frontend/src/components/student/InvitationCard.tsx
  - frontend/src/components/student/InvitationsPanel.tsx
  - frontend/src/components/student/AssignedExerciseCard.tsx
  - frontend/src/components/student/ExerciseQuestionView.tsx
  - frontend/src/components/student/ExerciseWorkspace.tsx
  - frontend/src/hooks/useTeacherClasses.ts
  - frontend/src/hooks/useStudentInvitations.ts
  - frontend/src/hooks/useExerciseGeneration.ts
  - frontend/src/hooks/useAssignedExercises.ts
  - frontend/src/hooks/useMemberships.ts
  - frontend/src/lib/api/teacher.ts
  - frontend/src/lib/api/student-classes.ts
  - frontend/src/app/(teacher)/layout.tsx
  - frontend/src/app/(teacher)/teacher/dashboard/page.tsx
  - frontend/src/app/(teacher)/teacher/classes/[id]/page.tsx
  - frontend/src/app/(teacher)/teacher/exercises/generate/page.tsx
  - frontend/src/app/(student)/exercises/page.tsx
  - frontend/src/app/(student)/exercises/[id]/page.tsx
  - frontend/src/app/(student)/invitations/page.tsx
  - frontend/src/app/(student)/dashboard/page.tsx
  - frontend/src/components/layout/nav-links.tsx
  - specs/018-teacher-dashboard/tasks.md
tests:
  - "Checkpoint T001-T002: migration file created, routers registered"
  - "Checkpoint T003-T010: models, schemas, repos, deps wired"
  - "Checkpoint T011-T015: role selector on signup, middleware, teacher shell"
  - "Checkpoint T016-T019: ClassService, InvitationService, teacher+student routers"
  - "Checkpoint T027-T028: teacher dashboard + class detail pages"
  - "Checkpoint T030-T032: guardrail + TeacherExerciseService + endpoints"
  - "Checkpoint T037: exercise generation page"
  - "Checkpoint T038-T039: StudentAssignmentService + student exercise endpoints"
  - "Checkpoint T044: student exercise workspace page"
  - "Checkpoint T045-T047: memberships endpoint + student dashboard section"
---

## Prompt

/sp.implement (with follow-up instruction: make maximum number of components server components)

## Response snapshot

Implemented all 51 tasks for F18 Teacher Dashboard across Phases 1–7:

**Backend (Python/FastAPI)**
- Alembic migration creating 7 new tables (classes, class_memberships, teacher_generated_exercises, class_exercises, class_exercise_submissions, question_reviews, teacher_notifications)
- 7 SQLAlchemy models in `backend/src/models/teacher_classes.py`
- Pydantic schemas in `backend/src/schemas/teacher.py` and `backend/src/schemas/student_classes.py`
- 4 repository files covering all CRUD operations
- 4 service files: ClassService, InvitationService, TeacherExerciseService (with multi-question agent + guardrail), StudentAssignmentService (with Code Review Agent per-question)
- Teacher router: `/api/v1/teacher/*` (classes CRUD, student search, exercise generate+assign)
- Student classes router: `/api/v1/student/classes/*` (invitations, memberships, assigned exercises, review, submit)
- `teacher_exercise_guardrail` added to guardrails.py for prompt validation
- All routes protected with `require_role(['teacher'])` / `require_role(['student'])`

**Frontend (Next.js/TypeScript) — maximizing server components**
- All pages are server components fetching data server-side via fastApiToken
- Only interactive islands are 'use client': ClassesPanel, ClassDetailPanel, StudentSearchModal, ExerciseGenerationWorkflow, InvitationsPanel, ExerciseWorkspace, ExerciseQuestionView (Monaco)
- Pure display components are server components: ClassCard, AssignedExerciseCard, ExercisePreview
- Next.js middleware protecting `/teacher/*` routes
- Role selector added to register form (Student/Teacher toggle)
- Teacher layout with sidebar + TeacherNavLinks
- Student NavLinks extended with Assigned + Invitations tabs
- Student dashboard extended with My Classes membership section
- 5 hooks for client-side mutations (useTeacherClasses, useStudentInvitations, useExerciseGeneration, useAssignedExercises, useMemberships)

**Next step**: Run `alembic upgrade head` against the live Neon database to apply the migration.
