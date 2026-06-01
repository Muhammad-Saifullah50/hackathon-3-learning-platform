---
id: 001
title: Create LearnPyByAI Constitution
stage: constitution
date: 2026-03-14
surface: agent
model: claude-sonnet-4.5
feature: none
branch: master
user: Muhammad-Saifullah50
command: /sp.constitution
labels: ["constitution", "governance", "standards", "learnpybyai"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - .specify/memory/constitution.md
tests:
  - N/A (documentation only)
---

## Prompt

use this data and the claude.md to create a constitution for this projkject useing /sp.constitution command

Perfect — now I have exactly what I need. Let me refine everything specifically for a **solo dev** running a **Next.js + FastAPI + PostgreSQL + LLM-agnostic** stack where quality, speed, and scale all matter equally.

---

## 🏗️ Engineering Standards for **LearnPyByAI**
*Next.js · FastAPI · PostgreSQL · LLM-agnostic · Solo Developer*

---

### 1. Code Quality Standards

**Formatting — Fully Automated (zero mental overhead)**
- **Python:** `black` (line length 88) + `isort`. Runs automatically on save + pre-commit hook.
- **TypeScript:** `prettier` + `eslint` with Next.js config. Auto-format on save.
- One command to lint everything: `make lint` — wraps both in a Makefile.
- CI blocks merges if either fails. You don't negotiate with formatting.

**Naming Conventions**

| Layer | Convention | Example |
|---|---|---|
| Python functions/vars | `snake_case` | `get_lesson_by_slug` |
| Python classes | `PascalCase` | `LessonProgressService` |
| React components | `PascalCase` | `CodeEditor.tsx` |
| TS vars/hooks | `camelCase` | `useUserProgress` |
| Custom hooks | `use` prefix | `useLessonStream` |
| DB columns | `snake_case` | `completed_at`, `user_id` |
| Env vars | `SCREAMING_SNAKE_CASE` | `OPENAI_API_KEY` |
| API routes | `kebab-case` nouns | `/api/lesson-progress` |
| LLM provider files | `provider_name.py` | `openai.py`, `claude.py` |

**Documentation — Lightweight but Consistent**
- All Python functions with business logic get a **Google-style docstring** (args, returns, raises). Pure utilities can skip it if the name is self-explanatory.
- React components: JSDoc comment on props interface — not the component itself.
- FastAPI routes: fill the `summary=` and `description=` fields — you get free Swagger docs.
- Maintain a `/docs/decisions/` folder with lightweight ADRs (Architecture Decision Records) — one markdown file per major decision. You'll thank yourself in 6 months.
- Convert any `# TODO` older than 2 weeks into a GitHub Issue immediately.

---

### 2. Testing Principles

**Coverage Targets — Pragmatic for Solo Dev**

| Layer | Target | What to Prioritize |
|---|---|---|
| FastAPI routes | 80% | Auth, progress tracking, lesson delivery |
| LLM adapter layer | 70% | Prompt builders, response parsers |
| DB repositories | 85% | Data integrity is sacred |
| React components | 65% | User interaction flows, not rendering |
| E2E flows | 5 journeys | Login → lesson → submit → feedback |

**Test Types (in execution order)**
1. **Unit** — Pure functions, prompt builders, utility helpers (`pytest` + `vitest`)
2. **Integration** — FastAPI routes against a real test DB (`pytest` + `httpx` async client + separate `test_` Postgres schema)
3. **Component** — React with `@testing-library/react`, focus on user events
4. **E2E** — `Playwright` for 5 critical journeys only. Don't over-invest here as a solo dev.
5. **LLM contract tests** — Assert the *shape* of AI responses (has `explanation`, `code_snippet`, etc.), never the content. Run against real API weekly as a smoke test; mock in unit tests always.

**TDD Approach — Apply Selectively**
- **Strict TDD (always):** Auth flows, billing/progress logic, code sandbox execution
- **Test-after (acceptable):** UI components, prompt engineering, experimental features
- **One non-negotiable rule:** Every bug fix starts with a failing test that reproduces the bug. No exceptions.

---

### 3. Performance Guidelines

**Latency Budgets**

| Operation | Target P95 | Hard Limit |
|---|---|---|
| Next.js page load (SSR) | < 800ms | 2s |
| FastAPI response (non-AI) | < 150ms | 400ms |
| AI first token (streaming) | < 1.2s | — |
| AI full response | — | 30s timeout |
| Python code execution | < 3s | 8s |
| PostgreSQL query | < 40ms | 150ms |

**Resource Limits**
- LLM calls: cap input at `1,200` tokens, output at `600` for feedback/hints. Tune per endpoint.
- Rate limit AI endpoints: **10 req/min per user** via `slowapi` on FastAPI. Protects you from both abuse and runaway costs.
- Code sandbox: 128MB RAM, 5s CPU, **zero network access**, temp filesystem only.
- Bundle size: keep Next.js initial JS under 200KB gzipped. Use `next/dynamic` for the code editor.

**Optimization Rules — Solo Dev Friendly**
- **Cache identical LLM prompt+lesson combinations** in PostgreSQL (a simple `llm_cache` table with a hash key) — this is the single biggest cost saver.
- Stream all AI responses using FastAPI `StreamingResponse` + Next.js `ReadableStream`. Never make the user wait for a full response.
- Add DB indexes on `user_id`, `lesson_id`, `created_at` from day one. Run `EXPLAIN ANALYZE` before any new query goes to production.
- Use Next.js `<Image>` for all images, `next/dynamic` for heavy components (Monaco editor, etc.).
- As a solo dev, **profile before optimizing** — add `time.perf_counter()` logs around suspected bottlenecks first.

---

### 4. Security Constraints

**Authentication Patterns**
- Use **Supabase Auth or NextAuth.js** — do not build auth yourself. Ever.
- Short-lived JWTs (15 min access + 7 day refresh). Handled by your auth provider.
- All FastAPI routes require auth by default via a `get_current_user` dependency. Explicitly whitelist public routes.
- Rate-limit login: 5 failures → 15-minute lockout.
- As a solo dev, **add auth on day one** — retrofitting it is 3x the work.

**Data Handling**
- User-submitted Python code runs in a **fully isolated sandbox** (Docker container or a service like Piston API) — never `exec()` or `eval()` on your server. This is non-negotiable.
- Never log user code or AI conversations in raw production logs.
- Store only what you need: email, hashed preferences, lesson progress. No unnecessary PII.
- Build a "Delete My Account" endpoint from the start — hard to bolt on later.

**Secrets Management**
- Local: `.env.local` for Next.js, `.env` for FastAPI. Both in `.gitignore` from commit #1.
- Install `detect-secrets` as a pre-commit hook — it will catch keys before they hit GitHub.
- Production: Vercel env vars (frontend) + Railway/Render secret manager (backend).
- **LLM-agnostic pattern:** All API keys behind a single `LLMProviderConfig` class — swap providers by changing one env var (`LLM_PROVIDER=claude`), not 10 files.
- Audit secrets every quarter. Rotate immediately if ever exposed.

---

### 5. Architecture Patterns

**Preferred Stack Decisions**

| Frontend | Next.js 16+ App Router | Streaming, SSR, API routes built-in |
| Backend | FastAPI + `asyncio` | Async-first, typed, auto OpenAPI docs |
| ORM | SQLAlchemy 2.0 (async) + Alembic | Type-safe, migrations, async support |
| Auth | betterauth | Managed, battle-tested |
| LLM abstraction | Custom `LLMProvider` interface | Swap OpenAI ↔ Claude ↔ Gemini freely |
| Styling | Tailwind CSS | Fast iteration, no context switching |
| State (client) | Zustand | Simple, no boilerplate, scales fine |
| Testing | pytest + Playwright + Vitest | Best-in-class per layer |

**Design Patterns — The Three You Actually Need**

**Repository Pattern** (DB access only through repos, never raw queries in routes):
```python
# ✅ Right
class LessonRepository:
    async def get_by_slug(self, slug: str) -> Lesson: ...

# ❌ Wrong — raw query in route handler
@router.get("/lessons/{slug}")
async def get_lesson(slug: str, db: Session = Depends(get_db)):
    return db.query(Lesson).filter(Lesson.slug == slug).first()
```

**LLM Provider Abstraction** (your most important pattern as an LLM-agnostic app):
```python
class LLMProvider(Protocol):
    async def complete(self, prompt: str, **kwargs) -> AsyncIterator[str]: ...

class OpenAIProvider:
    async def complete(self, prompt: str, **kwargs) -> AsyncIterator[str]: ...

class ClaudeProvider:
    async def complete(self, prompt: str, **kwargs) -> AsyncIterator[str]: ...

# Swap via env var — zero code changes
```


Load, version, and A/B test prompts without deployments.

**Anti-Patterns to Actively Avoid**

- ❌ Business logic inside FastAPI route handlers
- ❌ Calling LLM APIs synchronously (always stream or background)
- ❌ Hardcoding the LLM provider anywhere except the factory
- ❌ Running user code outside an isolated sandbox
- ❌ Skipping Alembic migrations — never alter the DB schema directly
- ❌ Over-engineering early — no microservices, no message queues until you have users screaming for them

---

### 6. Development Workflow

**Branching Strategy — GitHub Flow (right-sized for solo)**
```
main  ←  always deployable, branch-protected
  └── feature/llm-provider-abstraction
  └── fix/streaming-timeout-on-slow-responses
  └── chore/upgrade-sqlalchemy-2
  └── experiment/gemini-integration
```
- Every change goes through a PR — even as a solo dev. Review your own diff after a coffee break. You will catch things.
- Use `experiment/` branches for LLM provider trials — keeps `main` clean.

**Commit Conventions — Conventional Commits**
```bash
feat: add streaming AI feedback to code editor
fix: handle LLM timeout with graceful fallback message
chore: update FastAPI to 0.115 and regenerate lockfile
docs: add ADR for LLM provider abstraction pattern
test: add integration tests for lesson progress endpoint
experiment: test Claude Haiku for hint latency
```
Enforce with `commitlint`. Enables automatic changelogs via `release-please` when you're ready.

**Your CI Pipeline (GitHub Actions — keep it fast, under 3 min)**
```
Push / PR →
  [Parallel]
    ├── Python: black + isort + mypy + pytest
    └── TypeScript: prettier + eslint + vitest
  [Sequential]
    └── Playwright E2E (on PR to main only)
  [Deploy]
    └── Vercel (frontend) + Railway (backend) auto-deploy on merge to main
```

**Review Process — Solo Dev Edition**
- Write a PR description answering: *What changed? Why? How did you test it?*
- Let PRs sit for at least a few hours before merging — async self-review catches bugs.
- For any AI/LLM feature: manually test with 5+ real prompts before merging.
- Keep PRs under 300 lines. If it's larger, split it — your future self is the reviewer.
- Tag PRs with `[EXPERIMENT]` if they're LLM provider trials — makes rollback decisions obvious.

---

> **The solo dev golden rule:** Every standard here should take less time than the bugs it prevents. Automate everything that can be automated (formatting, linting, deploys), so your mental energy goes into the hard parts — great AI-powered learning experiences. 🚀

## Response snapshot

Created comprehensive LearnPyByAI Constitution v1.0.0 with 7 core principles:

1. **Code Quality Standards** - Automated formatting (black/prettier), naming conventions, documentation requirements
2. **Testing Principles** - Coverage targets (80% routes, 85% DB, 65% React), TDD approach, LLM contract tests
3. **Performance Standards** - Latency budgets (800ms SSR, 150ms API), resource limits, optimization rules (LLM caching)
4. **Security Constraints** - BetterAuth integration, isolated sandbox for code execution, secrets management
5. **Architecture Patterns** - Next.js + FastAPI + PostgreSQL stack, Repository pattern, LLM Provider abstraction
6. **Multi-Agent Architecture** - 6 specialized agents (Triage, Concepts, Code Review, Debug, Exercise, Progress)
7. **Business Logic Integrity** - Mastery calculation formula, struggle detection triggers, sandbox constraints

Added Development Workflow section with GitHub Flow, Conventional Commits, CI pipeline, and solo dev review process.

Constitution includes governance rules with semantic versioning (v1.0.0), ratification date (2026-03-14), and amendment process.

All templates verified for alignment - no updates needed.

## Outcome

- ✅ Impact: Created foundational governance document defining all engineering standards for LearnPyByAI project
- 🧪 Tests: N/A (documentation only)
- 📁 Files: Created .specify/memory/constitution.md (v1.0.0)
- 🔁 Next prompts: Begin feature specification with /sp.specify, or create first ADR for LLM provider abstraction
- 🧠 Reflection: Constitution successfully captures solo dev workflow for LLM-agnostic Python tutoring platform with multi-agent architecture

## Evaluation notes (flywheel)

- Failure modes observed: None
- Graders run and results (PASS/FAIL): PASS - All placeholders filled, version semantics correct, templates aligned
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): N/A
