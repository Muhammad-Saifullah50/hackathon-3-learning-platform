# Implementation Plan: Teacher Dashboard

**Branch**: `018-teacher-dashboard` | **Date**: 2026-05-18 | **Spec**: [spec.md](./spec.md)  
**Input**: Feature specification from `/specs/018-teacher-dashboard/spec.md`

---

## Summary

F18 delivers the teacher-student class loop: role selection at signup, teacher class management with invitation-based enrollment, AI-powered exercise generation with prompt guardrails, class-level assignment, and student exercise completion with per-question AI review. The implementation adds five new DB tables, two new API routers (teacher + student-classes), a new teacher frontend shell, and extends the student sidebar with Assigned/Invitations tabs.

---

## Technical Context

**Language/Version**: Python 3.13 (backend), TypeScript 5+ / React 19 (frontend)  
**Primary Dependencies**: FastAPI, openai-agents ≥0.13, SQLAlchemy 2.0+, Pydantic 2.0+, Alembic 1.13+, Next.js 14+, Tailwind CSS, Better Auth, Monaco Editor (reuse from F14)  
**Storage**: Neon PostgreSQL — five new tables: `classes`, `class_memberships`, `class_exercises`, `teacher_generated_exercises`, `class_exercise_submissions`, `question_reviews`, `teacher_notifications`  
**Testing**: pytest + httpx (backend), Vitest + @testing-library/react (frontend)  
**Target Platform**: Linux server (backend) + Vercel (frontend)  
**Project Type**: Web application (backend/ + frontend/ monorepo)  
**Performance Goals**:
- Exercise generation (AI): < 10s end-to-end (SC-004)
- Guardrail rejection: < 3s (SC-003)
- Student invitation accept: < 30s perceived (SC-002)
- Non-AI API responses: < 150ms p95 (constitution)

**Constraints**:
- All `/teacher/*` frontend routes and `/api/v1/teacher/*` backend routes restricted to `role='teacher'`
- Exercise generation reuses Exercise Agent from F07 via direct `Runner.run()` (no Triage)
- Code Review Agent reused for per-question AI review
- No new LLM providers; `LlmClient` pattern preserved
- Monaco editor component reused from F14 (no new editor)
- Alembic migration required; no direct schema changes

---

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-checked after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| Repository pattern (no raw queries in routes) | ✅ PASS | New repos for Class, ClassMembership, ClassExercise, TeacherExercise |
| LLM calls via LlmClient / Runner.run() | ✅ PASS | Exercise Agent + Code Review Agent via Runner.run() |
| Auth: all routes require get_current_user | ✅ PASS | `require_role(['teacher'])` wraps `get_current_user` |
| No exec/eval on server | ✅ PASS | Per-question review is AI text, no code execution |
| Alembic for schema changes | ✅ PASS | New migration: `20260518_teacher_dashboard.py` |
| Streaming AI responses | ✅ PASS | Exercise generation uses StreamingResponse; review uses streamed runner |
| Test coverage targets (80% routes, 85% repos) | ⚠️ TARGET | Unit + integration tests required for all new routes and repos |
| No hardcoded secrets | ✅ PASS | All config via env vars through existing patterns |
| next/dynamic for Monaco | ✅ PASS | Monaco already loaded dynamically in F14; reused as-is |

**Gate result**: PASS — no violations.

---

## Project Structure

### Documentation (this feature)

```text
specs/018-teacher-dashboard/
├── plan.md              ← this file
├── research.md          ← Phase 0 output
├── data-model.md        ← Phase 1 output
├── quickstart.md        ← Phase 1 output
├── contracts/           ← Phase 1 output
│   ├── teacher-api.yaml
│   └── student-classes-api.yaml
└── tasks.md             ← Phase 2 output (/sp.tasks — NOT created here)
```

### Source Code

```text
backend/
├── alembic/versions/
│   └── 20260518_teacher_dashboard.py        ← NEW migration
├── src/
│   ├── models/
│   │   └── teacher_classes.py               ← NEW (Class, ClassMembership, ClassExercise,
│   │                                             TeacherExercise, ClassExerciseSubmission,
│   │                                             QuestionReview, TeacherNotification)
│   ├── schemas/
│   │   ├── teacher.py                       ← NEW (request/response schemas)
│   │   └── student_classes.py               ← NEW (student-facing schemas)
│   ├── repositories/
│   │   ├── class_repository.py              ← NEW
│   │   ├── class_membership_repository.py   ← NEW
│   │   ├── class_exercise_repository.py     ← NEW
│   │   └── teacher_exercise_repository.py   ← NEW
│   ├── services/
│   │   ├── class_service.py                 ← NEW
│   │   ├── invitation_service.py            ← NEW
│   │   ├── teacher_exercise_service.py      ← NEW (guardrail + agent call)
│   │   └── student_assignment_service.py    ← NEW
│   ├── api/v1/
│   │   ├── teacher.py                       ← NEW router
│   │   └── student_classes.py               ← NEW router
│   └── dependencies.py                      ← MODIFIED (new repo/service deps)

frontend/
├── src/
│   ├── app/
│   │   ├── (teacher)/
│   │   │   ├── layout.tsx                   ← NEW (teacher shell with sidebar)
│   │   │   └── teacher/
│   │   │       ├── dashboard/
│   │   │       │   └── page.tsx             ← NEW (replaces coming-soon stub)
│   │   │       ├── classes/
│   │   │       │   └── [id]/
│   │   │       │       └── page.tsx         ← NEW (class detail)
│   │   │       └── exercises/
│   │   │           └── generate/
│   │   │               └── page.tsx         ← NEW (generation + assignment)
│   │   └── (student)/
│   │       └── exercises/
│   │           └── [id]/
│   │               └── page.tsx             ← NEW (student exercise view)
│   ├── components/
│   │   ├── auth/
│   │   │   └── register-form.tsx            ← MODIFIED (add role selector)
│   │   ├── teacher/
│   │   │   ├── TeacherNavLinks.tsx          ← NEW
│   │   │   ├── ClassCard.tsx                ← NEW
│   │   │   ├── StudentSearchModal.tsx       ← NEW
│   │   │   ├── ExerciseGeneratorForm.tsx    ← NEW
│   │   │   ├── ExercisePreview.tsx          ← NEW
│   │   │   └── AssignClassModal.tsx         ← NEW
│   │   └── student/
│   │       ├── InvitationCard.tsx           ← NEW
│   │       ├── AssignedExerciseCard.tsx     ← NEW
│   │       └── ExerciseQuestionView.tsx     ← NEW
│   ├── hooks/
│   │   ├── useTeacherClasses.ts             ← NEW
│   │   ├── useExerciseGeneration.ts         ← NEW
│   │   ├── useStudentInvitations.ts         ← NEW
│   │   └── useAssignedExercises.ts          ← NEW
│   └── lib/api/
│       ├── teacher.ts                       ← NEW (fetch helpers)
│       └── student-classes.ts               ← NEW (fetch helpers)
```

**Structure Decision**: Web application (Option 2). Backend in `backend/`, frontend in `frontend/`. All new files follow established patterns from F13–F17.

---

## Phase 0: Research Summary

Research completed. All unknowns resolved. See [research.md](./research.md) for full findings.

| Unknown | Resolution |
|---------|-----------|
| Exercise Agent bypass Triage | Direct `Runner.run(get_exercise_agent(), prompt, context)` |
| Multi-question exercise schema | New `teacher_generated_exercises` table + `TeacherExerciseResponse` |
| Teacher prompt guardrail | New `teacher_exercise_guardrail` (LLM-based, structured output) |
| Per-question AI review | Code Review Agent via direct `Runner.run()` |
| Role protection | Existing `require_role(['teacher'])` dependency |
| Teacher frontend shell | New `(teacher)/layout.tsx` + `TeacherNavLinks` component |
| Student sidebar extension | Add Assigned + Invitations to `NavLinks` |
| Duplicate prevention | DB unique constraints + service-layer 409 responses |

---

## Phase 1: Design

### Data Model

See [data-model.md](./data-model.md) for full entity definitions.

**New tables**:

| Table | Purpose |
|-------|---------|
| `classes` | Teacher-owned named class groups |
| `class_memberships` | Student↔class relationship (pending/accepted/declined) |
| `teacher_generated_exercises` | Multi-question exercises created by teachers |
| `class_exercises` | Assignment of an exercise to a class |
| `class_exercise_submissions` | Student submission per class exercise |
| `question_reviews` | Per-question AI review within a submission |
| `teacher_notifications` | DB record on student submission (UI in F22) |

### API Contracts

See [contracts/](./contracts/) for full OpenAPI schemas.

**Teacher router** (`/api/v1/teacher/*` — role: teacher only):
- `POST /classes` — create class
- `GET /classes` — list teacher's classes
- `GET /classes/{class_id}` — class detail with member list
- `GET /students/search?q=` — search students by name/email
- `POST /classes/{class_id}/invitations` — invite student to class
- `POST /exercises/generate` — validate prompt + generate exercise (streaming)
- `POST /exercises/{exercise_id}/assign` — assign exercise to class

**Student classes router** (`/api/v1/student/classes/*` — role: student only):
- `GET /invitations` — list pending invitations
- `PATCH /invitations/{invitation_id}` — accept or decline
- `GET /memberships` — list accepted classes with teacher names
- `GET /assigned-exercises` — all exercises assigned across all classes
- `GET /assigned-exercises/{class_exercise_id}` — exercise detail
- `POST /assigned-exercises/{class_exercise_id}/review` — AI review for one question
- `POST /assigned-exercises/{class_exercise_id}/submit` — submit all reviewed questions

### Key Service Logic

**TeacherExerciseService.generate(prompt: str)**:
1. Call `teacher_exercise_guardrail(prompt)` → returns `{is_valid, missing, message}`
2. If not valid: raise `400` with `{code: "PROMPT_INVALID", missing: [...], message}`
3. Build `TeacherExerciseGenerationRequest` with prompt
4. `Runner.run(get_exercise_agent_for_teacher(), prompt, context=ctx)` → `TeacherExerciseResponse`
5. Persist `TeacherGeneratedExercise` to DB via repo
6. Return exercise id + questions for preview

**StudentAssignmentService.submit(class_exercise_id, student_id)**:
1. Verify all questions have a `QuestionReview` in current session
2. Calculate `overall_score = mean(question_reviews.grade)`
3. Mark `ClassExerciseSubmission.status = 'submitted'`, set `submitted_at`
4. Insert `TeacherNotification(teacher_id, student_id, class_exercise_submission_id)`
5. Return `{score, submitted_at}`

### Quickstart

See [quickstart.md](./quickstart.md) for dev setup steps.

---

## Post-Design Constitution Check

| Principle | Status | Notes |
|-----------|--------|-------|
| 7 new tables — all via Alembic | ✅ PASS | Single migration file |
| Repository pattern maintained | ✅ PASS | 4 new repos; no raw queries in routes/services |
| Streaming for AI generation | ✅ PASS | `StreamingResponse` for exercise generation; SSE events for progress |
| LLM abstraction layer | ✅ PASS | All agent calls via `Runner.run()` + `LlmClient` factory |
| Auth guards on all new routes | ✅ PASS | Teacher: `require_role(['teacher'])`; Student: `require_role(['student'])` |
| Monaco reused via next/dynamic | ✅ PASS | Imported from existing editor component |
| No business logic in route handlers | ✅ PASS | Services contain all logic; routes delegate |

---

## Complexity Tracking

No constitution violations requiring justification.

---

## Risks and Follow-ups

1. **Exercise Agent output format**: The existing `ExerciseAgentResponse` is single-question. A new `TeacherExerciseResponse` schema must be registered before the agent is built — verify `output_type` is recognised by the agent SDK version in use.
2. **Teacher notification table**: Ensure `teacher_id` is always resolvable from `class → teacher_id` at submit time; guard against deleted teacher accounts with `SET NULL` on FK.
3. **Student sidebar nav**: The `NavLinks` component is shared between desktop and mobile sidebars — adding tabs must be tested in both contexts and on small screens.

📋 Architectural decision detected: Separate `teacher_generated_exercises` table vs extending `exercises_agent` for multi-question teacher exercises — Document reasoning and tradeoffs? Run `/sp.adr teacher-exercise-table-separation`
