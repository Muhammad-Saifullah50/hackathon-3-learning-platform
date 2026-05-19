# Feature Specification: Teacher Dashboard

**Feature Branch**: `018-teacher-dashboard`  
**Created**: 2026-05-18  
**Status**: Draft  
**Input**: Teacher Dashboard with class management, exercise assignment, and student invitation system

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Role Selection at Signup (Priority: P1)

A new user registering on the platform must declare whether they are a student or a teacher. This determines what the platform shows them and which routes they can access.

**Why this priority**: Without role selection, every downstream feature (teacher-only routes, student-only tabs) is inaccessible. This is the gating condition for everything else in F18.

**Independent Test**: A new user can register as a teacher, log in, and be redirected to the teacher dashboard. A user who registers as a student cannot access `/teacher/*` routes and is redirected to the student dashboard.

**Acceptance Scenarios**:

1. **Given** a visitor is on the signup form, **When** they view the form, **Then** a role selector (Student / Teacher) is displayed as a required field.
2. **Given** a user selects "Teacher" and submits the form, **When** they log in, **Then** they are directed to the teacher dashboard.
3. **Given** a user selects "Student" and submits the form, **When** they attempt to navigate to `/teacher/dashboard`, **Then** they are redirected to `/dashboard` with an access-denied message.
4. **Given** a teacher is logged in, **When** they attempt to access a student-facing route, **Then** the route is accessible (teachers are not blocked from student views).

---

### User Story 2 — Teacher Creates a Class and Invites Students (Priority: P1)

A teacher creates one or more named classes and adds students by searching for them. Each student receives an invitation they must accept before being considered a class member.

**Why this priority**: Class membership is the foundation of exercise assignment. Without it, teachers cannot assign work to anyone.

**Independent Test**: A teacher can create a class, search for a student by name or email, send an invitation, and the student can see and accept/decline it in their sidebar.

**Acceptance Scenarios**:

1. **Given** a teacher is on the dashboard, **When** they create a class with a name, **Then** the class appears in their class list.
2. **Given** a teacher has a class, **When** they search for a student by partial name or email, **Then** matching users with role "student" appear in results.
3. **Given** a teacher selects a student from search results, **When** they click "Add to class", **Then** the student receives a pending invitation in their "Invitations" sidebar tab.
4. **Given** a student has a pending invitation, **When** they click "Accept", **Then** they become a member of the class and the class appears on their dashboard with the teacher's name.
5. **Given** a student has a pending invitation, **When** they click "Decline", **Then** the invitation is dismissed and the student is not added to the class.
6. **Given** a student is already a member of or already has a pending invitation to a class, **When** the teacher attempts to add the same student again, **Then** an informative message is shown and no duplicate invitation is created.
7. **Given** a teacher has multiple classes, **When** they view the dashboard, **Then** each class is listed with its member count.

---

### User Story 3 — Teacher Generates and Assigns an Exercise (Priority: P2)

A teacher navigates to the exercise generation page, describes what they want in free-form text, and the Exercise Agent either produces the exercise or prompts the teacher for missing details (topic, difficulty, target module). Once satisfied, the teacher assigns the exercise to a class.

**Why this priority**: This is the core teacher-to-student value delivery mechanism. Without it, teachers have no way to send targeted work to students.

**Independent Test**: A teacher can type a free-form prompt, receive a generated exercise (or a friendly prompt to provide more detail), preview the questions, optionally regenerate, then assign to a class — and the exercise appears in every accepted class member's "Assigned" tab.

**Acceptance Scenarios**:

1. **Given** a teacher submits a prompt that lacks topic, difficulty, or target module, **When** the guardrail runs, **Then** an inline friendly message lists exactly which details are missing and asks the teacher to include them — no exercise is generated.
2. **Given** a teacher submits a prompt describing a non-Python subject, **When** the guardrail runs, **Then** an inline message informs the teacher this platform is for Python exercises only.
3. **Given** a teacher submits a complete, on-topic prompt, **When** the Exercise Agent processes it, **Then** a preview of the generated exercise is displayed with all questions visible.
4. **Given** a teacher previews an exercise and is unsatisfied, **When** they click "Generate Again" and refine their prompt, **Then** a new exercise is generated replacing the previous preview.
5. **Given** a teacher is satisfied with the preview, **When** they click "Assign to Class" and select a class, **Then** all accepted members of that class receive the exercise in their "Assigned" tab.
6. **Given** a teacher assigns an exercise to a class with no accepted members, **When** they attempt to assign, **Then** a warning is shown informing the teacher no students will receive it; the assignment proceeds only with explicit confirmation.
7. **Given** a teacher has no classes yet, **When** they attempt to assign, **Then** a message prompts them to create a class first.

---

### User Story 4 — Student Completes an Assigned Exercise (Priority: P2)

A student sees an assigned exercise in their sidebar, opens it, works through each question in a dedicated view (description + embedded code editor), requests AI review per question, and submits when all questions are reviewed.

**Why this priority**: This closes the teacher→student loop. Without it, assigned exercises serve no purpose.

**Independent Test**: A student can open an assigned exercise, write code for each question, get AI review per question, and submit when all are reviewed — seeing their score on completion.

**Acceptance Scenarios**:

1. **Given** a student has accepted a class invitation, **When** the teacher assigns an exercise to that class, **Then** the exercise appears in the student's "Assigned" sidebar tab labelled with the class name.
2. **Given** a student opens an assigned exercise, **When** the exercise view loads, **Then** each question is displayed with its description and a code editor pre-filled with starter code (if provided).
3. **Given** a student has written code for a question, **When** they click "Get AI Review", **Then** the AI grades the question and displays the review below the editor.
4. **Given** a student has not yet obtained AI review on at least one question, **When** they view the submit button, **Then** the submit button is disabled.
5. **Given** a student has obtained AI review on every question, **When** the submit button becomes enabled and they click it, **Then** their overall score is calculated and displayed.
6. **Given** a student submits an exercise, **When** the submission is recorded, **Then** a teacher notification record is created in the database (to be surfaced in F22).
7. **Given** a student has already submitted an exercise, **When** they navigate back to it, **Then** the exercise is shown in a read-only completed state with their score; resubmission is not possible.
8. **Given** a student belongs to multiple classes, **When** they view the "Assigned" tab, **Then** exercises from all classes appear in a flat list, each labelled with the originating class name.

---

### User Story 5 — Student Sees Class and Teacher Information (Priority: P3)

A student who has accepted a class invitation can see the class name and teacher's name on their dashboard.

**Why this priority**: Informational only — supports orientation but does not block core workflows.

**Independent Test**: A student who accepted an invitation sees their class name and teacher name displayed on the dashboard.

**Acceptance Scenarios**:

1. **Given** a student has accepted at least one class invitation, **When** they view their dashboard, **Then** each class they belong to is listed with the corresponding teacher's name.
2. **Given** a student has not accepted any invitations, **When** they view their dashboard, **Then** the class section shows an empty state ("You haven't joined a class yet").

---

### Edge Cases

- What happens when the Exercise Agent is unavailable during generation? → Show a user-friendly error on the generation page; allow the teacher to retry.
- What happens when a student opens an exercise after the class is deleted or modified? → Exercise remains accessible and completable if the assignment was made while they were a member.
- What if a student submits and the score calculation fails? → Preserve the submission attempt, show an error, and allow retry of submission without requiring re-review.
- What if a teacher assigns the same exercise to the same class twice? → Prevent duplicate assignments; show an informative message.

---

## Requirements *(mandatory)*

### Functional Requirements

**Auth & Access**
- **FR-001**: The signup form MUST include a required role selector with options "Student" and "Teacher".
- **FR-002**: All routes under `/teacher/*` MUST be accessible only to users with the teacher role; students attempting access MUST be redirected to `/dashboard`.
- **FR-003**: All teacher API endpoints MUST enforce teacher-role authorization; requests from non-teacher users MUST receive a 403 response.

**Class Management**
- **FR-004**: A teacher MUST be able to create multiple named classes.
- **FR-005**: A teacher MUST be able to search for students by partial name or email address.
- **FR-006**: A teacher MUST be able to send a class invitation to any student found in search results.
- **FR-007**: The system MUST prevent duplicate invitations to a student already invited or already accepted into a class.
- **FR-008**: A student MUST be able to accept or decline a class invitation from their "Invitations" sidebar tab.
- **FR-009**: A student MUST be able to belong to multiple classes simultaneously.
- **FR-010**: A teacher MUST be able to have multiple classes with independent rosters.

**Exercise Generation**
- **FR-011**: The exercise generation page MUST provide a free-form text input for the teacher's exercise prompt.
- **FR-012**: Before generating, the system MUST validate that the prompt contains topic, difficulty level, and target module; if any are missing, an inline message MUST list the missing items and ask the teacher to include them — no exercise is generated.
- **FR-013**: If the prompt describes a non-Python subject, an inline message MUST inform the teacher and decline to generate.
- **FR-014**: When validation passes, the Exercise Agent MUST generate an exercise and display a preview of all questions.
- **FR-015**: The teacher MUST be able to refine their prompt and regenerate the exercise any number of times; each regeneration replaces the previous preview entirely.
- **FR-016**: Each generated exercise question MUST include a description and may include starter code.

**Exercise Assignment**
- **FR-017**: A teacher MUST be able to assign a previewed exercise to a selected class with a single confirm action.
- **FR-018**: Upon assignment, all students who have accepted membership in the target class MUST receive the exercise in their "Assigned" sidebar tab.
- **FR-019**: The system MUST prevent a teacher from assigning the same exercise to the same class more than once.
- **FR-020**: The system MUST create a teacher notification record upon student submission (to be surfaced in F22).

**Student Exercise View**
- **FR-021**: Each assigned exercise question MUST render with: the question description at the top, followed by a code editor pre-filled with starter code (if provided).
- **FR-022**: Each question MUST have a "Get AI Review" action that sends the student's code for grading and displays the review and grade below the editor.
- **FR-023**: The exercise submit button MUST remain disabled until every question has received an AI review in the current session.
- **FR-024**: On submission, the student's overall score MUST be calculated and displayed.
- **FR-025**: A submitted exercise MUST be rendered read-only; resubmission MUST be prevented.

**Student Dashboard Additions**
- **FR-026**: The student left sidebar MUST include an "Assigned" tab listing all exercises assigned across all classes, each labelled with its originating class name.
- **FR-027**: The student left sidebar MUST include an "Invitations" tab listing all pending class invitations with accept and decline actions.
- **FR-028**: The student dashboard MUST display the name of each class the student belongs to and the corresponding teacher's name.

---

### Key Entities

- **Class**: A named group owned by one teacher. A teacher may own many classes.
- **ClassMembership**: Links a student to a class with a status: `pending` (invited, not responded), `accepted`, or `declined`. A student may have memberships in multiple classes.
- **ClassExercise**: Links a generated exercise to a class, recording when it was assigned. Multiple exercises can be assigned to a class over time; duplicate assignments to the same class are prohibited.
- **ExerciseSubmission**: Records a student's final submission for a class exercise, including overall score and timestamp. One submission allowed per student per class exercise.
- **QuestionReview**: Records the AI-generated review and grade for a single question within an exercise attempt, scoped to a student and exercise.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A teacher can create a class, search for students, and send invitations without leaving the dashboard — end-to-end in under 2 minutes.
- **SC-002**: A student can view, accept, and act on a class invitation within 30 seconds of it appearing in their sidebar.
- **SC-003**: An exercise prompt missing required details is rejected with a clear inline message in under 3 seconds — no partial generation occurs.
- **SC-004**: A complete, valid exercise prompt produces a fully previewed exercise within 10 seconds.
- **SC-005**: A student can complete an assigned exercise (read, write code, get AI review per question, submit) in a single uninterrupted session with no blocking errors.
- **SC-006**: All teacher-only routes redirect student users within 1 second, with no raw error pages shown.
- **SC-007**: 100% of accepted class members at the time of assignment receive the exercise in their "Assigned" tab — no silent delivery failures.

---

## Scope Boundaries

### In Scope
- Role selector on signup form (frontend change only; backend role field exists from F01)
- Teacher dashboard: class creation, student search by name/email, invitation management
- Exercise generation page: free-form prompt, guardrail validation, preview, regeneration, assignment to class
- Student sidebar additions: "Assigned" tab and "Invitations" tab
- Student exercise view: per-question description + code editor + AI review + submit
- Student dashboard: class name and teacher name display for each accepted class
- Teacher notification record created on student submission (DB write only, UI deferred to F22)
- Role-based route protection for all `/teacher/*` routes and teacher API endpoints

### Out of Scope
- Class analytics and performance charts (F19)
- Struggle detection and alert triggers (F20)
- Real-time push notifications to teacher on submission (F22)
- Removing or archiving a student from a class
- Deleting or archiving a class
- Exercise due dates or deadlines
- Teacher viewing individual student submission details in this feature
- Student-initiated exercise requests (those remain in the AI Tutor Chat, F15)

---

## Dependencies

- **F01 (Auth)**: Role field exists in user model; JWT includes role claim; role-based middleware infrastructure exists
- **F07 / F11 (Exercise Agent)**: Direct invocation of Exercise Agent bypassing Triage; grading capability for assigned exercise questions
- **F13 (Student Dashboard)**: Left sidebar already exists; "Assigned" and "Invitations" are new tabs added to it
- **F14 (Code Editor)**: Monaco editor component already exists and is reused in the exercise question view

---

## Assumptions

- The existing user model has a `role` field supporting at least `student` and `teacher` values (confirmed F01).
- The Exercise Agent can be invoked directly with a free-form prompt and returns structured output: a list of questions each with description and optional starter code.
- AI grading for assigned exercises reuses the Exercise Agent's grading capability established in F11/F16.
- A teacher can search across all registered students on the platform (not scoped to a subset).
- Notification records created on submission are lightweight DB inserts; the UI for surfacing them is deferred to F22.
- The "Generate Again" flow replaces the previous preview entirely; prior generations are not retained in the UI.
