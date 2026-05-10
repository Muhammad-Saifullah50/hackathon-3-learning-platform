# Tasks: Frontend Foundation & Student Dashboard

**Feature**: `013-frontend-foundation`
**Branch**: `013-frontend-foundation` | **Date**: 2026-05-09
**Input**: [spec.md](spec.md) · [plan.md](plan.md) · [data-model.md](data-model.md) · [contracts/frontend-backend.md](contracts/frontend-backend.md) · [research.md](research.md) · [quickstart.md](quickstart.md)

**Tech Stack**: TypeScript 5+ / React 19 · Next.js 16 (App Router, Turbopack default) · shadcn/ui (New York) + Tailwind CSS 4 + next-themes · Better Auth 1.x (pg.Pool → Neon) · TanStack Query 5 · Vitest + Playwright

**Tests**: Included — explicitly listed in plan.md Phase 7. Vitest (unit/component) + Playwright (E2E, 6 critical journeys). See Phase 10.

**Organization**: Tasks grouped by user story for independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Parallelizable — different files, no dependencies on incomplete tasks in this phase
- **[Story]**: User story label (US1–US7)
- All file paths are relative to repo root

---

## Phase 1: Setup — Project Scaffold & Design System

**Purpose**: A running Next.js 16 app with full design system (fonts, colours, dark/light mode) before any auth or pages.

- [X] T001 Init Next.js 16 with React 19 and install all project dependencies per `quickstart.md §1` in `frontend/package.json`
- [X] T002 Initialize shadcn/ui (New York style, Stone base, CSS variables, `src/` directory) and configure Tailwind CSS 4 with Warm Code Scholar HSL palette in `frontend/tailwind.config.ts`, `frontend/src/app/globals.css`, `frontend/components.json`
- [X] T003 [P] Configure `next.config.ts` with Turbopack (default in Next.js 16, no flag needed), backend proxy rewrites for `/api/v1/:path*`, and `optimizePackageImports` for `lucide-react` and `recharts` in `frontend/next.config.ts`
- [X] T004 [P] Configure TypeScript strict mode with `@/` path alias, `.prettierrc` (semi:false, singleQuote:true, tabWidth:2), and `.eslintrc.json` extending `eslint-config-next` in `frontend/tsconfig.json`, `frontend/.prettierrc`, `frontend/.eslintrc.json`
- [X] T005 Create root layout loading Google Fonts (Fraunces/Outfit/JetBrains Mono as CSS variables `--font-heading`/`--font-sans`/`--font-mono`), FOUC-prevention inline `<script>` in `<head>` that reads OS preference before first paint, ThemeProvider (`attribute="class"`, `defaultTheme="system"`, `storageKey="theme"`), and QueryProvider in `frontend/src/app/layout.tsx`, `frontend/src/components/providers/theme-provider.tsx`, `frontend/src/components/providers/query-provider.tsx`

**Checkpoint**: `npm run dev` starts on port 3000 with no TypeScript errors; toggling dark/light produces no flash; Fraunces headings render correctly.

---

## Phase 2: Foundational — Better Auth + DB Migration + Middleware

**Purpose**: Core auth infrastructure — session management, DB tables, route protection — that MUST be complete before any user story.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [X] T006 Add Alembic migration creating Better Auth tables (`user` with `role`/`fast_api_id` custom fields, `session` with `fast_api_token` field, `account`, `verification`) in `backend/alembic/versions/20260509_create_better_auth_tables.py`; run `alembic upgrade head` to apply
- [X] T007 [P] Define all TypeScript interfaces (`AuthUser`, `Session`, `ProgressSummary`, `TopicMastery`, `MasteryLevel`, `MasteryColor`, `ModuleCard`, `StreakInfo`, `LoginResponse`, `RegisterResponse`, `ProfileResponse`) in `frontend/src/types/index.ts`
- [X] T008 [P] Create API fetch wrapper `apiFetch<T>()` with 401 token-refresh logic (retry once after refresh; signOut + redirect on refresh failure) and `.env.local.example` with all required variable names (`NEXT_PUBLIC_BACKEND_URL`, `BETTER_AUTH_SECRET`, `BETTER_AUTH_BASE_URL`, `DATABASE_URL`, `NEXT_PUBLIC_APP_URL`) in `frontend/src/lib/api.ts`, `frontend/.env.local.example`
- [X] T009 Configure Better Auth server instance with `pg.Pool` connected to Neon, `disableSignUp: true` (registration handled by proxy), FastAPI credential proxy in `password.verify` (calls `POST /api/auth/login`, stores `fastApiToken` in session metadata), and custom `role`/`fastApiId` user fields in `frontend/src/lib/auth.ts`
- [X] T010 Create Better Auth catch-all route handler (`toNextJsHandler(auth)`) and dual-record registration proxy that calls FastAPI `POST /api/auth/register` then `auth.api.signUpEmail()` and returns session in `frontend/src/app/api/auth/[...all]/route.ts`, `frontend/src/app/api/register-proxy/route.ts`
- [X] T011 [P] Create Better Auth React client with `baseURL: NEXT_PUBLIC_APP_URL`, exporting `signIn`, `signOut`, `signUp`, and `useSession` in `frontend/src/lib/auth-client.ts`
- [X] T012 Implement Next.js middleware using `getSessionCookie` (cookie-only, no DB hit) to protect all non-public routes (redirect unauthenticated to `/login?next={pathname}`) and redirect authenticated users away from auth pages to `/dashboard`; matcher excludes `_next/static`, `_next/image`, `favicon.ico`, `api/auth` in `frontend/middleware.ts`

**Checkpoint**: Better Auth tables exist in Neon; `auth.api.getSession()` resolves from cookie; unauthenticated `GET /dashboard` redirects to `/login?next=/dashboard`.

---

## Phase 3: User Story 1 — Student Registers and Reaches Dashboard (Priority: P1) 🎯 MVP

**Goal**: Complete registration flow + Student Dashboard showing all 8 curriculum modules at 0% mastery (Beginner / red) with encouraging empty state.

**Independent Test**: Register with `test@example.com / Test@1234` → redirect to `/dashboard` → 8 module cards visible at Beginner (red) with 0% and "Start your learning journey" encouragement message.

- [X] T013 [US1] Create centred card auth layout with logo, WCAG 2.1 AA contrast, no sidebar, light/dark aware in `frontend/src/app/(auth)/layout.tsx`
- [X] T014 [US1] Create `RegisterForm` component with react-hook-form + zod (required name, email format, password ≥ 8 chars with special char), calls `POST /api/register-proxy`, shows inline errors for duplicate email (400) or weak password (400) without clearing form in `frontend/src/components/auth/register-form.tsx`
- [X] T015 [US1] Create register page rendering `RegisterForm` and redirecting to `/dashboard` on successful registration in `frontend/src/app/(auth)/register/page.tsx`
- [X] T016 [P] [US1] Implement `masteryColor(level: MasteryLevel): MasteryColor`, `masteryLevel(score: number): MasteryLevel` (0–40→Beginner, 41–70→Learning, 71–90→Proficient, 91–100→Mastered), `cn()` helper, and `CURRICULUM_MODULES` constant (8 modules: id/displayName/moduleNumber) in `frontend/src/lib/utils.ts`
- [X] T017 [US1] Create `ModuleCard` component displaying module name, mastery percentage, mastery level label, colour-coded Tailwind progress bar (Beginner=red/Learning=amber/Proficient=green/Mastered=blue with WCAG 4.5:1 contrast), "Start Lesson" button (→ `/chat`) and "Take Quiz" button (→ `/quiz/{id}`); animate reveal via `animation-delay: calc(var(--i) * 80ms)` in `frontend/src/components/dashboard/module-card.tsx`
- [X] T018 [US1] Create `ModuleGrid` component merging `CURRICULUM_MODULES` static list with API `topics[]` (matched by topic name), filling missing modules at 0% Beginner; shows "Start your learning journey!" empty-state prompt when all modules at 0%; single-column reflow on < 768px in `frontend/src/components/dashboard/module-grid.tsx`
- [X] T019 [P] [US1] Create `DashboardSkeleton` component with `<Skeleton>` placeholders matching the real layout (8 module card skeletons, streak widget, overview widget, weak-areas panel, recommendations panel) for use in `<Suspense fallback>` in `frontend/src/components/dashboard/dashboard-skeleton.tsx`
- [X] T020 [US1] Create basic `StudentSidebar` with navigation links (Dashboard, Chat, Progress, Quiz), user display name from session, and sign-out button calling `authClient.signOut()` in `frontend/src/components/layout/student-sidebar.tsx`
- [X] T021 [US1] Create basic `TopNav` with logo and page title in `frontend/src/components/layout/top-nav.tsx`
- [X] T022 [US1] Create student layout server component calling `auth.api.getSession({ headers: await headers() })`, redirecting unauthenticated users to `/login` and teachers to `/teacher/coming-soon`, wrapping `children` in `StudentSidebar` + `TopNav` shell in `frontend/src/app/(student)/layout.tsx`
- [X] T023 [US1] Create Dashboard server page with `<Suspense fallback={<DashboardSkeleton />}>` that fetches `GET /api/v1/agents/progress/summary` with `Authorization: Bearer {session.session.fastApiToken}` and `next: { revalidate: 60 }`, then passes data to `DashboardClient`; shows error state with retry button if fetch fails in `frontend/src/app/(student)/dashboard/page.tsx`

**Checkpoint**: Registration → `/dashboard` → 8 Beginner (red) module cards at 0%, encouraging empty-state message, no hydration errors.

---

## Phase 4: User Story 2 — Returning Student Signs In and Views Progress (Priority: P1)

**Goal**: Login flow + fully populated dashboard with real mastery data per module, streak count, overall mastery, weak areas, and recommendations.

**Independent Test**: Login with seeded student account (has progress data) → `/dashboard` shows correct mastery % and colour per module, streak count, overall mastery %, weak area tags, and at least one recommendation.

- [X] T024 [US2] Create `LoginForm` with react-hook-form + zod (email, password), calls `authClient.signIn.email()`, handles `?next=` redirect, shows inline 401 error ("Invalid email or password") and 429 rate-limit message without clearing form in `frontend/src/components/auth/login-form.tsx`
- [X] T025 [US2] Create login page rendering `LoginForm` and handling `?next=` redirect param (reads `searchParams`, redirects to `next` or `/dashboard` on success) in `frontend/src/app/(auth)/login/page.tsx`
- [X] T026 [US2] Create `StreakBadge` widget with flame icon, `aria-label="Current learning streak: N days"`, current streak count; shows "Start your streak!" empty state when `streak` is `null` in `frontend/src/components/dashboard/streak-badge.tsx`
- [X] T027 [P] [US2] Create `MasteryOverview` widget displaying overall mastery percentage and a bar chart loaded via `next/dynamic(() => import('recharts/...'), { ssr: false })` to keep initial JS bundle < 200KB in `frontend/src/components/dashboard/mastery-overview.tsx`
- [X] T028 [P] [US2] Create `WeakAreasPanel` rendering `weak_areas[]` as tag badges; shows "No weak areas yet! Keep it up." empty state when array is empty in `frontend/src/components/dashboard/weak-areas-panel.tsx`
- [X] T029 [P] [US2] Create `RecommendationsPanel` rendering `recommendations[]` as numbered list; shows "Complete some exercises to get personalised recommendations." empty state in `frontend/src/components/dashboard/recommendations-panel.tsx`
- [X] T030 [US2] Create `DashboardClient` client component assembling `ModuleGrid`, `StreakBadge`, `MasteryOverview`, `WeakAreasPanel`, and `RecommendationsPanel`; uses `useQuery` (React Query) for client-side refetch seeded with SSR `initialData`; shows error state with "Retry" button; handles session-expired 401 by redirecting to `/login?reason=session_expired` in `frontend/src/components/dashboard/dashboard-client.tsx`
- [X] T031 [P] [US2] Create `useProgress` React Query hook fetching `GET /api/v1/agents/progress/summary` with `fastApiToken` from session, returning `ProgressSummary` in `frontend/src/hooks/use-progress.ts`
- [X] T032 [P] [US2] Create `useProfile` React Query hook fetching `GET /api/profile` with `fastApiToken` from session, returning `ProfileResponse` in `frontend/src/hooks/use-profile.ts`

**Checkpoint**: Login → `/dashboard` → all 8 module cards show correct mastery colours, streak badge visible, overall mastery percentage, weak areas tagged, recommendations listed. Backend-down shows retry button with layout intact.

---

## Phase 5: User Story 3 — Student Navigates Between Platform Sections (Priority: P2)

**Goal**: Persistent sidebar with active-state highlighting, keyboard accessibility, hamburger drawer on mobile, and navigable stub pages for Chat, Progress, and Quiz.

**Independent Test**: Click each sidebar link → correct route, full layout, active item highlighted; on < 768px hamburger toggles drawer; "Start Lesson" on module card navigates to `/chat`; "Take Quiz" navigates to `/quiz/{id}`.

- [X] T033 [US3] Enhance `StudentSidebar` with active-state via `usePathname()` (highlighted item with distinct background/text), visible keyboard focus rings (WCAG 2.1 AA), and hamburger drawer for < 768px using shadcn/ui Sheet component in `frontend/src/components/layout/student-sidebar.tsx`
- [X] T034 [US3] Enhance `TopNav` with theme toggle button (`useTheme()` with `useEffect` mounted guard to prevent hydration mismatch), mobile hamburger trigger wired to sidebar drawer state, and sign-out option in `frontend/src/components/layout/top-nav.tsx`
- [X] T035 [P] [US3] Create chat stub page with full student layout, chat bubble icon, and "AI Tutor Chat — Coming soon" centered placeholder in `frontend/src/app/(student)/chat/page.tsx`
- [X] T036 [P] [US3] Create progress stub page with full student layout, chart icon, and "Progress Tracking — Coming soon" centered placeholder in `frontend/src/app/(student)/progress/page.tsx`
- [X] T037 [P] [US3] Create quiz stub page with async params (`const { lessonId } = await props.params`), full student layout, and "Quiz for [lessonId] — Coming soon" centered placeholder in `frontend/src/app/(student)/quiz/[lessonId]/page.tsx`

**Checkpoint**: All 4 sidebar links reachable in one click from any student page; active link highlighted; sidebar collapses to hamburger on mobile; stub pages render with full layout.

---

## Phase 6: User Story 4 — Student Resets a Forgotten Password (Priority: P2)

**Goal**: Forgot-password and reset-password flows working against FastAPI; no email enumeration; invalid-token error handled.

**Independent Test**: Request reset for seeded account → success message shown regardless of email existence; follow link to `/reset-password?token=...` → set new password → login with new password succeeds; expired token → error shown without form.

- [X] T038 [US4] Create `ForgotPasswordForm` calling `POST /api/auth/password-reset/request` via `api.ts`, always showing success message ("If that email exists, a reset link has been sent.") regardless of outcome (no email enumeration) in `frontend/src/components/auth/forgot-password-form.tsx`
- [X] T039 [US4] Create forgot-password page rendering `ForgotPasswordForm` in `frontend/src/app/(auth)/forgot-password/page.tsx`
- [X] T040 [US4] Create `ResetPasswordForm` reading `token` from `await props.searchParams`, showing invalid-token error immediately if token missing/malformed, calling `POST /api/auth/password-reset/confirm`, redirecting to `/login` on success (200), and showing inline error on 400 (expired/invalid token) with link to request new one in `frontend/src/components/auth/reset-password-form.tsx`
- [X] T041 [US4] Create reset-password page with `async searchParams` prop passing token to `ResetPasswordForm` in `frontend/src/app/(auth)/reset-password/page.tsx`

**Checkpoint**: Forgot-password form always shows success; valid reset link → new password accepted → login works; invalid/missing token → error shown; no email enumeration on form submission.

---

## Phase 7: User Story 6 — Visitor Discovers Platform via Landing Page (Priority: P2)

**Goal**: Polished, conversion-focused public landing page at `/` with all sections, responsive, dark/light aware; authenticated students redirected to `/dashboard`.

**Independent Test**: Visit `/` logged out → hero, workflow, 8 curriculum modules, features, stats, CTA sections all visible; "Get Started" links go to `/register`; "Sign In" links go to `/login`; mobile (< 768px) no horizontal overflow; visit `/` logged in → redirect to `/dashboard`.

- [X] T042 [US6] Create root `page.tsx` as server component that checks session (`auth.api.getSession()`) and redirects authenticated users to `/dashboard`; renders `LandingNavbar` + all marketing sections + `LandingFooter` for unauthenticated visitors in `frontend/src/app/page.tsx`
- [X] T043 [US6] Create `LandingNavbar` — sticky with frosted-glass backdrop (`backdrop-blur`), logo, "Sign In" (→ `/login`) and "Get Started" (→ `/register`) links, theme-aware in `frontend/src/app/(marketing)/_components/landing-navbar.tsx`
- [X] T044 [US6] Create `HeroSection` — full-viewport Fraunces serif headline ("Learn Python with an AI tutor that never sleeps"), sub-headline, "Get Started Free" and "Sign In" CTAs, static mock terminal (`<pre>` with JetBrains Mono + syntax-coloured spans, no Monaco/Prism), scroll-triggered fade-in via CSS `@keyframes` in `frontend/src/app/(marketing)/_components/hero-section.tsx`
- [X] T045 [P] [US6] Create `HowItWorksSection` — 5-step flow (Ask → AI explains → Write code → Sandbox runs → Mastery updates) horizontal on desktop, single-column on mobile, CSS scroll-triggered animation in `frontend/src/app/(marketing)/_components/how-it-works-section.tsx`
- [X] T046 [P] [US6] Create `CurriculumSection` — grid of all 8 module cards reusing `ModuleCard` visual style with static props (topic icon, sub-topic bullets, no API call), 2-column on mobile in `frontend/src/app/(marketing)/_components/curriculum-section.tsx`
- [X] T047 [P] [US6] Create `FeaturesSection` — 4-card bento grid (AI Tutor, Code Sandbox, Progress Tracking, Teacher Alerts) with icons; 1-column on mobile in `frontend/src/app/(marketing)/_components/features-section.tsx`
- [X] T048 [P] [US6] Create `StatsSection` — static stat row: "8 Modules · 40+ Lessons · Real-time AI Feedback" in `frontend/src/app/(marketing)/_components/stats-section.tsx`
- [X] T049 [P] [US6] Create `CtaSection` — full-width amber banner "Start learning Python today — it's free." with single "Create Account" (→ `/register`) button; dark foreground on amber (≥ 4.5:1 WCAG contrast) in `frontend/src/app/(marketing)/_components/cta-section.tsx`
- [X] T050 [P] [US6] Create `LandingFooter` — logo, brief tagline, links to `/login` and `/register` in `frontend/src/app/(marketing)/_components/landing-footer.tsx`
- [X] T051 [US6] Verify all landing page sections reflow correctly on < 768px (hero stacks vertically, steps go single-column, module grid goes 2-column, bento goes 1-column) — adjust responsive classes as needed across all marketing components

**Checkpoint**: `/` while logged out → full landing page with all 8 sections; all CTAs correct; mobile layout intact; authenticated → immediate redirect to `/dashboard`.

---

## Phase 8: User Story 5 — Interface Respects Light/Dark Mode Preference (Priority: P3)

**Goal**: OS preference applied on first load with no FOUC; manual toggle persists via HTTP cookie across refreshes and sessions.

**Independent Test**: Load with OS dark → dark theme active, no flash; toggle to light → light theme immediate; refresh → light preserved (cookie); new session → light preserved.

- [X] T052 [US5] Add cookie-write sync to `ThemeProvider` so every `next-themes` theme change writes to an HTTP cookie (`theme=dark|light`), and confirm the FOUC-prevention script in `layout.tsx` reads that cookie before applying the class; verify `suppressHydrationWarning` on `<html>` prevents React mismatch in `frontend/src/components/providers/theme-provider.tsx`

**Checkpoint**: OS dark → dark on first paint, no flash; toggle → cookie written; hard refresh → correct theme class applied before first paint.

---

## Phase 9: User Story 7 — Teacher Sees "Coming Soon" After Login (Priority: P3)

**Goal**: Teacher role redirected to `/teacher/coming-soon` instead of student dashboard; direct dashboard access blocked.

**Independent Test**: Login with seeded teacher account → `/teacher/coming-soon` shown (not `/dashboard`); direct `/dashboard` access → redirected back to `/teacher/coming-soon`; "Sign out" → `/login`.

- [X] T053 [US7] Create teacher coming-soon page with friendly placeholder, teacher role acknowledgement, and sign-out button calling `authClient.signOut()` + redirect to `/login` in `frontend/src/app/(teacher)/teacher/coming-soon/page.tsx`
- [X] T054 [US7] Confirm student layout role guard in `(student)/layout.tsx` redirects teachers to `/teacher/coming-soon` (already wired in T022 — validate and add a direct-navigation guard if needed) in `frontend/src/app/(student)/layout.tsx`

**Checkpoint**: Teacher login → `/teacher/coming-soon`; teacher visits `/dashboard` → redirected to `/teacher/coming-soon`; sign-out clears session.

---

## Phase 10: Tests — Vitest (Unit) + Playwright (E2E)

**Purpose**: Verify correctness of auth forms, mastery logic, and all 6 critical E2E journeys.

### Test Setup

- [X] T055 Configure Vitest with `@testing-library/react` and `jsdom` environment in `frontend/vitest.config.ts`, `frontend/src/setupTests.ts`
- [X] T056 Configure Playwright with `baseURL: http://localhost:3000`, Chromium browser, and screenshot on failure in `frontend/playwright.config.ts`

### Unit / Component Tests (Vitest)

- [X] T057 [P] Write `LoginForm` tests: renders form fields, submits with valid data, shows inline error on 401, shows rate-limit message on 429 in `frontend/src/components/auth/__tests__/login-form.test.tsx`
- [X] T058 [P] Write `RegisterForm` tests: validates all fields (required, email format, password complexity), handles duplicate-email 400 error inline, submits successfully with valid data in `frontend/src/components/auth/__tests__/register-form.test.tsx`
- [X] T059 [P] Write `ModuleCard` tests: renders correct colour class for each of the 4 mastery levels, "Start Lesson" links to `/chat`, "Take Quiz" links to `/quiz/{id}` in `frontend/src/components/dashboard/__tests__/module-card.test.tsx`
- [X] T060 [P] Write `utils.ts` tests: `masteryLevel()` boundary values (0, 40, 41, 70, 71, 90, 91, 100) and `masteryColor()` for all 4 levels in `frontend/src/lib/__tests__/utils.test.ts`
- [X] T061 [P] Write `HeroSection` tests: "Get Started" link points to `/register`, "Sign In" link points to `/login` in `frontend/src/app/(marketing)/__tests__/hero-section.test.tsx`

### E2E Tests (Playwright — 6 Critical Journeys)

- [X] T062 [P] Write registration E2E: register with valid credentials → land on `/dashboard` → 8 module cards visible in `frontend/e2e/registration.spec.ts`
- [X] T063 [P] Write login E2E: login with seeded student account → `/dashboard` renders with user's display name in `frontend/e2e/login.spec.ts`
- [X] T064 [P] Write password-reset E2E: forgot-password form → success message shown; invalid token → error shown in `frontend/e2e/password-reset.spec.ts`
- [X] T065 [P] Write theme-toggle E2E: load with OS dark → dark theme active; toggle → light; refresh → light preserved (cookie set) in `frontend/e2e/theme-toggle.spec.ts`
- [X] T066 [P] Write route-protection E2E: visit `/dashboard` unauthenticated → redirected to `/login?next=/dashboard` in `frontend/e2e/route-protection.spec.ts`
- [X] T067 [P] Write landing-page E2E: visit `/` logged out → all 8 module cards + "Get Started" CTA visible; visit `/` logged in → redirected to `/dashboard` in `frontend/e2e/landing-page.spec.ts`

**Checkpoint**: `npx vitest run` → all 5 unit test suites pass; `npx playwright test` → all 6 E2E journeys pass.

---

## Phase 11: Polish & Cross-Cutting Concerns

- [X] T068 Run all quickstart.md §6 verification checks (`npm run dev`, register, dashboard empty state, theme toggle, route protection) and fix any failures
- [X] T069 [P] Verify WCAG 2.1 AA compliance: run axe-core assertions in Playwright E2E for auth pages and dashboard (all colour pairs ≥ 4.5:1 text contrast, ≥ 3:1 UI component contrast) in `frontend/e2e/accessibility.spec.ts`
- [X] T070 [P] Verify initial JS bundle < 200KB gzipped via `next build` output; confirm recharts and Monaco (if added) are excluded from initial bundle via `next/dynamic`

**Checkpoint**: All quickstart checks green; axe-core: zero WCAG AA violations; initial bundle ≤ 200KB gzipped.

---

## Dependencies & Execution Order

### Phase Dependencies

```
Phase 1 (Setup)       ──────────────────────────────────────────────────────► No deps
Phase 2 (Foundational)  Depends on Phase 1 ──────────────────────────────► BLOCKS all stories
Phase 3 (US1 — P1)     Depends on Phase 2 ─────────────────────────────────► MVP!
Phase 4 (US2 — P1)     Depends on Phase 2, integrates Phase 3 components ──►
Phase 5 (US3 — P2)     Depends on Phase 4 (sidebar enhancement) ────────────►
Phase 6 (US4 — P2)     Depends on Phase 2 ──────────────────────────────────► Can parallel US3
Phase 7 (US6 — P2)     Depends on Phase 3 (ModuleCard reuse) ───────────────► Can parallel US4
Phase 8 (US5 — P3)     Depends on Phase 5 (TopNav has toggle) ──────────────►
Phase 9 (US7 — P3)     Depends on Phase 4 (student layout role guard) ──────►
Phase 10 (Tests)        Depends on Phases 3–9 ───────────────────────────────►
Phase 11 (Polish)       Depends on Phase 10 ────────────────────────────────►
```

### User Story Dependencies

| Story | Priority | Depends On | Can Parallel With |
|-------|----------|-----------|-------------------|
| US1 — Register + Dashboard | P1 | Phase 2 (Foundational) | — |
| US2 — Login + Progress | P1 | Phase 2 + US1 components | US4, US6 after Phase 2 |
| US3 — Navigation | P2 | US2 (enhances sidebar/nav) | US4, US6 |
| US4 — Password Reset | P2 | Phase 2 | US3, US6 |
| US6 — Landing Page | P2 | US1 (ModuleCard reuse) | US3, US4 |
| US5 — Theme Persistence | P3 | US3 (TopNav toggle) | US7 |
| US7 — Teacher Coming Soon | P3 | US2 (student layout role guard) | US5 |

### Within Each User Story

- Types / utilities before components
- Components before pages
- Pages before E2E tests
- Each story shippable independently after its checkpoint

### Parallel Opportunities

- T003, T004 — run in parallel after T001
- T007, T008, T011 — run in parallel after T006 (db migration)
- T016, T019 — run in parallel within US1
- T027, T028, T029, T031, T032 — run in parallel within US2
- T035, T036, T037 — run in parallel within US3
- T045, T046, T047, T048, T049, T050 — run in parallel within US6
- T057, T058, T059, T060, T061 — run in parallel (Vitest)
- T062, T063, T064, T065, T066, T067 — run in parallel (Playwright)
- T069, T070 — run in parallel in Polish phase

---

## Parallel Example: User Story 2

```bash
# After T024 (LoginForm) and T025 (Login page) complete, run in parallel:
Agent A: T026 — StreakBadge widget
Agent B: T027 — MasteryOverview widget (recharts with next/dynamic)
Agent C: T028 — WeakAreasPanel widget
Agent D: T029 — RecommendationsPanel widget
Agent E: T031 — useProgress hook
Agent F: T032 — useProfile hook

# Then sequentially:
T030 — DashboardClient assembles all widgets (depends on T026–T029)
```

---

## Implementation Strategy

### MVP First (User Stories 1 + 2 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL — blocks everything)
3. Complete Phase 3: US1 — Register + Dashboard empty state (**STOP → validate**)
4. Complete Phase 4: US2 — Login + Dashboard with real data (**STOP → validate**)
5. Deploy/demo to stakeholders

**MVP delivers**: Full auth flow (register, login) + data-driven Student Dashboard for the daily student use case.

### Incremental Delivery

| Phase | Delivers | Independent Test |
|-------|----------|-----------------|
| Setup + Foundational | Auth infrastructure | Better Auth session resolves |
| US1 | Register → Dashboard (empty state) | 8 module cards at 0% Beginner |
| US2 | Login → Dashboard (live data) | Module mastery, streak, weak areas |
| US3 | Full navigation + stubs | Sidebar active states; all 4 routes |
| US4 | Password reset self-service | Reset email → new password → login |
| US6 | Public landing page | All sections; CTAs; mobile layout |
| US5 | Theme persistence | No FOUC; cookie persists after refresh |
| US7 | Teacher placeholder | Teacher sees coming-soon, not dashboard |

---

## Summary

| Phase | Tasks | Story |
|-------|-------|-------|
| Phase 1: Setup | T001–T005 (5) | — |
| Phase 2: Foundational | T006–T012 (7) | — |
| Phase 3: US1 Register + Dashboard | T013–T023 (11) | US1 (P1) |
| Phase 4: US2 Login + Progress | T024–T032 (9) | US2 (P1) |
| Phase 5: US3 Navigation | T033–T037 (5) | US3 (P2) |
| Phase 6: US4 Password Reset | T038–T041 (4) | US4 (P2) |
| Phase 7: US6 Landing Page | T042–T051 (10) | US6 (P2) |
| Phase 8: US5 Theme Persistence | T052 (1) | US5 (P3) |
| Phase 9: US7 Teacher Coming Soon | T053–T054 (2) | US7 (P3) |
| Phase 10: Tests | T055–T067 (13) | All |
| Phase 11: Polish | T068–T070 (3) | Cross-cutting |
| **TOTAL** | **70 tasks** | |

**Parallel opportunities**: 24 tasks marked `[P]` across all phases.

**Suggested MVP scope**: Complete through Phase 4 (US1 + US2) = 38 tasks delivering full auth + data-driven Student Dashboard.
