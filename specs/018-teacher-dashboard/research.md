# Research: 018-Teacher Dashboard

**Phase**: Phase 0 — Research  
**Date**: 2026-05-18  
**Branch**: `018-teacher-dashboard`

---

## 1. Exercise Agent Direct Invocation

**Decision**: Invoke the Exercise Agent directly via `Runner.run()` with a structured prompt, bypassing the Triage Agent.

**Rationale**: The Triage Agent is designed for student chat routing. Teacher exercise generation is a distinct entry point that already knows the target agent. Bypassing Triage eliminates unnecessary classification latency and avoids mixing teacher workflows with the student chat session model.

**How it works today**: `agents.py` builds an `exercise_agent` using `Agent(name="Exercise", output_type=ExerciseAgentResponse, ...)`. The Triage Agent hands off to it via `handoff()`. For teacher use, we create a standalone runner call:

```python
result = await Runner.run(exercise_agent, prompt, context=lf_context)
```

**Gap**: The existing `ExerciseAgentResponse` schema (in `src/schemas/agent_responses.py`) returns a single exercise with `description`, `starter_code`, `test_cases`. F18 requires **multi-question exercises** (`questions: list[{description, starter_code}]`). A new response schema `TeacherExerciseResponse` is needed.

**Alternatives considered**:
- Route through Triage with a special "teacher" surface flag → rejected (adds coupling, Triage prompt not designed for teacher intent)
- Separate LLM call without agents SDK → rejected (bypasses established agent patterns from constitution)

---

## 2. Role-Based Middleware (FastAPI)

**Decision**: Use the existing `require_role(['teacher'])` dependency factory from `src/auth/dependencies.py` for all teacher API routes.

**Rationale**: The factory already exists and is tested. No new infrastructure needed.

**Pattern**:
```python
# In route definition
@router.post("/classes", dependencies=[Depends(require_role(['teacher']))])
async def create_class(...):
    ...

# Or as parameter (when current_user is needed)
@router.get("/students/search")
async def search_students(
    current_user: User = Depends(require_role(['teacher'])),
    ...
):
```

**Frontend role protection**: The `(student)/layout.tsx` pattern redirects non-students. The `(teacher)/layout.tsx` (to be created) will redirect non-teachers to `/dashboard`:

```tsx
if (!session || session.user.role !== 'teacher') {
  redirect('/dashboard')
}
```

**Alternatives considered**:
- Middleware-level route prefix protection → rejected (adds complexity; dependency injection is simpler and consistent with existing codebase)

---

## 3. Multi-Question Exercise Structure

**Decision**: Create a new `teacher_generated_exercises` table (separate from `exercises_agent`) to store teacher-authored multi-question exercises.

**Rationale**: The `exercises_agent` table is built for single-question sandbox exercises with `test_cases` JSONB for automated grading. F18 teacher exercises are fundamentally different: multi-question, AI-reviewed (not auto-graded via test cases), and tied to class assignment. Sharing the table would require nullable columns and conditional logic that violates single-responsibility.

**Schema for `questions` JSONB column**:
```json
[
  {
    "index": 0,
    "description": "Write a function that returns the sum of two numbers",
    "starter_code": "def add(a, b):\n    pass"
  },
  {
    "index": 1,
    "description": "Write a list comprehension that squares each number",
    "starter_code": "numbers = [1, 2, 3, 4, 5]\nresult = ..."
  }
]
```

**Alternatives considered**:
- Extend `exercises_agent` with nullable `questions` column → rejected (violates SRP; conflates auto-graded and AI-reviewed exercises)
- Separate `exercise_questions` relational table → rejected (overkill for MVP; JSONB is sufficient and aligns with existing patterns like `quiz_sessions.questions`)

---

## 4. Prompt Guardrail Validation for Exercise Generation

**Decision**: Use a lightweight LLM call (via `LlmClient`) to validate teacher prompts before generation, returning structured feedback on missing fields.

**Rationale**: Simple regex/keyword matching cannot reliably detect whether a prompt specifies "difficulty" (could be "easy", "for beginners", "challenging") or "module" (could be "loops", "for loops", "iteration"). An LLM validator is more robust and already consistent with the codebase's agent-first approach.

**Validation schema**:
```python
class ExercisePromptValidation(BaseModel):
    is_valid: bool
    is_python_topic: bool
    missing: list[str]  # ["topic", "difficulty", "module"]
    message: str        # Human-readable explanation
```

**Guardrail prompt** (lightweight, cached):
```
Given this exercise generation prompt: "{prompt}"
Evaluate if it specifies: topic, difficulty level, and a Python module/concept area.
Also confirm it is asking for a Python programming exercise.
Return JSON: {is_valid, is_python_topic, missing: [], message}
```

**Caching**: Results are NOT cached per-request (prompts are free-form); guardrail is rate-limited to 5 req/min via existing `slowapi` pattern.

**Alternatives considered**:
- Regex keyword matching → rejected (too brittle; "beginner-friendly" or "challenging" wouldn't match "difficulty")
- Build guardrail into the Exercise Agent system prompt → rejected (exercise agent already invoked after validation; mixing concerns)

---

## 5. AI Review per Exercise Question

**Decision**: Reuse the Code Review Agent's grading capability (via direct `Runner.run()`) for per-question AI review. Return `grade` (0–100 Float) + `review` (Text).

**Rationale**: The Code Review Agent (`code_review_agent` in `agents.py`) already returns `CodeReviewResponse` with structured feedback. Reusing it avoids duplicating grading logic.

**Pattern**:
```python
review_prompt = f"""
Module question: {question['description']}
Student code:
{student_code}

Grade this solution out of 100 and provide specific feedback.
"""
result = await Runner.run(code_review_agent, review_prompt, context=ctx)
```

**Alternatives considered**:
- Use Exercise Agent for grading → rejected (Exercise Agent generates, not grades; role separation)
- Build separate grading endpoint → rejected (unnecessary duplication of existing agent)

---

## 6. Student Sidebar Extension

**Decision**: Add `Assigned` and `Invitations` as new tabs to the existing `NavLinks` component by passing additional tab configuration. No structural redesign.

**Rationale**: The `NavLinks` component in `frontend/src/components/layout/nav-links.tsx` already renders a list of navigation links for the student layout. Adding new links is additive and safe.

**Alternatives considered**:
- Separate sidebar component for class features → rejected (creates duplication; existing NavLinks handles the pattern)

---

## 7. Teacher Notification Record (DB Write Only)

**Decision**: Create a `teacher_notifications` table with a simple INSERT on student submission. No real-time push in F18 (deferred to F22).

**Schema**: `{id, teacher_id, student_id, class_exercise_submission_id, type='exercise_submitted', created_at}`

**Rationale**: Spec explicitly states "DB write only, UI deferred to F22". Lightweight insert in the submit endpoint is sufficient.

---

## 8. Duplicate Prevention Logic

**Decision**: Enforce uniqueness at DB level (unique constraints) + surface friendly messages at service layer.

- `class_memberships`: unique on `(class_id, student_id)` — prevents duplicate invitations
- `class_exercises`: unique on `(class_id, exercise_id)` — prevents duplicate assignments
- `class_exercise_submissions`: unique on `(class_exercise_id, student_id)` — prevents resubmission

Service layer catches `IntegrityError` from SQLAlchemy and returns appropriate 409 responses.

---

## Resolved Unknowns Summary

| Unknown | Resolution |
|---------|-----------|
| Exercise Agent invocation (bypass Triage) | Direct `Runner.run(exercise_agent, prompt, context)` |
| Multi-question exercise format | New `teacher_generated_exercises` table with `questions` JSONB |
| Prompt guardrail mechanism | Lightweight LLM validation call with structured output |
| Per-question AI review | Reuse Code Review Agent via direct `Runner.run()` |
| Role-based route protection | Existing `require_role(['teacher'])` dependency |
| Frontend role guard (teacher routes) | New `(teacher)/layout.tsx` mirroring student layout pattern |
| Student sidebar tabs | Extend `NavLinks` with `Assigned` + `Invitations` links |
| Duplicate prevention | DB unique constraints + service-layer 409 responses |
