# Quickstart: 013 — Frontend Foundation

**Branch**: `013-frontend-foundation`

Prerequisites: Node.js 20+, the FastAPI backend running on `http://localhost:8000`, and MailHog on `localhost:1025` for email previews.

---

## 1. Bootstrap the Next.js Project

```bash
cd /home/saifullah/projects/hackathon-2-learning-platform/frontend

# Install Next.js 16 with all dependencies
npm install next@latest react@latest react-dom@latest typescript @types/node @types/react @types/react-dom

# Auth + session
npm install better-auth pg @types/pg

# UI
npm install tailwindcss@latest postcss autoprefixer
npm install tailwindcss-animate class-variance-authority clsx tailwind-merge
npm install next-themes lucide-react sonner recharts

# Data fetching + forms
npm install @tanstack/react-query zod react-hook-form @hookform/resolvers

# Dev tooling
npm install -D eslint eslint-config-next prettier
```

## 2. Initialise shadcn/ui

```bash
# From frontend/
npx shadcn@latest init
# Select: New York style, Stone base, yes to CSS variables, src/ directory

# Install all components used in this feature
npx shadcn@latest add button card input label badge progress separator
npx shadcn@latest add dropdown-menu avatar tooltip skeleton
npx shadcn@latest add form   # react-hook-form integration
npx shadcn@latest add toast  # via sonner
```

## 3. Environment Variables

Create `frontend/.env.local`:

```bash
# Backend
NEXT_PUBLIC_BACKEND_URL=http://localhost:8000

# Better Auth
BETTER_AUTH_SECRET=generate-with-openssl-rand-base64-32
BETTER_AUTH_BASE_URL=http://localhost:3000

# Database (same Neon URL as backend — Better Auth needs it for sessions)
DATABASE_URL=postgresql://neondb_owner:<password>@<host>/neondb?sslmode=require

# App URL (used for password reset email links)
NEXT_PUBLIC_APP_URL=http://localhost:3000
```

## 4. Apply Better Auth Database Migration

Better Auth needs four new tables in the shared Neon database. Add the migration to the **backend** Alembic chain:

```bash
# From backend/
# The migration file is at:
# backend/alembic/versions/20260509_create_better_auth_tables.py
# (created as part of this feature's tasks)

alembic upgrade head
```

## 5. Run the Development Server

```bash
# Terminal 1: FastAPI backend
cd backend && uvicorn src.main:app --reload --port 8000

# Terminal 2: Next.js frontend (Turbopack is now default in Next.js 16)
cd frontend && npm run dev
# → http://localhost:3000
```

## 6. Verify Installation

| Check | Expected |
|-------|----------|
| `http://localhost:3000/login` | Login page renders with Fraunces headings |
| `http://localhost:3000/register` | Registration form renders |
| Register with `test@example.com / Test@1234` | Redirects to `/dashboard` |
| `/dashboard` renders all 8 module cards at 0% | Empty state with encouragement message |
| Toggle theme in nav | Switches light ↔ dark with no flash |
| Visit `/dashboard` while logged out | Redirects to `/login?next=/dashboard` |

## 7. Project Structure

```
frontend/
├── .env.local                 # ← Copy from .env.local.example
├── next.config.ts
├── tailwind.config.ts
├── components.json            # shadcn/ui config
├── tsconfig.json
├── middleware.ts              # Route protection (Better Auth cookie check)
└── src/
    ├── app/
    │   ├── globals.css        # CSS vars, fonts, Tailwind base
    │   ├── layout.tsx         # Root layout — ThemeProvider, fonts
    │   ├── page.tsx           # Redirect → /dashboard or /login
    │   ├── (auth)/
    │   │   ├── layout.tsx     # Centred auth layout (no sidebar)
    │   │   ├── login/page.tsx
    │   │   ├── register/page.tsx
    │   │   ├── forgot-password/page.tsx
    │   │   └── reset-password/page.tsx
    │   ├── (student)/
    │   │   ├── layout.tsx     # Sidebar + top-nav, role guard (student only)
    │   │   ├── dashboard/page.tsx   ← Full real-data page
    │   │   ├── chat/page.tsx        ← Stub
    │   │   ├── progress/page.tsx    ← Stub
    │   │   └── quiz/[lessonId]/page.tsx  ← Stub
    │   ├── (teacher)/
    │   │   └── teacher/
    │   │       └── coming-soon/page.tsx
    │   └── api/
    │       ├── auth/[...all]/route.ts    # Better Auth handler
    │       └── register-proxy/route.ts  # Dual-record registration
    ├── components/
    │   ├── providers/
    │   │   ├── query-provider.tsx  # TanStack Query client
    │   │   └── theme-provider.tsx  # next-themes wrapper
    │   ├── layout/
    │   │   ├── student-sidebar.tsx
    │   │   └── top-nav.tsx
    │   ├── ui/                     # shadcn/ui components (auto-generated)
    │   ├── auth/
    │   │   ├── login-form.tsx
    │   │   ├── register-form.tsx
    │   │   ├── forgot-password-form.tsx
    │   │   └── reset-password-form.tsx
    │   └── dashboard/
    │       ├── module-card.tsx
    │       ├── module-grid.tsx
    │       ├── streak-badge.tsx
    │       ├── mastery-overview.tsx
    │       ├── weak-areas-panel.tsx
    │       ├── recommendations-panel.tsx
    │       └── dashboard-skeleton.tsx
    ├── lib/
    │   ├── auth.ts          # Better Auth server instance
    │   ├── auth-client.ts   # Better Auth React client
    │   ├── api.ts           # FastAPI fetch wrapper (auth header, 401 refresh)
    │   └── utils.ts         # cn(), masteryColor(), masteryLabel() helpers
    ├── hooks/
    │   ├── use-progress.ts  # React Query hook for /progress/summary
    │   └── use-profile.ts   # React Query hook for /profile
    └── types/
        └── index.ts         # All TypeScript interfaces from data-model.md
```
