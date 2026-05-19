# Tasks: Teacher Dashboard (F18)

**Input**: Design documents from `/specs/018-teacher-dashboard/`
**Branch**: `018-teacher-dashboard`
**Date**: 2026-05-18
**Prerequisites**: plan.md ✅ spec.md ✅ data-model.md ✅ contracts/ ✅ quickstart.md ✅

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: Which user story this task belongs to (US1–US5)
- Exact file paths are included in every task description

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create the migration and wire new routers so the rest of the feature has a runnable foundation.

- [X] T001 Create Alembic migration for all 7 new tables in `backend/alembic/versions/20260518_teacher_dashboard.py` (classes, class_memberships, teacher_generated_exercises, class_exercises, class_exercise_submissions, question_reviews, teacher_notifications)
- [X] T002 Register `teacher` and `student_classes` routers in `backend/src/main.py`

**Checkpoint**: `alembic upgrade head` applies cleanly; `/api/v1/teacher` and `/api/v1/student/classes` prefixes appear in `/openapi.json`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core backend models, schemas, repositories, and dependency wiring that every user story depends on.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [X] T003 Create all 7 SQLAlchemy models (Class, ClassMembership, TeacherGeneratedExercise, ClassExercise, ClassExerciseSubmission, QuestionReview, TeacherNotification) in `backend/src/models/teacher_classes.py`
- [X] T004 [P] Create teacher request/response Pydantic schemas (ClassCreate, ClassResponse, ClassDetail, ClassMember, StudentSearchResult, TeacherExercise, ExerciseQuestion, GuardrailRejection, AssignResponse) in `backend/src/schemas/teacher.py`
- [X] T005 [P] Create student-facing Pydantic schemas (PendingInvitation, AcceptedClass, AssignedExerciseSummary, AssignedExerciseDetail, QuestionReviewResult, InvitationAction, SubmitResponse) in `backend/src/schemas/student_classes.py`
- [X] T006 [P] Implement ClassRepository (create, get_by_id, list_by_teacher, get_with_member_count) in `backend/src/repositories/class_repository.py`
- [X] T007 [P] Implement ClassMembershipRepository (create, get_by_class_and_student, list_pending_by_student, list_accepted_by_student, update_status) in `backend/src/repositories/class_membership_repository.py`
- [X] T008 [P] Implement ClassExerciseRepository (create, get_by_id, get_by_class_and_exercise, list_by_class, list_assigned_to_student) in `backend/src/repositories/class_exercise_repository.py`
- [X] T009 [P] Implement TeacherExerciseRepository (create, get_by_id) and submission/review repos (ClassExerciseSubmissionRepository, QuestionReviewRepository) in `backend/src/repositories/teacher_exercise_repository.py`
- [X] T010 Register dependency factories for all new repositories and services (get_class_repository, get_class_membership_repository, get_class_exercise_repository, get_teacher_exercise_repository) in `backend/src/dependencies.py`

**Checkpoint**: `pytest backend/tests/` imports all new models and repos without error; DB tables created via migration

---

## Phase 3: User Story 1 — Role Selection at Signup (Priority: P1) 🎯 MVP Gate

**Goal**: A new user declaring "Teacher" at signup is routed to the teacher dashboard; students are blocked from `/teacher/*` routes.

**Independent Test**: Register as teacher → redirected to `/teacher/dashboard`. Register as student → `/teacher/dashboard` redirects to `/dashboard` with access-denied feedback.

### Implementation for User Story 1

- [X] T011 [US1] Add role selector (Student / Teacher radio or select, required) to the signup form in `frontend/src/components/auth/register-form.tsx`; include `role` in the POST body sent to `POST /api/auth/sign-up/email`
- [X] T012 [US1] Update Next.js middleware to protect `/teacher/*` routes: redirect non-teacher users to `/dashboard`; allow teachers access to all routes in `frontend/src/middleware.ts`
- [X] T013 [US1] Create teacher route-group shell layout with sidebar placeholder in `frontend/src/app/(teacher)/layout.tsx`
- [X] T014 [P] [US1] Create TeacherNavLinks component (Dashboard, Classes, Generate Exercise nav items) in `frontend/src/components/teacher/TeacherNavLinks.tsx`
- [X] T015 [US1] Create teacher dashboard page skeleton (renders TeacherNavLinks, shows "Welcome, Teacher" heading, class list placeholder) in `frontend/src/app/(teacher)/teacher/dashboard/page.tsx`

**Checkpoint**: Signup form shows role selector; teacher login → `/teacher/dashboard`; student → redirected away from `/teacher/*`

---

## Phase 4: User Story 2 — Teacher Creates a Class and Invites Students (Priority: P1)

**Goal**: Teacher can create named classes, search students, send invitations; students can accept or decline from their Invitations sidebar tab.

**Independent Test**: Teacher creates class → class appears in list. Teacher searches "Alice" → student found. Teacher invites → student sees pending invitation. Student accepts → class appears on student dashboard with teacher name.

### Implementation for User Story 2 — Backend

- [X] T016 [US2] Implement ClassService (create_class, list_classes, get_class_detail, search_students by partial name/email, max 20 results) in `backend/src/services/class_service.py`
- [X] T017 [US2] Implement InvitationService (invite_student with duplicate guard returning 409, respond_to_invitation accept/decline with 409 on re-response) in `backend/src/services/invitation_service.py`
- [X] T018 [US2] Implement teacher router with class management endpoints: `POST /classes`, `GET /classes`, `GET /classes/{class_id}`, `GET /students/search?q=`, `POST /classes/{class_id}/invitations` — all guarded by `require_role(['teacher'])` in `backend/src/api/v1/teacher.py`
- [X] T019 [US2] Implement student classes router with invitation endpoints: `GET /invitations`, `PATCH /invitations/{invitation_id}` — guarded by `require_role(['student'])` in `backend/src/api/v1/student_classes.py`

### Implementation for User Story 2 — Frontend

- [X] T020 [P] [US2] Create teacher API fetch helpers (createClass, listClasses, getClassDetail, searchStudents, inviteStudent) in `frontend/src/lib/api/teacher.ts`
- [X] T021 [P] [US2] Create student classes API fetch helpers (listInvitations, respondToInvitation, listMemberships) in `frontend/src/lib/api/student-classes.ts`
- [X] T022 [P] [US2] Create useTeacherClasses hook (useClasses, useClassDetail, useStudentSearch) in `frontend/src/hooks/useTeacherClasses.ts`
- [X] T023 [P] [US2] Create useStudentInvitations hook (invitations list, respond mutation) in `frontend/src/hooks/useStudentInvitations.ts`
- [X] T024 [P] [US2] Create ClassCard component (class name, member count, click-to-detail) in `frontend/src/components/teacher/ClassCard.tsx`
- [X] T025 [P] [US2] Create StudentSearchModal component (search input, result list, "Add to class" action, duplicate-invitation error display) in `frontend/src/components/teacher/StudentSearchModal.tsx`
- [X] T026 [P] [US2] Create InvitationCard component (class name, teacher name, Accept/Decline buttons) in `frontend/src/components/student/InvitationCard.tsx`
- [X] T027 [US2] Implement teacher dashboard page with class list (ClassCard grid), "Create Class" form, and StudentSearchModal integration in `frontend/src/app/(teacher)/teacher/dashboard/page.tsx`
- [X] T028 [US2] Implement class detail page (member list with status badges, "Add Student" button opening StudentSearchModal) in `frontend/src/app/(teacher)/teacher/classes/[id]/page.tsx`
- [X] T029 [US2] Add "Invitations" tab to student sidebar NavLinks and wire InvitationCard list with accept/decline actions in `frontend/src/components/student/NavLinks.tsx`

**Checkpoint**: Full teacher→student invitation round-trip works; duplicate invitation returns informative message; student accepts → class appears on dashboard

---

## Phase 5: User Story 3 — Teacher Generates and Assigns an Exercise (Priority: P2)

**Goal**: Teacher types a free-form prompt, prompt guardrail validates it, Exercise Agent generates a multi-question preview, teacher assigns to a class — exercise appears in accepted students' Assigned tab.

**Independent Test**: Incomplete prompt → inline error listing missing items. Valid on-topic prompt → exercise preview with all questions. Assign to class with one accepted member → exercise appears in that student's Assigned tab.

### Implementation for User Story 3 — Backend

- [X] T030 [US3] Add `teacher_exercise_guardrail(prompt)` function (LLM-based structured output: `{is_valid, missing, message, code}` covering PROMPT_INVALID and NOT_PYTHON_TOPIC cases) to `backend/src/services/agents/guardrails.py`
- [X] T031 [US3] Implement TeacherExerciseService (generate: runs guardrail → raises 400 on failure → calls `Runner.run(get_exercise_agent(), prompt)` → persists TeacherGeneratedExercise; assign: creates ClassExercise with 409 guard, returns assigned_to_count with warning if zero accepted members) in `backend/src/services/teacher_exercise_service.py`
- [X] T032 [US3] Add exercise endpoints to teacher router: `POST /exercises/generate` (returns TeacherExercise or GuardrailRejection 400), `POST /exercises/{exercise_id}/assign` (returns AssignResponse with optional warning) in `backend/src/api/v1/teacher.py`

### Implementation for User Story 3 — Frontend

- [X] T033 [P] [US3] Create useExerciseGeneration hook (generate mutation with streaming state, assign mutation, guardrail error state) in `frontend/src/hooks/useExerciseGeneration.ts`
- [X] T034 [P] [US3] Create ExerciseGeneratorForm component (textarea with char counter, submit button, inline guardrail error display listing missing items) in `frontend/src/components/teacher/ExerciseGeneratorForm.tsx`
- [X] T035 [P] [US3] Create ExercisePreview component (displays exercise title + questions list with description and starter code per question, "Generate Again" and "Assign to Class" actions) in `frontend/src/components/teacher/ExercisePreview.tsx`
- [X] T036 [P] [US3] Create AssignClassModal component (class selector dropdown, confirm/cancel, zero-member warning with explicit confirmation) in `frontend/src/components/teacher/AssignClassModal.tsx`
- [X] T037 [US3] Create exercise generation page (ExerciseGeneratorForm + ExercisePreview + AssignClassModal composed with loading state during agent call) in `frontend/src/app/(teacher)/teacher/exercises/generate/page.tsx`

**Checkpoint**: Incomplete prompt shows guardrail error inline; valid prompt returns preview within 10s; assign routes exercise to accepted student's Assigned tab

---

## Phase 6: User Story 4 — Student Completes an Assigned Exercise (Priority: P2)

**Goal**: Student opens an assigned exercise, writes code per question, gets AI review per question, submits when all reviewed — sees score; exercise becomes read-only.

**Independent Test**: Student sees exercise in Assigned tab. Opens it → questions with code editor. Writes code → AI review returned per question. Submit disabled until all reviewed. Submit → score shown. Revisit → read-only, no resubmit.

### Implementation for User Story 4 — Backend

- [X] T038 [US4] Implement StudentAssignmentService (list_assigned_exercises, get_exercise_detail with existing reviews, review_question via `Runner.run(get_code_review_agent())` with upsert, submit_exercise with all-reviewed check + score calc + TeacherNotification insert) in `backend/src/services/student_assignment_service.py`
- [X] T039 [US4] Add assigned-exercise endpoints to student classes router: `GET /assigned-exercises`, `GET /assigned-exercises/{id}`, `POST /assigned-exercises/{id}/review`, `POST /assigned-exercises/{id}/submit` in `backend/src/api/v1/student_classes.py`

### Implementation for User Story 4 — Frontend

- [X] T040 [P] [US4] Create useAssignedExercises hook (list query, detail query, review mutation, submit mutation) in `frontend/src/hooks/useAssignedExercises.ts`
- [X] T041 [P] [US4] Create AssignedExerciseCard component (exercise title, class name label, topic/difficulty badges, status indicator) in `frontend/src/components/student/AssignedExerciseCard.tsx`
- [X] T042 [P] [US4] Create ExerciseQuestionView component (question description, Monaco editor pre-filled with starter code, "Get AI Review" button, review/grade display below editor, read-only mode when submitted) in `frontend/src/components/student/ExerciseQuestionView.tsx`
- [X] T043 [US4] Add "Assigned" tab to student sidebar NavLinks with AssignedExerciseCard list in `frontend/src/components/student/NavLinks.tsx`
- [X] T044 [US4] Create student exercise view page (list of ExerciseQuestionView per question, submit button disabled until all reviewed, score display on submission, read-only guard when status=submitted) in `frontend/src/app/(student)/exercises/[id]/page.tsx`

**Checkpoint**: Student sees assigned exercise in sidebar; per-question AI review works; submit button enables only after all reviews; submitted exercise is read-only

---

## Phase 7: User Story 5 — Student Sees Class and Teacher Information (Priority: P3)

**Goal**: Student dashboard displays each accepted class with the corresponding teacher's name.

**Independent Test**: Student who accepted invitation sees class name + teacher name on dashboard. Student with no accepted classes sees empty state.

### Implementation for User Story 5 — Backend

- [X] T045 [US5] Add `GET /memberships` endpoint to student classes router (returns list of AcceptedClass with class_name and teacher_name) in `backend/src/api/v1/student_classes.py`

### Implementation for User Story 5 — Frontend

- [X] T046 [P] [US5] Create useMemberships hook (accepted classes list query) in `frontend/src/hooks/useMemberships.ts`
- [X] T047 [US5] Add class membership section to student dashboard showing each class name + teacher name; empty state "You haven't joined a class yet" when list is empty in `frontend/src/app/(student)/dashboard/page.tsx`

**Checkpoint**: Student dashboard shows accepted classes with teacher names; empty state renders correctly

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: End-to-end validation, error resilience, and production readiness across all stories.

- [ ] T048 [P] Add loading skeletons and error boundary states to all new teacher components (ClassCard, ExercisePreview, AssignClassModal) in `frontend/src/components/teacher/`
- [ ] T049 [P] Add loading and error states to all new student components (InvitationCard, AssignedExerciseCard, ExerciseQuestionView) in `frontend/src/components/student/`
- [ ] T050 Run end-to-end smoke test from `specs/018-teacher-dashboard/quickstart.md` Steps A→D; verify all 7 acceptance scenarios from spec pass
- [ ] T051 [P] Verify teacher role protection: confirm all `/api/v1/teacher/*` endpoints return 403 for student tokens; confirm `/teacher/*` frontend routes redirect students within 1 second

---

## Dependencies & Execution Order

### Phase Dependencies

```
Phase 1 (Setup) ──────────────────────────────────── no dependencies
Phase 2 (Foundational) ──── depends on Phase 1 ──── BLOCKS all user stories
Phase 3 (US1) ──────────────┐
Phase 4 (US2) ──────────────┤ all depend on Phase 2 completion
Phase 5 (US3) ──────────────┤ can run in parallel if staffed
Phase 6 (US4) ──────────────┤ US3 must finish before US4 (exercise must exist to assign/complete)
Phase 7 (US5) ──────────────┘
Phase 8 (Polish) ─────────── depends on desired stories complete
```

### User Story Dependencies

| Story | Depends On | Can Parallelise With |
|-------|-----------|----------------------|
| US1 (Role Selection) | Phase 2 | US2 backend work |
| US2 (Class + Invitations) | Phase 2 | US1 |
| US3 (Generate + Assign) | US2 (classes must exist to assign) | US1 |
| US4 (Student Exercise) | US3 (assigned exercises must exist) | US5 |
| US5 (Class Info Display) | US2 (memberships must exist) | US4 |

### Within Each User Story

- Backend: Models → Repositories → Services → Endpoints (sequential)
- Frontend: API helpers → Hooks → Components → Pages (sequential)
- Backend and frontend for same story: can run in parallel once schemas are agreed

### Parallel Opportunities

```bash
# Phase 2 — run all [P] tasks simultaneously:
T004  backend/src/schemas/teacher.py
T005  backend/src/schemas/student_classes.py
T006  backend/src/repositories/class_repository.py
T007  backend/src/repositories/class_membership_repository.py
T008  backend/src/repositories/class_exercise_repository.py
T009  backend/src/repositories/teacher_exercise_repository.py

# Phase 4 — after T016/T017/T018/T019 are done, run frontend in parallel:
T020  frontend/src/lib/api/teacher.ts
T021  frontend/src/lib/api/student-classes.ts
T022  frontend/src/hooks/useTeacherClasses.ts
T023  frontend/src/hooks/useStudentInvitations.ts
T024  frontend/src/components/teacher/ClassCard.tsx
T025  frontend/src/components/teacher/StudentSearchModal.tsx
T026  frontend/src/components/student/InvitationCard.tsx

# Phase 5 — after T030/T031/T032 done, run frontend in parallel:
T033  frontend/src/hooks/useExerciseGeneration.ts
T034  frontend/src/components/teacher/ExerciseGeneratorForm.tsx
T035  frontend/src/components/teacher/ExercisePreview.tsx
T036  frontend/src/components/teacher/AssignClassModal.tsx

# Phase 6 — after T038/T039 done, run frontend in parallel:
T040  frontend/src/hooks/useAssignedExercises.ts
T041  frontend/src/components/student/AssignedExerciseCard.tsx
T042  frontend/src/components/student/ExerciseQuestionView.tsx
```

---

## Implementation Strategy

### MVP Scope (User Stories 1 + 2 Only)

1. Complete Phase 1: Setup (T001–T002)
2. Complete Phase 2: Foundational (T003–T010)
3. Complete Phase 3: US1 — Role Selection (T011–T015)
4. Complete Phase 4: US2 — Class + Invitations (T016–T029)
5. **STOP and VALIDATE**: Teacher creates class, invites student, student accepts — full round-trip
6. Demo to stakeholders; proceed to P2 stories

### Incremental Delivery

1. Setup + Foundational → foundation ready
2. US1 → role-based access live
3. US2 → class management + invitations live (MVP!)
4. US3 → exercise generation + assignment live
5. US4 → student exercise completion live (closes teacher→student loop)
6. US5 → student sees class info (polish)

### Parallel Team Strategy (2 developers)

1. Both complete Setup + Foundational together (Phase 1–2)
2. Developer A: US1 + US2 backend
   Developer B: US1 + US2 frontend (after schemas agreed)
3. Developer A: US3 backend → US4 backend
   Developer B: US2 frontend → US3 frontend
4. Merge and validate each story independently before proceeding

---

## Notes

- `require_role(['teacher'])` and `require_role(['student'])` already exist from F01 — do not recreate
- Monaco editor component already exists from F14 — import it in ExerciseQuestionView (T042)
- The Exercise Agent and Code Review Agent already exist from F07/F16 — invoke via `Runner.run()` in T031/T038
- T029 and T043 both modify `NavLinks.tsx` — implement sequentially; T029 (Invitations tab) before T043 (Assigned tab)
- Alembic migration in T001 depends on `20260518_add_mastery_snapshots` (F17 head)
- No new env vars required — reuse existing `GEMINI_API_KEY` / `DATABASE_URL`
