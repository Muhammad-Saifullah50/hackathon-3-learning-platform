# Data Model: 013 — Frontend Foundation & Student Dashboard

**Date**: 2026-05-09 | **Branch**: `013-frontend-foundation`

This document describes the frontend data layer — TypeScript types consumed by components and the Better Auth tables created in the shared Neon database.

---

## Frontend TypeScript Types

### Auth / Session

```typescript
// User identity stored in Better Auth session
interface AuthUser {
  id: string          // UUID matching FastAPI users.id (synced on registration)
  email: string
  name: string        // Maps to FastAPI display_name
  role: "student" | "teacher" | "admin"
  emailVerified: boolean
  image?: string
}

// Better Auth session (available via useSession() hook)
interface Session {
  user: AuthUser
  session: {
    id: string
    token: string
    expiresAt: Date
    fastApiToken: string   // FastAPI JWT — used for backend API calls
  }
}
```

### Progress & Dashboard

```typescript
// From GET /api/v1/agents/progress/summary
interface ProgressSummary {
  overall_mastery: number           // 0–100 float
  topics: TopicMastery[]
  weak_areas: string[]
  streak: StreakInfo | null
  recommendations: string[]
  missing_components: string[]
}

interface TopicMastery {
  topic: string                    // Module name (matches curriculum seed data)
  score: number                    // 0–100 float
  level: MasteryLevel
  component_breakdown: {
    exercises?: number
    quizzes?: number
    code_quality?: number
    consistency?: number
  }
}

type MasteryLevel = "Beginner" | "Learning" | "Proficient" | "Mastered"

interface StreakInfo {
  current_streak: number
  longest_streak: number
}
```

### Module Cards (Dashboard)

```typescript
// Derived from TopicMastery — enriched with static curriculum metadata
interface ModuleCard {
  id: string                       // slug, e.g. "basics", "control-flow"
  displayName: string              // e.g. "Python Basics"
  moduleNumber: number             // 1–8
  score: number
  level: MasteryLevel
  color: MasteryColor              // Derived from level
  componentBreakdown: TopicMastery["component_breakdown"]
}

type MasteryColor = "red" | "amber" | "green" | "blue"

// Mastery level → color mapping (Business Logic — from CLAUDE.md)
const MASTERY_COLOR: Record<MasteryLevel, MasteryColor> = {
  "Beginner":   "red",    // 0–40%
  "Learning":   "amber",  // 41–70%
  "Proficient": "green",  // 71–90%
  "Mastered":   "blue",   // 91–100%
}
```

### Static Curriculum Metadata (8 Modules)

```typescript
// Seeded in DB — used to enrich progress data and fill empty state
const CURRICULUM_MODULES = [
  { id: "basics",         displayName: "Python Basics",        moduleNumber: 1 },
  { id: "control-flow",   displayName: "Control Flow",         moduleNumber: 2 },
  { id: "data-structures",displayName: "Data Structures",      moduleNumber: 3 },
  { id: "functions",      displayName: "Functions",            moduleNumber: 4 },
  { id: "oop",            displayName: "Object-Oriented",      moduleNumber: 5 },
  { id: "files",          displayName: "File Handling",        moduleNumber: 6 },
  { id: "errors",         displayName: "Error Handling",       moduleNumber: 7 },
  { id: "libraries",      displayName: "Libraries & APIs",     moduleNumber: 8 },
] as const
```

### API Client Response Types

```typescript
// POST /api/auth/login response (FastAPI)
interface LoginResponse {
  user: {
    id: string
    email: string
    role: string
    display_name: string
    email_verified_at: string | null
    created_at: string
    updated_at: string
  }
  tokens: {
    access_token: string
    refresh_token: string
    token_type: "bearer"
    expires_in: number   // seconds
  }
}

// POST /api/auth/register response (FastAPI)
interface RegisterResponse {
  message: string
  user_id: string
}

// GET /api/profile response (FastAPI)
interface ProfileResponse {
  id: string
  email: string
  display_name: string
  role: string
  bio: string | null
  email_verified_at: string | null
  preferences: Record<string, unknown>
  created_at: string
  updated_at: string
}
```

---

## Better Auth Database Tables (New — Neon PostgreSQL)

Better Auth creates these tables automatically on first `auth.handler` call when `autoMigrate` is enabled, or via a manual Alembic migration file added to the backend.

### `user` (Better Auth — separate from FastAPI `users`)

| Column | Type | Notes |
|--------|------|-------|
| `id` | `text` PK | UUID string |
| `name` | `text` NOT NULL | Maps to FastAPI `display_name` |
| `email` | `text` NOT NULL UNIQUE | |
| `email_verified` | `boolean` | |
| `image` | `text` NULL | Not used in MVP |
| `role` | `text` DEFAULT `'student'` | Custom field: student / teacher / admin |
| `fast_api_id` | `text` NULL | FastAPI `users.id` UUID — sync reference |
| `created_at` | `timestamp` | |
| `updated_at` | `timestamp` | |

### `session`

| Column | Type | Notes |
|--------|------|-------|
| `id` | `text` PK | |
| `expires_at` | `timestamp` NOT NULL | |
| `token` | `text` NOT NULL UNIQUE | Better Auth session token |
| `user_id` | `text` FK → `user.id` | |
| `fast_api_token` | `text` NULL | FastAPI JWT access token — stored in session |
| `created_at` | `timestamp` | |
| `updated_at` | `timestamp` | |

### `account`

| Column | Type | Notes |
|--------|------|-------|
| `id` | `text` PK | |
| `account_id` | `text` NOT NULL | Provider account ID |
| `provider_id` | `text` NOT NULL | `"credential"` for email/password |
| `user_id` | `text` FK → `user.id` | |
| `password` | `text` NULL | Empty string (credential validation proxied to FastAPI) |
| `created_at` | `timestamp` | |
| `updated_at` | `timestamp` | |

### `verification`

| Column | Type | Notes |
|--------|------|-------|
| `id` | `text` PK | |
| `identifier` | `text` NOT NULL | Email address |
| `value` | `text` NOT NULL | Verification token |
| `expires_at` | `timestamp` NOT NULL | |
| `created_at` | `timestamp` | |
| `updated_at` | `timestamp` | |

---

## State Transitions

### Auth State Machine

```
[Unauthenticated]
      │ signIn.email() success
      ▼
[Authenticated: student]  ──── signOut() ────► [Unauthenticated]
      │
      │ role check in layout
      ▼
[Dashboard accessible]

[Authenticated: teacher]
      │ role check in layout
      ▼
[/teacher/coming-soon]
```

### Module Card States

```
[0% — No data]  ──── progress loaded ────► [Scored — level from score]
                                                  │
                             ┌────────────────────┼────────────────────┐
                         0–40%                 41–70%                71–90%           91–100%
                       Beginner (red)       Learning (amber)     Proficient (green)  Mastered (blue)
```
