# Research: 013 — Frontend Foundation & Student Dashboard

**Date**: 2026-05-09 | **Branch**: `013-frontend-foundation`

---

## 1. Next.js Version Decision

### Decision
Use **Next.js 16** (current `next@latest`).

### Key Next.js 16 Changes vs. 14 (Must Implement Correctly)

| Area | Change | Impact |
|------|--------|--------|
| Bundler | Turbopack is the **default** — no `--turbopack` flag needed | Remove flag from dev scripts |
| `cookies()` / `headers()` | Now **async** — must `await` | All route handlers, server components |
| `params` / `searchParams` | Now **Promise-wrapped** — must `await props.params` | Every dynamic route page |
| React version | Requires **React 19** | Update peer deps |
| Upgrade path | `npm install next@latest` or `npx @next/codemod@canary upgrade latest` | Use codemod for green-field |

### package.json scripts (Next.js 16 — Turbopack default)
```json
{
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start"
  }
}
```

### Async params pattern (dynamic routes)
```typescript
// /app/(student)/quiz/[lessonId]/page.tsx
export default async function QuizPage(props: {
  params: Promise<{ lessonId: string }>
}) {
  const { lessonId } = await props.params
  // ...
}
```

### Async cookies pattern (route handlers / server components)
```typescript
import { cookies } from 'next/headers'
const cookieStore = await cookies()   // Must await in Next.js 15/16
const token = cookieStore.get('token')
```

---

## 2. Better Auth Integration Strategy

### Decision
Better Auth uses `pg.Pool` (no Drizzle/Prisma required) connected to the **same Neon PostgreSQL** database. It creates its own tables (`user`, `session`, `account`, `verification`) which are separate from FastAPI's `users` table. Credential validation is **proxied to FastAPI** via a custom `password.verify` function.

### Rationale
- Constitution mandates: "Use BetterAuth — NEVER build auth yourself"
- `pg.Pool` is supported natively — no ORM dependency overhead
- Custom `password.verify` lets FastAPI remain the authoritative credential validator (avoids duplicating bcrypt logic)
- Better Auth manages session cookies; FastAPI JWT stored in session for backend API calls

### Alternatives Considered
- **Drizzle + column mapping to existing users table**: Complex, requires Drizzle ORM, column-name mismatch between Better Auth schema (`name`, `emailVerified`) and FastAPI schema (`display_name`, `email_verified_at`)
- **Raw cookies only (no Better Auth)**: Violates constitution. Rejected.
- **Better Auth with full duplicate user table**: Chosen approach with dual-record sync on registration

### Dual-record Sync on Registration

Registration flow (the only place duplication occurs):
1. User submits register form → calls Next.js API route `POST /api/auth/register-proxy`
2. Next.js route calls FastAPI `POST /api/auth/register` → FastAPI creates `users` record with bcrypt hash
3. On success → Next.js route calls `auth.api.signUpEmail()` internally → Better Auth creates `user` record (password stored as empty string — credential validation is always proxied to FastAPI)
4. Better Auth session cookie set, role stored in Better Auth `user.role` (custom field)

Login flow:
1. Client calls `authClient.signIn.email({ email, password })`
2. Better Auth server calls custom `password.verify({ hash, password })` which calls FastAPI `POST /api/auth/login`
3. FastAPI returns `{ user, tokens }` → `verify` returns `true` + stores FastAPI `access_token` in session metadata
4. Better Auth sets session cookie containing `fastApiToken`

### Better Auth Server Config
```typescript
import { betterAuth } from "better-auth"
import { Pool } from "pg"

export const auth = betterAuth({
  secret: process.env.BETTER_AUTH_SECRET!,
  baseURL: process.env.BETTER_AUTH_BASE_URL || "http://localhost:3000",
  database: new Pool({ connectionString: process.env.DATABASE_URL }),
  emailAndPassword: {
    enabled: true,
    disableSignUp: true,             // Sign-up handled by custom proxy route
    sendResetPassword: async ({ user, url }) => {
      // Proxy to FastAPI password reset
    },
    password: {
      hash: async (password) => password,   // Never called (signUp disabled)
      verify: async ({ hash, password, ...ctx }) => {
        const res = await fetch(`${BACKEND_URL}/api/auth/login`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ email: ctx.email, password }),
        })
        if (!res.ok) return false
        const data = await res.json()
        // Store FastAPI token for this session
        ctx.session.fastApiToken = data.tokens.access_token
        return true
      }
    }
  },
  user: {
    additionalFields: {
      role: { type: "string", defaultValue: "student" },
      fastApiId: { type: "string" },
    }
  },
  session: {
    expiresIn: 7 * 24 * 60 * 60,
    additionalFields: {
      fastApiToken: { type: "string" },
    }
  }
})
```

### Better Auth Middleware Pattern (Fast — No DB Hit)
```typescript
// middleware.ts
import { getSessionCookie } from "better-auth/cookies"
import { NextRequest, NextResponse } from "next/server"

export async function middleware(request: NextRequest) {
  const session = getSessionCookie(request)   // Cookie check only — fast
  const { pathname } = request.nextUrl

  if (!session && !isPublicPath(pathname)) {
    const url = new URL("/login", request.url)
    url.searchParams.set("next", pathname)
    return NextResponse.redirect(url)
  }

  // Role routing handled in layout server components
  return NextResponse.next()
}
```

Role-based routing (student vs. teacher) is handled inside the `(student)/layout.tsx` and `(teacher)/layout.tsx` **server components** using `auth.api.getSession({ headers: await headers() })` — not in middleware — to avoid DB hits on every request.

### Better Auth Client
```typescript
// lib/auth-client.ts
import { createAuthClient } from "better-auth/react"

export const authClient = createAuthClient({
  baseURL: process.env.NEXT_PUBLIC_APP_URL || "http://localhost:3000",
})

export const { signIn, signOut, signUp, useSession } = authClient
```

---

## 3. shadcn/ui + Tailwind + Theming

### Decision
- **Component library**: shadcn/ui (`new-york` style) with custom CSS-variable color palette
- **Dark mode**: Tailwind `darkMode: ['class']`, toggled by next-themes with `attribute="class"`
- **Fonts**: Three Google Fonts via `next/font/google` as CSS variables

### Font Choices (Distinctive — Avoids Generic)
| Role | Font | Variable |
|------|------|----------|
| Headings | `Fraunces` (variable optical-size serif) | `--font-heading` |
| Body / UI | `Outfit` (geometric sans) | `--font-sans` |
| Code | `JetBrains Mono` | `--font-mono` |

### Color Palette (LearnFlow — Warm Code Scholar)
| Token | Light (HSL) | Dark (HSL) | Usage |
|-------|-------------|------------|-------|
| `--background` | `40 30% 98%` (warm white) | `220 20% 7%` (near-black) | Page bg |
| `--foreground` | `25 25% 10%` (espresso) | `40 20% 94%` (warm white) | Text |
| `--card` | `40 25% 100%` | `220 18% 10%` | Card bg |
| `--primary` | `35 90% 48%` (amber) | `38 95% 58%` (bright amber) | Buttons, active |
| `--muted` | `40 20% 93%` | `220 15% 16%` | Muted bg |
| `--muted-foreground` | `30 10% 45%` | `220 10% 60%` | Subtle text |
| `--border` | `35 20% 88%` | `220 15% 20%` | Borders |
| `--destructive` | `0 85% 60%` | `0 70% 55%` | Errors |

### Mastery Level Colors (hardcoded, not CSS variables)
```css
.mastery-beginner   { color: hsl(0 80% 55%); }     /* Red */
.mastery-learning   { color: hsl(40 95% 50%); }    /* Yellow/Amber */
.mastery-proficient { color: hsl(142 70% 40%); }   /* Green */
.mastery-mastered   { color: hsl(217 90% 55%); }   /* Blue */
```

### FOUC Prevention (System Default)
```tsx
// app/layout.tsx — The inline script must be in <head> BEFORE body
<html lang="en" suppressHydrationWarning>
  <head>
    <script dangerouslySetInnerHTML={{ __html: `
      try {
        const theme = localStorage.getItem('theme')
        if (theme === 'dark' || (!theme && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
          document.documentElement.classList.add('dark')
        }
      } catch {}
    `}} />
  </head>
  <body className={`${heading.variable} ${sans.variable} ${mono.variable}`}>
    <ThemeProvider attribute="class" defaultTheme="system" enableSystem storageKey="theme">
      {children}
    </ThemeProvider>
  </body>
</html>
```

### components.json
```json
{
  "$schema": "https://ui.shadcn.com/schema.json",
  "style": "new-york",
  "rsc": true,
  "tsx": true,
  "tailwind": {
    "config": "tailwind.config.ts",
    "css": "src/app/globals.css",
    "baseColor": "stone"
  },
  "aliases": {
    "components": "@/components",
    "utils": "@/lib/utils",
    "ui": "@/components/ui",
    "lib": "@/lib",
    "hooks": "@/hooks"
  }
}
```

---

## 4. React Query + Server Components Pattern

### Decision
Use `@tanstack/react-query` v5 for all client-side data fetching. Dashboard data is fetched **server-side** (server component) for initial render, then optionally hydrated into React Query for client-side refetch.

### Dashboard Data Pattern
```tsx
// app/(student)/dashboard/page.tsx — Server Component
import { auth } from "@/lib/auth"
import { headers } from "next/headers"

export default async function DashboardPage() {
  const session = await auth.api.getSession({ headers: await headers() })
  const progress = await fetch(`${BACKEND_URL}/api/v1/agents/progress/summary`, {
    headers: { Authorization: `Bearer ${session?.session.fastApiToken}` },
    next: { revalidate: 60 }   // ISR — revalidate every 60s
  }).then(r => r.json())

  return <DashboardClient initialData={progress} session={session} />
}
```

---

## 5. New Alembic Migration Required

Better Auth needs three new tables in Neon PostgreSQL:

| Table | Purpose |
|-------|---------|
| `user` (Better Auth) | Better Auth user records (separate from FastAPI `users`) |
| `session` | Better Auth sessions (token, expiry, fastApiToken) |
| `account` | OAuth account linking (email/password provider) |
| `verification` | Email verification tokens |

A new Alembic migration (`20260509_create_better_auth_tables.py`) must be added to the backend, even though these tables are owned by the frontend session layer.
