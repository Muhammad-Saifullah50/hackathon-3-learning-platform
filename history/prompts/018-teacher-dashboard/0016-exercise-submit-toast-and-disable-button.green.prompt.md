---
name: 0016-exercise-submit-toast-and-disable-button
description: Show success toast and permanently disable submit button after exercise submission
metadata:
  type: green
  feature: 018-teacher-dashboard
  date: 2026-05-19
  branch: 018-teacher-dashboard
  user: Muhammad
---

## Prompt

after submitting exercise disable the button and also show a toast that exercise has been submitted

## Response

### Changes

**`frontend/src/hooks/useAssignedExercises.ts`**
- Imported `toast` from `sonner`
- After successful `submitExercise`, fires `toast.success('Exercise submitted!')` with the score and teacher-notification note
- On submission error, fires `toast.error('Submission failed')` with the error message

**`frontend/src/components/student/ExerciseWorkspace.tsx`**
- Added `isSubmitted` to the button's `disabled` condition so it stays disabled after submission completes (before the UI transitions to the submitted view)

## Files Modified

- `frontend/src/hooks/useAssignedExercises.ts`
- `frontend/src/components/student/ExerciseWorkspace.tsx`
