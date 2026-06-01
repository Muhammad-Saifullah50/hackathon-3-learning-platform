# Feature Specification: Frontend Foundation & Student Dashboard

**Feature Branch**: `013-frontend-foundation`
**Created**: 2026-05-09
**Status**: Draft
**Input**: User description: "Scaffold the entire Next.js frontend with all user-facing pages including auth pages. Configure Better Auth. Develop the frontend with real data and proper designed UI. Must support both light and dark modes defaulting to system preference. Scope includes: Next.js setup, design system, Better Auth, auth pages, student layout, Student Dashboard (full real data), and stub pages for chat/progress/quiz. No teacher pages."

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Student Registers and Reaches the Dashboard (Priority: P1)

A prospective student visits the platform for the first time. They create an account by providing their name, email address, and password. On success they are immediately signed in and land on their personalised Student Dashboard, which shows all eight Python curriculum modules at 0% mastery with an encouraging empty state.

**Why this priority**: Registration and first login are the entry gate to every other feature. Nothing else is testable without a working auth + dashboard path.

**Independent Test**: Can be fully tested by completing the registration form with valid credentials, verifying the redirect to `/dashboard`, and confirming all eight modules render with 0% mastery.

**Acceptance Scenarios**:

1. **Given** an unregistered visitor on `/register`, **When** they submit a valid name, email, and password, **Then** their account is created, they are signed in, and they are redirected to `/dashboard`.
2. **Given** a student on `/register`, **When** they submit an email that is already registered, **Then** an inline error message clearly states the email is taken and the form is not submitted.
3. **Given** a brand-new student on `/dashboard`, **When** the page loads, **Then** all eight curriculum modules are shown as cards with 0% mastery in the Beginner (red) state and an encouraging "Start your learning journey" prompt is visible.
4. **Given** a student on `/register`, **When** they submit a password that does not meet complexity rules, **Then** a clear, specific validation message appears before submission.

---

### User Story 2 — Returning Student Signs In and Views Their Progress (Priority: P1)

A returning student navigates to the login page. They enter their credentials and are taken straight to the Student Dashboard, where they can see their current mastery levels across all eight modules, their learning streak, overall mastery score, any flagged weak areas, and at least one personalised recommendation.

**Why this priority**: This is the daily-use flow for every student. The dashboard must surface actionable progress information from real backend data on every visit.

**Independent Test**: Can be fully tested by logging in with a seeded student account that has progress data, and verifying that module cards, streak, overall mastery, weak areas, and recommendations all render with correct values.

**Acceptance Scenarios**:

1. **Given** a registered student on `/login`, **When** they submit valid credentials, **Then** they are redirected to `/dashboard` within 3 seconds.
2. **Given** a logged-in student on `/dashboard`, **When** the page loads, **Then** each of the eight module cards shows the correct mastery percentage and the corresponding colour-coded level indicator (red/yellow/green/blue).
3. **Given** a logged-in student on `/dashboard`, **When** the page loads, **Then** their current streak (consecutive active days) is prominently displayed.
4. **Given** a logged-in student on `/dashboard`, **When** the page loads, **Then** their overall mastery percentage across all modules is displayed.
5. **Given** a logged-in student on `/dashboard**, **When** the backend returns weak areas and recommendations, **Then** at least one weak area and one recommendation are surfaced on the page.
6. **Given** a visitor who attempts to access `/dashboard` without being signed in, **When** the page is requested, **Then** they are immediately redirected to `/login`.

---

### User Story 3 — Student Navigates Between Platform Sections (Priority: P2)

A logged-in student uses the persistent sidebar navigation to move between the Dashboard, AI Tutor Chat, Progress, and Quiz sections of the platform. Chat, Progress, and Quiz pages are available as navigable destinations that acknowledge they are under development while preserving the full layout.

**Why this priority**: Navigation scaffolding must exist before individual sections can be built out. Students need to understand the platform's structure even if features are not fully live.

**Independent Test**: Can be fully tested by clicking each navigation item and verifying the correct route is reached, the layout is intact, the active state is highlighted, and the stub content is shown for non-dashboard pages.

**Acceptance Scenarios**:

1. **Given** a logged-in student, **When** they click "AI Tutor Chat" in the sidebar, **Then** they navigate to `/chat`, which shows the full student layout and a placeholder message.
2. **Given** a logged-in student, **When** they click "Progress" in the sidebar, **Then** they navigate to `/progress` with the full student layout and a placeholder.
3. **Given** a logged-in student, **When** they click "Quiz" in the sidebar (or follow a link to `/quiz/[lessonId]`), **Then** the quiz page renders with the full student layout and a placeholder.
4. **Given** a logged-in student on any page, **When** they look at the sidebar, **Then** the currently active section is visually highlighted.
5. **Given** a logged-in student on the dashboard, **When** they click a "Start Lesson" quick-action button on a module card, **Then** they are taken to the AI Tutor Chat page (stub).
6. **Given** a logged-in student on the dashboard, **When** they click a "Take Quiz" quick-action button on a module card, **Then** they are taken to the Quiz page stub for that module.

---

### User Story 4 — Student Resets a Forgotten Password (Priority: P2)

A student who has forgotten their password clicks "Forgot password?" on the login page, enters their email address, and receives a reset link. They click the link, enter a new password, and can then sign in with it.

**Why this priority**: Password reset is a critical self-service flow that prevents locked-out users from needing support intervention.

**Independent Test**: Can be tested by requesting a password reset for a seeded account, following the email link to `/reset-password?token=...`, setting a new password, and verifying that login with the new password succeeds.

**Acceptance Scenarios**:

1. **Given** a student on `/forgot-password`, **When** they enter a registered email and submit, **Then** a confirmation message is shown and a password-reset email is sent.
2. **Given** a student who clicks a valid reset link, **When** they land on `/reset-password`, **Then** they can set a new password and are redirected to `/login` on success.
3. **Given** a student who clicks an expired or invalid reset link, **When** they land on `/reset-password`, **Then** a clear error message explains the link is invalid and offers to request a new one.
4. **Given** a student on `/forgot-password`, **When** they enter an unregistered email, **Then** the same success message is shown (no email enumeration).

---

### User Story 5 — Interface Respects Light/Dark Mode Preference (Priority: P3)

The application automatically adopts the student's operating system colour scheme preference (light or dark) on first load. Students can also toggle the preference manually at any time using a control in the navigation bar, and their choice persists across page navigations and browser sessions.

**Why this priority**: Accessibility and comfort, especially for students who code in dark environments. Default-to-system ensures no jarring flash for any user.

**Independent Test**: Can be tested by loading the app with OS set to dark mode and verifying the dark theme activates, then toggling to light and confirming the preference is saved after a page refresh.

**Acceptance Scenarios**:

1. **Given** a user whose operating system is set to dark mode, **When** they open the application for the first time, **Then** the dark theme is applied with no flash of light content.
2. **Given** a user whose operating system is set to light mode, **When** they open the application, **Then** the light theme is applied.
3. **Given** a logged-in student, **When** they toggle the theme in the navigation bar, **Then** the theme switches immediately across the entire interface.
4. **Given** a student who has manually toggled the theme, **When** they refresh the page, **Then** their selected theme is preserved.

---

### User Story 6 — Visitor Discovers the Platform via Landing Page (Priority: P2)

A first-time visitor lands on the root URL (`/`) before signing in. They see a polished, full-featured marketing page that demonstrates the complete LearnPyByAI workflow end-to-end: the AI tutor conversation flow, the live code sandbox, the quiz and progress system, and the teacher monitoring experience. Compelling copy and clear CTAs lead them to register or log in.

**Why this priority**: The landing page is the product's first impression for every new user. It must immediately communicate the platform's value — AI-powered Python tutoring — and convert visitors into registered students. Without it the platform has no discoverable entry point beyond a raw `/login` URL.

**Independent Test**: Can be fully tested by visiting `/` while logged out and verifying all sections render, animations play, all CTA links lead to `/register` or `/login`, and the page is fully responsive on mobile.

**Acceptance Scenarios**:

1. **Given** an unauthenticated visitor on `/`, **When** the page loads, **Then** a hero section renders with the platform name, a one-sentence value proposition, and prominent "Get Started" and "Sign In" CTAs.
2. **Given** a visitor on `/`, **When** they scroll, **Then** they encounter a workflow section that shows the full student journey: ask a question → AI explains → write code → sandbox runs it → take a quiz → mastery updates.
3. **Given** a visitor on `/`, **When** they scroll, **Then** they see the 8 Python curriculum modules presented as visual cards with their topics.
4. **Given** a visitor on `/`, **When** they scroll, **Then** they see a features/benefits section covering the AI tutor, code sandbox, progress tracking, and teacher alerts.
5. **Given** a visitor on `/`, **When** they click any "Get Started" or "Sign Up" CTA, **Then** they are taken to `/register`.
6. **Given** an authenticated student on `/`, **When** the page is requested, **Then** they are redirected directly to `/dashboard` (landing page is for unauthenticated visitors only).
7. **Given** a visitor on a mobile screen (< 768 px), **When** the page loads, **Then** all sections reflow correctly with no horizontal overflow and text remains readable.

---

### User Story 7 — Teacher Sees "Coming Soon" After Login (Priority: P3)

A user with the teacher role signs in. They are not shown the student dashboard. Instead they see a clear, friendly placeholder page that acknowledges their teacher status and informs them the teacher portal is under development.

**Why this priority**: Prevents teachers from accidentally seeing student-only content and gives a professional experience even before teacher features are built.

**Independent Test**: Can be tested by logging in with a seeded teacher account and verifying the "coming soon" placeholder is shown instead of the student dashboard.

**Acceptance Scenarios**:

1. **Given** a teacher account, **When** they log in, **Then** they are redirected to a `/teacher/coming-soon` page instead of `/dashboard`.
2. **Given** a teacher on `/teacher/coming-soon`, **When** they directly navigate to `/dashboard`, **Then** they are redirected back to `/teacher/coming-soon`.
3. **Given** a teacher on `/teacher/coming-soon`, **When** they click "Sign out", **Then** their session is ended and they are returned to `/login`.

---

### Edge Cases

- What happens when the backend progress API returns no data for a new user? → All eight modules render at 0% mastery with an empty-state prompt.
- What happens when the backend is unavailable during dashboard load? → A clear error state with a retry button is shown; the layout and navigation remain functional. Each dashboard section uses a React `<Suspense>` boundary with a skeleton screen so partial data can still render while other sections recover.
- What happens when a student's access token expires while they are on the dashboard? → The session is silently refreshed using the refresh token; if refresh also fails, the student is redirected to `/login` with a "session expired" message.
- What happens when a student tries to register with a password that has already been compromised (HIBP check by the backend)? → The backend returns a 400 error with a specific message; the frontend displays it inline without clearing the form.
- What happens when the reset-password token in the URL is missing or malformed? → The page shows an error message immediately on load without allowing form submission.
- What happens when a student signs in on a page they were previously trying to reach? → They are redirected to their originally intended destination, not always `/dashboard`.

---

## Clarifications

### Session 2026-05-09

- Q: How should the Student Dashboard fetch its data (mastery scores, streak, weak areas, recommendations)? → A: Server Components / SSR — fetch data server-side using Next.js App Router React Server Component (RSC) patterns; no client-side state for the initial load.
- Q: How should theme preference be persisted to avoid a flash on SSR? → A: HTTP cookie — write preference to a cookie on toggle; Next.js middleware or RSC reads it before rendering to apply the correct theme class server-side.
- Q: Must the student layout be fully responsive on mobile devices (< 768 px)? → A: Fully responsive — sidebar collapses to a hamburger drawer on screens narrower than 768 px; dashboard module cards reflow to a single column.
- Q: What loading state pattern should be used while SSR dashboard data is being fetched? → A: Skeleton screens via React Suspense — each dashboard section (module cards, streak, recommendations) streams in with a skeleton placeholder until its data resolves.
- Q: What accessibility standard must the UI meet? → A: WCAG 2.1 AA — minimum contrast ratios (4.5:1 for text, 3:1 for UI components), full keyboard navigation, and ARIA labelling for all interactive elements.

---

## Requirements *(mandatory)*

### Functional Requirements

**Authentication**

- **FR-001**: Students MUST be able to create an account with a display name, email address, and password via a registration form.
- **FR-002**: The system MUST validate registration inputs client-side (required fields, email format, password complexity) before submission.
- **FR-003**: Students MUST be able to sign in with their email and password.
- **FR-004**: The system MUST redirect authenticated users who visit `/login` or `/register` to `/dashboard`.
- **FR-005**: The system MUST protect all routes under `/(student)` — unauthenticated requests MUST be redirected to `/login`.
- **FR-006**: The system MUST redirect teachers away from student-only routes to `/teacher/coming-soon`.
- **FR-007**: Students MUST be able to sign out from any page; signing out clears the session and redirects to `/login`.
- **FR-008**: Students MUST be able to request a password-reset email from the `/forgot-password` page.
- **FR-009**: Students MUST be able to set a new password by visiting the link sent in the reset email.
- **FR-010**: The system MUST NOT reveal whether an email address is registered when processing password-reset requests.

**Student Dashboard**

- **FR-011**: The dashboard MUST fetch and display all eight Python curriculum modules as individual cards. Data MUST be fetched server-side via a React Server Component using the Next.js App Router; no client-side fetch is required for the initial render.
- **FR-012**: Each module card MUST display: module name, mastery percentage, mastery level label, and a colour-coded indicator (Beginner = red, Learning = yellow, Proficient = green, Mastered = blue).
- **FR-013**: The dashboard MUST display the student's current learning streak in consecutive active days.
- **FR-014**: The dashboard MUST display the student's overall mastery percentage across all modules.
- **FR-015**: The dashboard MUST display identified weak areas (topics below the Proficient threshold).
- **FR-016**: The dashboard MUST display at least one personalised learning recommendation when available.
- **FR-017**: Each module card MUST provide a "Start Lesson" action that navigates to the Chat stub and a "Take Quiz" action that navigates to the Quiz stub.
- **FR-018**: When no progress data exists for a student, the dashboard MUST show all eight modules at 0% with an encouraging empty-state message.

**Navigation & Layout**

- **FR-019**: The student layout MUST include a persistent sidebar with links to: Dashboard, AI Tutor Chat, Progress, and Quiz. On screens narrower than 768 px, the sidebar MUST collapse to a hamburger-triggered drawer; dashboard module cards MUST reflow to a single column.
- **FR-020**: The active navigation item MUST be visually distinguished from inactive items.
- **FR-021**: The navigation MUST include the student's display name and a sign-out action.
- **FR-022**: The navigation MUST include a theme toggle control.

**Landing Page**

- **FR-023**: The root URL `/` MUST render a public landing page for unauthenticated visitors; authenticated students MUST be redirected to `/dashboard`.
- **FR-024**: The landing page MUST include a hero section with the platform name, a concise value proposition, and "Get Started" (→ `/register`) and "Sign In" (→ `/login`) CTAs.
- **FR-025**: The landing page MUST include a workflow section that illustrates the full student journey: question → AI explanation → code sandbox → quiz → mastery update — using static mockups or animated step cards.
- **FR-026**: The landing page MUST display all 8 Python curriculum modules as visual cards with their names and topic icons.
- **FR-027**: The landing page MUST include a features section highlighting: AI Tutor, Code Sandbox, Progress Tracking, and Teacher Alerts.
- **FR-028**: The landing page MUST be fully responsive on mobile (< 768 px) with no horizontal overflow.
- **FR-029**: The landing page MUST respect the light/dark theme preference and use the same design tokens as the rest of the application.

**Stub Pages**

- **FR-030**: `/chat`, `/progress`, and `/quiz/[lessonId]` MUST exist as routable pages within the full student layout, displaying a clear "coming soon" placeholder.

**Theming**

- **FR-031**: The application MUST support light mode, dark mode, and system-preference mode.
- **FR-032**: The default theme on first load MUST be the user's operating system preference.
- **FR-033**: A manually selected theme MUST persist across page refreshes and navigation. The preference MUST be stored in an HTTP cookie so that Next.js middleware can read and apply it server-side before the first render, eliminating any flash of the wrong theme.

---

### Key Entities

- **Student Session**: Represents an authenticated student — holds identity (display name, email, role) and is used by route protection middleware and the UI to personalise content.
- **Module Progress Card**: Represents a student's standing in one of the eight curriculum modules — mastery score (0–100%), mastery level (Beginner / Learning / Proficient / Mastered), and actionable quick-links.
- **Learning Streak**: The count of consecutive days on which a student has been active on the platform.
- **Weak Area**: A curriculum topic where the student's mastery score falls below the Proficient threshold (71%), surfaced on the dashboard to guide study focus.
- **Recommendation**: A personalised prompt suggesting what the student should work on next, derived from their progress data.

---

## Assumptions

- Self-registration always creates a **student** account; teacher accounts are created by an administrator out of band.
- Email verification is **not** required before a student can access the dashboard (MVP convenience); the verification banner may be shown as informational only.
- The password-reset flow relies on email delivery being configured in the backend; in local development this uses MailHog on `localhost:1025`.
- "Module" identity and names are fixed (8 seeded modules); no module CRUD is in scope.
- The streak counter is sourced from the backend progress summary endpoint and displayed as-is; streak logic is owned by the backend.
- Redirect-after-login uses the originally requested URL stored in query params (e.g. `/login?next=/progress`).

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A new student can complete registration and see their dashboard in under 2 minutes on first visit.
- **SC-002**: A returning student's dashboard — including all eight module cards and progress data — is fully visible within 3 seconds of sign-in on a standard broadband connection.
- **SC-003**: All eight curriculum modules render correctly with colour-coded mastery indicators on every dashboard load, for both new users (0% state) and users with progress data.
- **SC-004**: An unauthenticated user who requests any protected route is redirected to `/login` within 1 second.
- **SC-005**: A student who has forgotten their password can successfully reset it and regain access within 5 minutes end-to-end.
- **SC-006**: The application renders correctly and is fully usable in both light and dark modes with no layout breakage or unreadable contrast. All colour pairs MUST meet WCAG 2.1 AA minimum contrast ratios (4.5:1 for normal text, 3:1 for large text and UI components) in both themes.
- **SC-007**: The theme applied on first load matches the user's operating system preference with no visible flash of the wrong theme.
- **SC-008**: All four navigation destinations (Dashboard, Chat, Progress, Quiz) are reachable in one click from any student page.
