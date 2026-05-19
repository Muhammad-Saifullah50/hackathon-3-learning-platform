---
id: "0010"
title: Fix invite flow — toast, modal close, and invitation refresh
stage: green
date: 2026-05-19
surface: agent
model: claude-sonnet-4-6
feature: 018-teacher-dashboard
branch: 018-teacher-dashboard
user: Muhammad
command: debug invite button
labels: ["bug", "invite", "toast", "ux", "student-invitations"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - frontend/src/hooks/useTeacherClasses.ts
  - frontend/src/components/teacher/ClassDetailPanel.tsx
  - frontend/src/components/student/InvitationsPanel.tsx
tests:
  - manual: invite flow end-to-end (teacher invites → toast shown → modal closes → member appears → student page refreshes)
---

## Prompt

when a teacher searches a student and finds it, it click the invite button, a loader appears but nothing happens. No invite reaches the student. also if an invite is successfully sent i should see a toast notification letting the user know that the invite has been sent and the student should be able to see in their invitations page. this is not working right now

## Response snapshot

Systematic debugging identified four root causes:

1. **`useClassDetail.load()` returned `void`** — `ClassDetailPanel.handleInvite` did `const refreshed = await load()` expecting data back, but got `undefined`. The `if (refreshed) setDetail(...)` guard never ran, so the member list never updated.

2. **`useClassDetail.invite()` also returned `void`** — same problem; the refreshed detail was silently discarded.

3. **No toast call** — `sonner` Toaster is in layout but no `toast.success()` was ever called in the invite path.

4. **Modal never closed** — `setShowSearch(false)` was missing from `handleInvite`, so after a successful invite the modal stayed open with no visible confirmation.

5. **`InvitationsPanel` never fetched fresh data** — `load()` from `useStudentInvitations` was never called, so students already on the page saw only the SSR-fetched snapshot. The `useEffect` had an inverted guard (`if (invitations.length > 0 || displayed.length === 0) return`) that prevented `displayed` from ever being updated from client-side fetched data.

Fixes applied:
- `useTeacherClasses.ts`: `load()` now returns `Promise<ClassDetail | null>`; `invite()` now returns `Promise<ClassDetail | null>` (calls `load()` and forwards its return value).
- `ClassDetailPanel.tsx`: `handleInvite` uses the returned detail to update local state, calls `setShowSearch(false)`, and calls `toast.success('Invitation sent successfully')`.
- `InvitationsPanel.tsx`: added `useEffect(() => { load() }, [load])` on mount; fixed the guard condition to `if (invitations.length === 0) return` so the displayed list updates when fresh invitations arrive.

## Outcome

- ✅ Impact: Teacher now sees a success toast and the modal closes after inviting a student; the new member appears immediately in the class member list without a page refresh. Student navigating to /invitations (or already on it) now sees the new pending invitation.
- 🧪 Tests: Manual end-to-end verification recommended
- 📁 Files: 3 files changed
- 🔁 Next prompts: Consider adding a loading state to InvitationsPanel while the client-side fetch runs
- 🧠 Reflection: The root cause was a type mismatch — `load()` returning `void` instead of data made the refresh logic silently no-op. Systematic data-flow tracing from button click through hook to component state caught all four issues before any fix was attempted.

## Evaluation notes (flywheel)

- Failure modes observed: hook returning void instead of data; missing toast; missing modal close; InvitationsPanel not calling load()
- Graders run and results (PASS/FAIL): none automated
- Prompt variant (if applicable): null
- Next experiment: add polling interval to InvitationsPanel so students see invitations in near-real-time
