---
name: 0015-fix-exercise-generator-placeholder-title-topic
description: Fix LLM returning ":" as placeholder values for title and topic in teacher exercise generation
metadata:
  type: green
  feature: 018-teacher-dashboard
  date: 2026-05-19
  branch: 018-teacher-dashboard
  user: Muhammad
---

## Prompt

the agent is not giving proper structured response when generating exercise 
Exercise generation failed: Invalid JSON when parsing {"title":":","topic":":","difficulty":"beginner","target_module":"data_structures","questions":[...]} for TypeAdapter(TeacherMultiExerciseResponse); 2 validation errors for TeacherMultiExerciseResponse title Value error, Field must not be empty or a placeholder [type=value_error, input_value=':', input_type=str] topic Value error, Field must not be empty or a placeholder [type=value_error, input_value=':', input_type=str]

## Response

Root cause: the LLM was interpreting the JSON schema and outputting `:` as a literal value for `title` and `topic` fields — a common failure mode when the model confuses JSON key-value syntax with schema descriptions.

### Changes to `backend/src/services/teacher_exercise_service.py`

1. **Added `_EXERCISE_EXAMPLE`** — a concrete JSON example embedded in the agent instructions so the model can see exactly what valid `title` and `topic` values look like.

2. **Updated agent instructions** — explicitly stated that `title` and `topic` must be "real descriptive text" with examples, and included `NEVER just ':' or empty` guard language.

3. **Added retry logic in `generate()`** — on the first validation failure (e.g. placeholder values), retries once with an augmented prompt that includes an explicit REMINDER about the title/topic fields.

## Files Modified

- `backend/src/services/teacher_exercise_service.py`
