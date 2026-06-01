# Implementation Plan: Frontend Foundation & Student Dashboard

**Branch**: `013-frontend-foundation` | **Date**: 2026-05-09 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/013-frontend-foundation/spec.md`

---

## Summary

Scaffold the LearnPyByAI Next.js 16 frontend from zero: project setup, design system (shadcn/ui + Tailwind + custom Fraunces/Outfit/JetBrains Mono typography), Better Auth session management proxied to the existing FastAPI backend, auth pages (login, register, forgot/reset password), student layout with sidebar, a fully data-driven Student Dashboard, and stub pages for chat/progress/quiz. The teacher role gets a "coming soon" placeholder. System-default dark/light mode with no flash. All dashboard data fetched server-side via React Server Components. Theme persisted in HTTP cookie. Fully responsive down to 768 px (hamburger drawer). Skeleton screens via React Suspense. WCAG 2.1 AA accessibility.

---

## Technical Context

**Language/Version**: TypeScript 5+ / React 19
**Framework**: Next.js 16 (App Router, Turbopack default)
**UI**: shadcn/ui (New York style) + Tailwind CSS 4 + next-themes
**Auth**: Better Auth 1.x (pg.Pool → Neon, credential proxy to FastAPI)
**State**: @tanstack/react-query 5 (client) + Server Components (initial load)
**Storage**: Neon PostgreSQL — shared DB; Better Auth adds 4 new tables
**Testing**: Vitest + @testing-library/react (components), Playwright (E2E)
**Target Platform**: Web browser, SSR + CSR
**Performance Goals**: SSR page load < 800ms p95; initial JS bundle < 200KB gzipped
**Constraints**: No FOUC on theme load; params/cookies/headers all async (Next.js 16); FastAPI JWT must reach backend API calls via Better Auth session; WCAG 2.1 AA compliance; mobile-responsive ≥ 768px
**Scale/Scope**: ~15 files of source code, 1 complete page (dashboard), 3 stubs, 4 auth pages

---

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-checked after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| Use BetterAuth | ✅ PASS | Better Auth 1.x with pg.Pool and custom `password.verify` proxy |
| TypeScript + Next.js | ✅ PASS | Next.js 16, TypeScript 5+ strict mode |
| Prettier + ESLint on save | ✅ PASS | `.prettierrc` + `eslint-config-next` configured in setup task |
| React components: PascalCase | ✅ PASS | Enforced in all component files |
| Custom hooks: `use` prefix | ✅ PASS | `useProgress`, `useProfile` |
| Bundle < 200KB gzipped | ✅ PASS | `next/dynamic` for recharts on dashboard; Monaco deferred to F14 |
| Short-lived JWTs | ✅ PASS | FastAPI JWT (15 min) stored in Better Auth session; refresh on 401 |
| Secrets in `.env.local` | ✅ PASS | `BETTER_AUTH_SECRET`, `DATABASE_URL` never in source |
| Test coverage: React 65% | ⚠️ TARGET | Auth forms + dashboard components will have unit tests |
| E2E: 5 critical journeys | ✅ PLAN | Registration, login, dashboard load, password reset, theme toggle |
| No business logic in route handlers | ✅ PASS | Mastery color/label logic in `lib/utils.ts`, not in pages |
| WCAG 2.1 AA | ✅ PASS | Enforced via color tokens (contrast ≥ 4.5:1) and ARIA labels on interactive elements |

---

## Project Structure

### Documentation (this feature)

```
specs/013-frontend-foundation/
├── plan.md              ← This file
├── research.md          ← Phase 0 findings
├── data-model.md        ← TypeScript types + Better Auth DB schema
├── quickstart.md        ← Developer setup guide
├── contracts/
│   └── frontend-backend.md   ← API contracts (frontend → FastAPI)
└── checklists/
    └── requirements.md
```

### Source Code

```
frontend/
├── .env.local
├── .env.local.example
├── next.config.ts
├── tailwind.config.ts
├── components.json
├── tsconfig.json
├── .prettierrc
├── .eslintrc.json
├── middleware.ts
└── src/
    ├── app/
    │   ├── globals.css
    │   ├── layout.tsx
    │   ├── page.tsx                          ← Landing page (unauthenticated) or redirect
    │   ├── (marketing)/
    │   │   └── _components/
    │   │       ├── landing-navbar.tsx
    │   │       ├── hero-section.tsx
    │   │       ├── how-it-works-section.tsx
    │   │       ├── curriculum-section.tsx
    │   │       ├── features-section.tsx
    │   │       ├── stats-section.tsx
    │   │       ├── cta-section.tsx
    │   │       └── landing-footer.tsx
    │   ├── (auth)/
    │   │   ├── layout.tsx
    │   │   ├── login/page.tsx
    │   │   ├── register/page.tsx
    │   │   ├── forgot-password/page.tsx
    │   │   └── reset-password/page.tsx
    │   ├── (student)/
    │   │   ├── layout.tsx
    │   │   ├── dashboard/page.tsx
    │   │   ├── chat/page.tsx
    │   │   ├── progress/page.tsx
    │   │   └── quiz/[lessonId]/page.tsx
    │   ├── (teacher)/
    │   │   └── teacher/coming-soon/page.tsx
    │   └── api/
    │       ├── auth/[...all]/route.ts
    │       └── register-proxy/route.ts
    ├── components/
    │   ├── providers/query-provider.tsx
    │   ├── providers/theme-provider.tsx
    │   ├── layout/student-sidebar.tsx
    │   ├── layout/top-nav.tsx
    │   ├── ui/                          ← shadcn/ui (generated)
    │   ├── auth/login-form.tsx
    │   ├── auth/register-form.tsx
    │   ├── auth/forgot-password-form.tsx
    │   ├── auth/reset-password-form.tsx
    │   └── dashboard/
    │       ├── module-card.tsx
    │       ├── module-grid.tsx
    │       ├── streak-badge.tsx
    │       ├── mastery-overview.tsx
    │       ├── weak-areas-panel.tsx
    │       ├── recommendations-panel.tsx
    │       └── dashboard-skeleton.tsx
    ├── lib/auth.ts
    ├── lib/auth-client.ts
    ├── lib/api.ts
    ├── lib/utils.ts
    ├── hooks/use-progress.ts
    ├── hooks/use-profile.ts
    └── types/index.ts
```

Also (backend — Alembic migration):
```
backend/alembic/versions/20260509_create_better_auth_tables.py
```

---

## Implementation Phases

### Phase 1 — Project Scaffold & Design System (Tasks T131–T135)

**Goal**: A running Next.js 16 app with the full design system in place — fonts, colours, dark/light mode — before any auth or pages.

**T131 — Init Next.js 16 + install all dependencies**
- `npm install next@latest react@19 react-dom@19 typescript`
- Install all packages from quickstart.md §1
- Create `next.config.ts` with backend proxy rewrites for `/api/v1` and `/api/auth` passthrough

```typescript
// next.config.ts
import type { NextConfig } from 'next'
const config: NextConfig = {
  // Turbopack is default in Next.js 16 — no flag needed
  experimental: {
    optimizePackageImports: ['lucide-react', 'recharts'],
  },
  async rewrites() {
    return [
      {
        source: '/api/v1/:path*',
        destination: `${process.env.NEXT_PUBLIC_BACKEND_URL}/api/v1/:path*`,
      },
    ]
  },
}
export default config
```

**T132 — Configure Tailwind CSS 4 + shadcn/ui**
- `tailwind.config.ts` with `darkMode: ['class']`, CSS variable color tokens, font family variables
- `globals.css` with `:root` and `.dark` HSL color tokens (Warm Code Scholar palette from research.md)
- Run `npx shadcn@latest init` and install all required components
- `components.json` pointing to `src/` directory with `@/` aliases

**T133 — Set up Google Fonts + Typography**
- Load `Fraunces` (variable, opsz), `Outfit`, `JetBrains Mono` via `next/font/google`
- Expose as CSS variables `--font-heading`, `--font-sans`, `--font-mono`
- Apply variables to `<html>` element in root layout
- Tailwind `fontFamily` config references the CSS variables

**T134 — Root layout + Theme System (no FOUC)**
- `app/layout.tsx`: fonts, FOUC-prevention inline script in `<head>`, `suppressHydrationWarning`, `ThemeProvider`
- Theme preference stored in HTTP cookie (`theme`) — read server-side by middleware before first render
- `components/providers/theme-provider.tsx`: wraps `next-themes` ThemeProvider with `storageKey="theme"` and cookie sync
- `components/providers/query-provider.tsx`: wraps TanStack Query client
- Theme toggle button component using `useTheme()` with `useEffect` mounted guard

```tsx
// app/layout.tsx — The inline script must be in <head> BEFORE body
<html lang="en" suppressHydrationWarning>
  <head>
    <script dangerouslySetInnerHTML={{ __html: `
      try {
        const theme = document.cookie.match(/theme=([^;]+)/)?.[1]
          || (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light')
        if (theme === 'dark') document.documentElement.classList.add('dark')
      } catch {}
    `}} />
  </head>
  <body>
    <ThemeProvider attribute="class" defaultTheme="system" enableSystem storageKey="theme">
      {children}
    </ThemeProvider>
  </body>
</html>
```

**T135 — Tooling: Prettier + ESLint + tsconfig**
- `tsconfig.json` with strict mode, `@/` path alias
- `.prettierrc` with `semi: false, singleQuote: true, tabWidth: 2`
- `.eslintrc.json` extending `eslint-config-next` + no-console rule
- `.env.local.example` with all required variable names

---

### Phase 2 — Better Auth + DB Migration (Tasks T136–T138)

**Goal**: Working session management — sign in creates a Better Auth session cookie containing the FastAPI JWT; middleware protects routes.

**T136 — Alembic migration: Better Auth tables**
Add `backend/alembic/versions/20260509_create_better_auth_tables.py`:
```python
# Creates: user, session, account, verification tables
# These are Better Auth's session-layer tables.
# They do NOT replace the FastAPI 'users' table.
# user.fast_api_id references users.id for cross-system sync.
```
Run `alembic upgrade head` to apply.

**T137 — Better Auth server (`lib/auth.ts`)**
```typescript
import { betterAuth } from "better-auth"
import { Pool } from "pg"

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL!

export const auth = betterAuth({
  secret: process.env.BETTER_AUTH_SECRET!,
  baseURL: process.env.BETTER_AUTH_BASE_URL || "http://localhost:3000",
  database: new Pool({ connectionString: process.env.DATABASE_URL }),
  emailAndPassword: {
    enabled: true,
    disableSignUp: true,   // Sign-up handled by register-proxy route
    sendResetPassword: async ({ user, url }) => {
      // POST to FastAPI /api/auth/password-reset/request
    },
    password: {
      hash: async (p) => p,
      verify: async ({ hash, password, ...ctx }) => {
        const res = await fetch(`${BACKEND_URL}/api/auth/login`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ email: (ctx as any).email, password }),
        })
        if (!res.ok) return false
        const data = await res.json()
        ;(ctx as any).fastApiToken = data.tokens.access_token
        ;(ctx as any).role = data.user.role
        return true
      },
    },
  },
  user: {
    additionalFields: {
      role: { type: "string", defaultValue: "student", input: true },
      fastApiId: { type: "string", input: true },
    },
  },
  session: {
    expiresIn: 7 * 24 * 60 * 60,
    additionalFields: {
      fastApiToken: { type: "string", input: true },
    },
  },
})
```

**T138 — Route handler + registration proxy + auth client**
- `app/api/auth/[...all]/route.ts`: `toNextJsHandler(auth)` (Better Auth handler)
- `app/api/register-proxy/route.ts`: calls FastAPI register → on success calls `auth.api.signUpEmail()` → returns session
- `lib/auth-client.ts`: `createAuthClient({ baseURL: NEXT_PUBLIC_APP_URL })` — exports `signIn`, `signOut`, `useSession`

---

### Phase 3 — Middleware + Auth Pages (Tasks T139–T142)

**Goal**: All auth pages functional with real backend calls; route protection working.

**T139 — Middleware (route protection)**
```typescript
// middleware.ts
import { getSessionCookie } from "better-auth/cookies"
import { NextRequest, NextResponse } from "next/server"

const PUBLIC_PATHS = ["/login", "/register", "/forgot-password", "/reset-password"]

export async function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl
  const session = getSessionCookie(request)   // Fast cookie-only check

  if (!session && !PUBLIC_PATHS.some(p => pathname.startsWith(p))) {
    const url = new URL("/login", request.url)
    url.searchParams.set("next", pathname)
    return NextResponse.redirect(url)
  }

  if (session && PUBLIC_PATHS.some(p => pathname === p)) {
    return NextResponse.redirect(new URL("/dashboard", request.url))
  }

  return NextResponse.next()
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico|api/auth).*)"],
}
```

Note: Role-based routing (student → `/dashboard`, teacher → `/teacher/coming-soon`) is handled in the `(student)/layout.tsx` and `(teacher)/layout.tsx` server components using `auth.api.getSession()` — this avoids a DB hit on every request while still providing role guard at the layout boundary.

**T140 — Auth layout + Login page**
- `(auth)/layout.tsx`: centred card layout, logo, no sidebar, light/dark aware, WCAG 2.1 AA contrast
- `components/auth/login-form.tsx`: react-hook-form + zod validation, calls `authClient.signIn.email()`, handles 401 / rate-limit errors inline
- `app/(auth)/login/page.tsx`: renders `LoginForm`, handles `?next=` redirect param

**T141 — Register page**
- `components/auth/register-form.tsx`: name, email, password, zod validation, calls `POST /api/register-proxy`
- `app/(auth)/register/page.tsx`: renders form, redirects to `/dashboard` on success

**T142 — Forgot password + Reset password pages**
- `forgot-password-form.tsx`: calls FastAPI `POST /api/auth/password-reset/request` (via api.ts); always shows success message (no enumeration)
- `reset-password-form.tsx`: reads `?token=` from URL (`await props.searchParams`), calls FastAPI `POST /api/auth/password-reset/confirm`; redirects to `/login` on success; shows invalid-token error if 400

---

### Phase 4 — Student Layout + Dashboard (Tasks T143–T147)

**Goal**: The complete, data-driven Student Dashboard — all 8 module cards, mastery colours, streak, weak areas, recommendations — working against live backend.

**T143 — Student layout (sidebar + top nav)**
- `(student)/layout.tsx`: server component — calls `auth.api.getSession()`, redirects teachers to `/teacher/coming-soon`; renders `StudentSidebar` + `TopNav` + children
- `components/layout/student-sidebar.tsx`: navigation links (Dashboard, Chat, Progress, Quiz), active state from `usePathname()`, user avatar + display name, sign-out button; collapses to hamburger drawer on < 768 px; all links keyboard-navigable with visible focus ring (WCAG 2.1 AA)
- `components/layout/top-nav.tsx`: logo, page title, theme toggle, mobile menu trigger

**T144 — Dashboard page (server component + Suspense)**
```typescript
// app/(student)/dashboard/page.tsx
import { auth } from "@/lib/auth"
import { headers } from "next/headers"
import { Suspense } from "react"
import { DashboardSkeleton } from "@/components/dashboard/dashboard-skeleton"

export default async function DashboardPage() {
  const session = await auth.api.getSession({ headers: await headers() })
  return (
    <Suspense fallback={<DashboardSkeleton />}>
      <DashboardContent session={session} />
    </Suspense>
  )
}

async function DashboardContent({ session }) {
  const progress = await fetch(
    `${process.env.NEXT_PUBLIC_BACKEND_URL}/api/v1/agents/progress/summary`,
    {
      headers: { Authorization: `Bearer ${session?.session.fastApiToken}` },
      next: { revalidate: 60 },
    }
  ).then(r => r.ok ? r.json() : null)

  return <DashboardClient user={session!.user} initialProgress={progress} />
}
```

**T145 — Module cards + mastery grid**
- `components/dashboard/module-card.tsx`: displays module name, mastery badge, coloured progress bar, "Start Lesson" + "Take Quiz" buttons; colour contrast meets WCAG 2.1 AA (4.5:1 for text, 3:1 for UI components)
- `components/dashboard/module-grid.tsx`: merges `CURRICULUM_MODULES` static list with API `topics[]` — fills missing modules at 0% (empty state); single-column reflow on < 768 px
- Mastery colour logic in `lib/utils.ts`:
```typescript
export function masteryColor(level: MasteryLevel): string {
  return { Beginner: "red", Learning: "amber", Proficient: "green", Mastered: "blue" }[level]
}
export function masteryLevel(score: number): MasteryLevel {
  if (score <= 40) return "Beginner"
  if (score <= 70) return "Learning"
  if (score <= 90) return "Proficient"
  return "Mastered"
}
```

**T146 — Dashboard widgets (streak, overview, weak areas, recommendations)**
- `streak-badge.tsx`: flame icon + current streak count; shows "Start your streak!" if null; `aria-label` set for screen readers
- `mastery-overview.tsx`: overall mastery percentage + circular/bar chart (recharts — loaded with `next/dynamic` to keep bundle < 200KB)
- `weak-areas-panel.tsx`: list of weak area tags; "No weak areas yet!" empty state
- `recommendations-panel.tsx`: numbered recommendation list
- `dashboard-skeleton.tsx`: Suspense skeleton placeholder matching layout of real content — each section (module cards, streak, recommendations) has its own `<Suspense>` boundary for streaming

**T147 — Dashboard client component**
- `DashboardClient`: ties all widgets together, handles error state (retry button), handles loading state (`DashboardSkeleton`)
- Uses React Query's `useQuery` for client-side refetch after initial server render
- Staggered CSS animation on card reveal (`animation-delay: calc(var(--i) * 80ms)`)

---

### Phase 5 — Landing Page (Task T148)

**Goal**: A polished, conversion-focused public landing page at `/` that demonstrates the complete LearnPyByAI workflow to unauthenticated visitors and drives registrations.

**T148 — Landing page (`app/page.tsx` + components)**

The root `app/page.tsx` becomes a **public server component** that checks for an active session: authenticated students are immediately redirected to `/dashboard`; unauthenticated visitors receive the full marketing page.

**Page sections (in scroll order):**

1. **Navbar** — Logo, "Sign In" and "Get Started" links; sticky, frosted-glass backdrop, theme-aware.

2. **Hero** — Full-viewport headline using Fraunces serif ("Learn Python with an AI tutor that never sleeps"), sub-headline, two CTAs ("Get Started Free" → `/register`, "Sign In" → `/login`), and an animated code-snippet preview (mock terminal showing a student asking a question and the AI responding with highlighted Python).

3. **How It Works** — Horizontal step-flow (or vertical on mobile) with 5 illustrated steps:
   - Step 1: Ask the AI tutor a Python question
   - Step 2: AI explains with code examples
   - Step 3: Write and run code in the sandbox
   - Step 4: Take a quiz to test understanding
   - Step 5: Watch your mastery score rise

4. **Curriculum Modules** — Grid of all 8 module cards (Python Basics → Libraries & APIs) using the same `MasteryColor` design tokens as the dashboard, but showing topic icons and sub-topic bullets instead of real scores.

5. **Features** — 4-card bento grid:
   - 🤖 AI Tutor (conversational, context-aware)
   - 🐍 Live Code Sandbox (no install needed, stdlib only)
   - 📊 Progress Tracking (mastery levels, streak, weak areas)
   - 🔔 Teacher Alerts (struggle detection, exercise assignment)

6. **Social Proof / Stats** — Simple stat row: "8 Modules · 40+ Lessons · Real-time AI Feedback" (static copy, no real data needed).

7. **Final CTA** — Full-width amber call-to-action banner: "Start learning Python today — it's free." with a single "Create Account" button.

8. **Footer** — Logo, brief tagline, links to `/login` and `/register`. No heavy footer needed.

**Key implementation notes:**
- Entire page is a React Server Component — no `"use client"` at the page level.
- Scroll-triggered fade-in animations via CSS `@keyframes` + `animation-delay` (no JS animation library; keeps bundle lean).
- Mock AI chat snippet in hero uses a static `<pre>` block styled with `JetBrains Mono` and syntax-coloured spans — no Monaco/Prism dependency.
- Module cards in section 4 reuse the `ModuleCard` component visual style but accept static props (no API call).
- All colour tokens from `globals.css` — dark mode works automatically.
- WCAG 2.1 AA: hero text on amber background must use dark foreground (hsl 25 25% 10%) to achieve ≥ 4.5:1 contrast.
- Mobile (< 768 px): hero stacks vertically, steps go single-column, module grid goes 2-column, bento goes 1-column.

```
frontend/src/
├── app/
│   ├── page.tsx                    ← Root page (public landing or redirect)
│   └── (marketing)/               ← Route group for public pages
│       └── _components/
│           ├── landing-navbar.tsx
│           ├── hero-section.tsx
│           ├── how-it-works-section.tsx
│           ├── curriculum-section.tsx
│           ├── features-section.tsx
│           ├── stats-section.tsx
│           ├── cta-section.tsx
│           └── landing-footer.tsx
```

---

### Phase 6 — Stub Pages + Teacher Placeholder (Tasks T149–T150)

**T149 — Stub pages**
- `(student)/chat/page.tsx`: full layout, centered "AI Tutor Chat coming soon" with chat bubble icon
- `(student)/progress/page.tsx`: full layout, centered "Progress tracking coming soon" with chart icon
- `(student)/quiz/[lessonId]/page.tsx`: async params (`await props.params`), full layout, "Quiz for [module] coming soon"

**T150 — Teacher coming-soon page**
- `(teacher)/teacher/coming-soon/page.tsx`: teacher-aware layout, friendly placeholder, sign-out button

---

### Phase 7 — Tests (Tasks T151–T152)

**T151 — Unit/component tests (Vitest + Testing Library)**
- `login-form.test.tsx`: renders form, submits with valid data, shows error on 401
- `register-form.test.tsx`: validates all fields, handles duplicate email error
- `module-card.test.tsx`: renders correct colour class for each mastery level
- `utils.test.ts`: `masteryColor()` and `masteryLevel()` boundary tests (0, 40, 41, 70, 71, 90, 91, 100)
- `hero-section.test.tsx`: "Get Started" and "Sign In" links point to `/register` and `/login`

**T152 — E2E tests (Playwright — 6 critical journeys)**
1. `registration.spec.ts`: register → land on dashboard → 8 module cards visible
2. `login.spec.ts`: login → dashboard renders with user's display name
3. `password-reset.spec.ts`: forgot-password form → success message shown
4. `theme-toggle.spec.ts`: load with OS dark → dark theme active; toggle → light; refresh → light preserved (cookie)
5. `route-protection.spec.ts`: visit `/dashboard` unauthenticated → redirected to `/login?next=/dashboard`
6. `landing-page.spec.ts`: visit `/` logged out → all 8 module cards + "Get Started" CTA visible; visit `/` logged in → redirected to `/dashboard`

---

## Key Architectural Decisions

### ADR-1: Better Auth as Session Layer Over Dual User Tables
Using Better Auth for session management while FastAPI remains the credential authority avoids rebuilding auth logic. The cost is dual-record sync on registration (acceptable for MVP). Alternatives: single user table via field mapping (complex Drizzle setup) or custom cookie-only auth (violates constitution).

📋 Architectural decision detected: **Better Auth session layer with FastAPI credential proxy** — Document? Run `/sp.adr better-auth-session-proxy`

### ADR-2: Server Components + Suspense Streaming for Dashboard
The dashboard uses React Server Components for the initial data fetch with ISR (`revalidate: 60`) and per-section `<Suspense>` boundaries for streaming skeleton screens. React Query handles client-side refetch after mount. This hybrid pattern avoids FOUC and meets SC-002 (3 s full render).

📋 Architectural decision detected: **Server Component + Suspense streaming + React Query hybrid for dashboard** — Document? Run `/sp.adr dashboard-server-component-hybrid`

### ADR-3: Cookie-Based Theme Persistence (No FOUC on SSR)
Theme preference is written to an HTTP cookie on toggle so Next.js middleware can read and apply the correct theme class server-side before the first HTML byte is sent. `localStorage`-only approaches always flash the wrong theme on SSR hard refreshes.

📋 Architectural decision detected: **HTTP cookie for theme persistence (SSR FOUC prevention)** — Document? Run `/sp.adr theme-cookie-persistence`

### ADR-4: Role Guard in Layout Server Components, Not Middleware
Middleware uses `getSessionCookie` (cookie-only, no DB hit) for auth check. Role-based redirects happen in layout server components where `auth.api.getSession()` is called once per route tree, not per request. This trades some security at the middleware edge for significantly better performance.

---

## Risk Register

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| Better Auth `additionalFields` for `fastApiToken` not persisting to session row correctly | Medium | High | Test with a simple integration test before building dashboard; fallback to cookie-based token storage |
| Next.js 16 breaking change not yet covered in research (new async API) | Low | Medium | Run `npx @next/codemod@canary upgrade latest` on any Next.js 15→16 patterns; check runtime errors |
| FastAPI CORS blocks Next.js 3000 origin | Low | High | Backend `.env` already includes `CORS_ORIGINS=http://localhost:3000` — verify on first run |
| recharts bundle exceeds 200KB budget | Medium | Low | Recharts is loaded with `next/dynamic` — excluded from initial bundle; verify with `next build --debug` |
| WCAG 2.1 AA colour contrast failures in dark theme | Low | Medium | All color tokens pre-verified in research.md against 4.5:1 ratio; run axe-core in Playwright E2E |
