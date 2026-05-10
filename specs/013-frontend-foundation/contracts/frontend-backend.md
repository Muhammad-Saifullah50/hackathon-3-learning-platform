# API Contracts: Frontend → FastAPI Backend

**Branch**: `013-frontend-foundation` | **Date**: 2026-05-09

All requests go to `NEXT_PUBLIC_BACKEND_URL` (default: `http://localhost:8000`).
Authenticated requests include `Authorization: Bearer {fastApiToken}` header.
The `fastApiToken` is extracted from the Better Auth session via `session.session.fastApiToken`.

---

## Auth Endpoints (FastAPI prefix: `/api/auth`)

### POST /api/auth/register
Registers a new user. Called by the Next.js proxy route `POST /api/register-proxy` during the dual-record registration flow.

**Request**
```json
{
  "email": "student@example.com",
  "password": "SecureP@ss123",
  "display_name": "Alice Smith",
  "role": "student"
}
```

**Response 201**
```json
{
  "message": "Registration successful. Please verify your email.",
  "user_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Errors**
| Status | Condition |
|--------|-----------|
| 400 | Email already registered |
| 400 | Password too weak (< 8 chars, no special char, HIBP flagged) |
| 422 | Validation error (malformed email, etc.) |

---

### POST /api/auth/login
Validates credentials. Called by Better Auth's `password.verify` hook — never called directly by the frontend UI.

**Request**
```json
{
  "email": "student@example.com",
  "password": "SecureP@ss123"
}
```

**Response 200**
```json
{
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "student@example.com",
    "role": "student",
    "display_name": "Alice Smith",
    "email_verified_at": null,
    "created_at": "2026-05-09T10:00:00Z",
    "updated_at": "2026-05-09T10:00:00Z"
  },
  "tokens": {
    "access_token": "eyJ...",
    "refresh_token": "eyJ...",
    "token_type": "bearer",
    "expires_in": 900
  }
}
```

**Errors**
| Status | Condition |
|--------|-----------|
| 401 | Invalid credentials |
| 429 | Rate limited (5 failures → 15 min lockout) |

---

### POST /api/auth/password-reset/request
Requests a password-reset email. Frontend sends this on `POST /forgot-password`.

**Request**
```json
{ "email": "student@example.com" }
```

**Response 200** (always 200 — no email enumeration)
```json
{ "message": "If that email exists, a reset link has been sent." }
```

---

### POST /api/auth/password-reset/confirm
Sets a new password using the token from the reset email link.

**Request**
```json
{
  "token": "abc123resettoken",
  "new_password": "NewSecure@789"
}
```

**Response 200**
```json
{ "message": "Password reset successful." }
```

**Errors**
| Status | Condition |
|--------|-----------|
| 400 | Token expired or invalid |
| 400 | New password does not meet complexity rules |

---

### POST /api/auth/logout
Revokes the FastAPI session. Called when `authClient.signOut()` fires.

**Request** — requires `Authorization: Bearer {access_token}` header

**Response 200**
```json
{ "message": "Logged out successfully." }
```

---

## Profile Endpoint (FastAPI prefix: `/api`)

### GET /api/profile
Returns the current user's full profile, including bio and preferences.

**Headers**: `Authorization: Bearer {fastApiToken}`

**Response 200**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "student@example.com",
  "display_name": "Alice Smith",
  "role": "student",
  "bio": null,
  "email_verified_at": null,
  "preferences": {},
  "created_at": "2026-05-09T10:00:00Z",
  "updated_at": "2026-05-09T10:00:00Z"
}
```

**Errors**
| Status | Condition |
|--------|-----------|
| 401 | Missing or expired token |

---

## Agent Endpoints (FastAPI prefix: `/api/v1/agents`)

### GET /api/v1/agents/progress/summary
Returns the student's mastery summary across all modules, streak, weak areas, and recommendations.

**Headers**: `Authorization: Bearer {fastApiToken}`

**Response 200**
```json
{
  "overall_mastery": 42.5,
  "topics": [
    {
      "topic": "Python Basics",
      "score": 75.0,
      "level": "Proficient",
      "component_breakdown": {
        "exercises": 80,
        "quizzes": 70,
        "code_quality": 75,
        "consistency": 60
      }
    }
  ],
  "weak_areas": ["Control Flow", "Object-Oriented"],
  "streak": {
    "current_streak": 3,
    "longest_streak": 7
  },
  "recommendations": [
    "Practice more exercises on Control Flow loops",
    "Review OOP inheritance concepts"
  ],
  "missing_components": ["quizzes"]
}
```

**Empty State (new user — no data)**
```json
{
  "overall_mastery": 0,
  "topics": [],
  "weak_areas": [],
  "streak": null,
  "recommendations": ["Start with Python Basics to begin your learning journey!"],
  "missing_components": ["exercises", "quizzes", "code_quality", "consistency"]
}
```

**Errors**
| Status | Condition |
|--------|-----------|
| 401 | Missing or expired token |
| 500 | Agent error (show retry UI) |

---

## Next.js Internal API Routes (Frontend → Next.js BFF)

These routes exist within the Next.js app and proxy or transform requests.

### POST /api/register-proxy
Handles the dual-record registration (FastAPI user + Better Auth user). Not called directly by the client UI — the registration form calls `authClient.signUp.email()` which triggers this internally.

### POST + GET /api/auth/[...all]
Better Auth handler — manages sessions, sign-in, sign-out, password reset tokens.
Consumed exclusively by the Better Auth client (`authClient.*`).

---

## Error Handling Convention

All frontend API calls follow this pattern:

```typescript
// lib/api.ts
async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BACKEND_URL}${path}`, options)
  if (res.status === 401) {
    // Trigger token refresh or redirect to login
    throw new UnauthorizedError()
  }
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw new ApiError(res.status, body.detail || "Request failed")
  }
  return res.json()
}
```

Token refresh on 401:
- If `fastApiToken` is expired, call FastAPI `POST /api/auth/refresh` with the stored refresh token
- Update the Better Auth session with the new access token
- Retry the original request once
- If refresh also fails → call `authClient.signOut()` + redirect to `/login?reason=session_expired`
