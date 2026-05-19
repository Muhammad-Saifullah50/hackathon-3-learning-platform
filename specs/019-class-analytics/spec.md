# Feature Specification: Class Analytics

**Feature Branch**: `019-class-analytics`  
**Created**: 2026-05-19  
**Status**: Draft  
**Input**: User description: "Basic analytics on the teacher dashboard — replace placeholder data with real data from DB. Fast scope: all classes combined, struggling students from quiz score < 50%."

## User Scenarios & Testing *(mandatory)*

### User Story 1 — View Real Class Overview Stats (Priority: P1)

A teacher opens the dashboard and sees live summary numbers: total students enrolled across all their classes, number of active classes, average mastery score, and count of students who recently scored below 50% on a quiz.

**Why this priority**: This is the core value — the existing dashboard shows hardcoded numbers; replacing them with real data is the entire point of F19.

**Independent Test**: Teacher with at least one class and two enrolled students can open `/teacher/dashboard` and see non-hardcoded totals that change when a new student is added.

**Acceptance Scenarios**:

1. **Given** a teacher has 2 classes with 10 enrolled students total, **When** they load the dashboard, **Then** "Total Students" shows 10, "Active Classes" shows 2.
2. **Given** the mastery records table has scores for all enrolled students, **When** the dashboard loads, **Then** "Avg Mastery" shows the correct average rounded to the nearest percent.
3. **Given** 3 students scored below 50% on their most recent quiz, **When** the dashboard loads, **Then** "Open Alerts" shows 3.

---

### User Story 2 — View Module Mastery Bar Chart (Priority: P1)

A teacher views a bar chart showing average mastery per Python module across all their students, color-coded by mastery level (red/yellow/green).

**Why this priority**: The chart is already rendered; it just needs real data. High value, low effort.

**Independent Test**: Bar chart shows different values than the current hardcoded data when real mastery records exist in DB.

**Acceptance Scenarios**:

1. **Given** students have mastery records across multiple modules, **When** the teacher loads the dashboard, **Then** each module bar reflects the true average mastery across all enrolled students.
2. **Given** a module has no student data yet, **When** the dashboard loads, **Then** that module bar shows 0% (not an error).
3. **Given** a module's avg mastery is 75%, **When** displayed, **Then** the bar is green; at 55% amber; at 35% red.

---

### User Story 3 — View Students Needing Attention (Priority: P2)

A teacher sees a list of students who scored below 50% on their most recent quiz, including the student name, their class, and the quiz score.

**Why this priority**: Actionable insight for teacher intervention. Uses existing `quiz_sessions` data — no new detection logic needed.

**Independent Test**: A student who scored 40% on their last quiz appears in the list; a student who scored 60% does not.

**Acceptance Scenarios**:

1. **Given** a student's most recent quiz score is 45%, **When** the teacher views the dashboard, **Then** that student appears in "Students Needing Attention" with their score and class name.
2. **Given** no students have scored below 50% recently, **When** the dashboard loads, **Then** the section shows an empty state message ("All students are on track").
3. **Given** a student has no quiz attempts, **When** the dashboard loads, **Then** they do not appear in this list.

---

### Edge Cases

- Teacher has no classes yet → all stat cards show 0, charts show empty state, no error.
- Teacher has classes but no students enrolled → same as above.
- Module mastery record missing for a student-module pair → treat as 0 for averaging purposes.
- Student's most recent quiz was graded null/incomplete → exclude from alert list.

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST expose an analytics endpoint that returns, for the authenticated teacher: total enrolled student count, active class count, average mastery score, and low-quiz-score student count.
- **FR-002**: System MUST compute average mastery per module across all students enrolled in the teacher's classes.
- **FR-003**: System MUST return a list of students whose most recent quiz score is below 50%, including student name, class name, and score.
- **FR-004**: The teacher dashboard MUST fetch analytics data from the API instead of rendering hardcoded placeholder values.
- **FR-005**: All analytics MUST aggregate across all classes owned by the authenticated teacher (no per-class filter in this scope).
- **FR-006**: The dashboard MUST show a loading state while analytics data is being fetched.
- **FR-007**: If the analytics fetch fails, the dashboard MUST show an error state rather than stale placeholder data.
- **FR-008**: Any chart or UI section that cannot be backed by real data within this feature's scope MUST be removed from the dashboard entirely — hardcoded placeholder charts are not acceptable.

### Key Entities

- **Class**: A teaching group owned by a teacher; has many enrolled students via class memberships.
- **ClassMembership**: Links a student user to a class.
- **ModuleMastery**: A per-student, per-module mastery score (0–100) stored in `user_module_mastery`.
- **QuizSession**: A completed quiz attempt with a score; used to identify low-performing students.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Analytics data loads within 2 seconds for a teacher with up to 100 students across 10 classes.
- **SC-002**: Stat card values match ground truth DB counts — zero tolerance for off-by-one errors in student counts.
- **SC-003**: Module mastery chart values differ from the current hardcoded data when real records exist, confirming live data is used.
- **SC-004**: A student added to a class appears in the total student count on the next dashboard load (no stale cache).
- **SC-005**: Teachers with no classes or students see a functional dashboard with zero-value stats rather than an error page.

---

## Assumptions

- Weekly activity chart (code submissions & quizzes per day) is **out of scope** for this feature — it requires aggregating `code_sessions` and `quiz_sessions` by day, which adds complexity. It MUST be removed from the dashboard (not left as a placeholder).
- "Active classes" means classes owned by the teacher (all classes count as active for now).
- Mastery data is read from the existing `user_module_mastery` table populated by F17.
- Quiz scores are read from the existing `quiz_sessions` table populated by F16.
- No CSV export in this scope.
- No individual student drill-down in this scope.
