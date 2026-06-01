# LearnPyByAI Constitution

<!--
Sync Impact Report:
- Version: 0.0.0 → 1.0.0 (Initial constitution creation)
- Modified Principles: N/A (new constitution)
- Added Sections: All (Code Quality, Testing, Performance, Security, Architecture, Development Workflow, Governance)
- Removed Sections: None
- Templates Requiring Updates:
  ✅ .specify/templates/plan-template.md (verified alignment)
  ✅ .specify/templates/spec-template.md (verified alignment)
  ✅ .specify/templates/tasks-template.md (verified alignment)
- Follow-up TODOs: None
-->

## Core Principles

### I. Code Quality Standards

**Formatting — Fully Automated**
- Python: `black` (line length 88) + `isort`. MUST run automatically on save + pre-commit hook.
- TypeScript: `prettier` + `eslint` with Next.js config. MUST auto-format on save.
- CI MUST block merges if linting fails. Formatting is non-negotiable.

**Naming Conventions**
- Python functions/variables: `snake_case`
- Python classes: `PascalCase`
- React components: `PascalCase`
- TypeScript variables/hooks: `camelCase`
- Custom hooks: `use` prefix (e.g., `useUserProgress`)
- Database columns: `snake_case`
- Environment variables: `SCREAMING_SNAKE_CASE`
- API routes: `kebab-case` nouns (e.g., `/api/lesson-progress`)
- LLM provider files: `provider_name.py` (e.g., `openai.py`, `claude.py`)

**Documentation Requirements**
- All Python functions with business logic MUST have Google-style docstrings (args, returns, raises).
- React components: JSDoc comment on props interface only.
- FastAPI routes: MUST fill `summary=` and `description=` fields for auto-generated Swagger docs.
- Maintain `/docs/decisions/` folder with lightweight ADRs for major architectural decisions.
- Convert any `# TODO` older than 2 weeks into a GitHub Issue immediately.

**Rationale:** Automated formatting eliminates bikeshedding. Consistent naming reduces cognitive load. Documentation is investment in future maintainability.

### II. Testing Principles (NON-NEGOTIABLE)

**Coverage Targets**
- FastAPI routes: 80% (prioritize auth, progress tracking, lesson delivery)
- LLM adapter layer: 70% (prompt builders, response parsers)
- Database repositories: 85% (data integrity is sacred)
- React components: 65% (user interaction flows, not rendering)
- E2E flows: 5 critical journeys minimum

**Test Types (execution order)**
1. Unit — Pure functions, prompt builders, utilities (`pytest` + `vitest`)
2. Integration — FastAPI routes against real test DB (`pytest` + `httpx` async client)
3. Component — React with `@testing-library/react`, focus on user events
4. E2E — `Playwright` for 5 critical journeys only
5. LLM contract tests — Assert response shape (has `explanation`, `code_snippet`), never content

**TDD Approach**
- Strict TDD (ALWAYS): Auth flows, billing/progress logic, code sandbox execution
- Test-after (acceptable): UI components, prompt engineering, experimental features
- Non-negotiable rule: Every bug fix MUST start with a failing test that reproduces the bug

**Rationale:** High test coverage on critical paths prevents regressions. TDD on security-sensitive code is mandatory. LLM contract tests ensure API compatibility without brittleness.

### III. Performance Standards

**Latency Budgets (P95)**
- Next.js page load (SSR): < 800ms (hard limit: 2s)
- FastAPI response (non-AI): < 150ms (hard limit: 400ms)
- AI first token (streaming): < 1.2s
- AI full response: 30s timeout
- Python code execution: < 3s (hard limit: 8s)
- PostgreSQL query: < 40ms (hard limit: 150ms)

**Resource Limits**
- LLM calls: cap input at 1,200 tokens, output at 600 tokens for feedback/hints
- Rate limit AI endpoints: 10 req/min per user via `slowapi` on FastAPI
- Code sandbox: 128MB RAM, 5s CPU, zero network access, temp filesystem only
- Bundle size: Next.js initial JS under 200KB gzipped

**Optimization Rules**
- Cache identical LLM prompt+lesson combinations in PostgreSQL (`llm_cache` table with hash key)
- Stream all AI responses using FastAPI `StreamingResponse` + Next.js `ReadableStream`
- Add DB indexes on `user_id`, `lesson_id`, `created_at` from day one
- Run `EXPLAIN ANALYZE` before any new query goes to production
- Use Next.js `<Image>` for all images, `next/dynamic` for heavy components (Monaco editor)
- Profile before optimizing — add `time.perf_counter()` logs around suspected bottlenecks first

**Rationale:** Performance budgets prevent death by a thousand cuts. Streaming improves perceived performance. Caching LLM responses is the single biggest cost saver.

### IV. Security Constraints (NON-NEGOTIABLE)

**Authentication Patterns**
- Use BetterAuth — NEVER build auth yourself
- Short-lived JWTs (15 min access + 7 day refresh)
- All FastAPI routes MUST require auth by default via `get_current_user` dependency
- Explicitly whitelist public routes
- Rate-limit login: 5 failures → 15-minute lockout

**Data Handling**
- User-submitted Python code MUST run in fully isolated sandbox (Docker container or Piston API)
- NEVER use `exec()` or `eval()` on server — this is non-negotiable
- Never log user code or AI conversations in raw production logs
- Store only necessary data: email, hashed preferences, lesson progress (no unnecessary PII)
- Build "Delete My Account" endpoint from the start

**Secrets Management**
- Local: `.env.local` for Next.js, `.env` for FastAPI (both in `.gitignore`)
- Install `detect-secrets` as pre-commit hook
- Production: Vercel env vars (frontend) + Railway/Render secret manager (backend)
- LLM-agnostic pattern: All API keys behind single `LLMProviderConfig` class
- Audit secrets quarterly. Rotate immediately if exposed.

**Rationale:** Security breaches destroy trust. Isolated sandboxes prevent code injection. Managed auth reduces attack surface. Secrets in version control are unacceptable.

### V. Architecture Patterns

**Preferred Stack**
- Frontend: Next.js + Monaco (user interface with embedded code editor)
- Backend: FastAPI + OpenAI SDK (AI-powered tutoring agents as microservices)
- Database: Neon PostgreSQL (user data, progress, code submissions)
- Auth: Better Auth (authentication framework)
- Service Mesh: Dapr (state management, pub/sub, service invocation)
- Messaging: Kafka on Kubernetes (asynchronous event-driven communication)
- API Gateway: Kong API Gateway on Kubernetes (routes traffic and handles JWT authentication)
- AI Context: MCP Servers (give AI agents real-time access to data)
- Orchestration: Kubernetes (deploy and manage all containerized services)
- Continuous Delivery: Argo CD + GitHub Actions (GitOps approach with Helm)
- Documentation: Docusaurus (auto-generated documentation site)
- Testing: pytest + Playwright + Vitest

**Design Patterns (The Three You Actually Need)**

1. **Repository Pattern** — DB access only through repos, never raw queries in routes
2. **LLM Provider Abstraction** — Protocol-based interface for swapping LLM providers via env var
3. **Prompt Template Management** — Load, version, and A/B test prompts without deployments

**Anti-Patterns (Actively Avoid)**
- Business logic inside FastAPI route handlers
- Calling LLM APIs synchronously (always stream or background)
- Hardcoding LLM provider anywhere except the factory
- Running user code outside isolated sandbox
- Skipping Alembic migrations — never alter DB schema directly
- Over-engineering early — no microservices, no message queues until users demand them
- Adding error handling for scenarios that can't happen

**Rationale:** Repository pattern keeps data access testable. LLM abstraction enables provider flexibility. Anti-patterns prevent premature complexity.

### VI. Multi-Agent Architecture Standards

**Agent Responsibilities (Strict Separation)**
- Triage Agent: Routes queries to specialist agents
- Concepts Agent: Explains Python concepts with examples
- Code Review Agent: Analyzes code for correctness, PEP 8, efficiency
- Debug Agent: Parses errors, provides progressive hints
- Exercise Agent: Generates coding challenges, auto-grades
- Progress Agent: Tracks mastery scores, provides summaries

**Agent Communication Rules**
- Agents MUST communicate via well-defined interfaces (no shared state)
- Each agent MUST have independent prompt templates
- Agent responses MUST follow consistent JSON schema
- Triage routing MUST be deterministic and testable

**Rationale:** Clear agent boundaries prevent responsibility creep. Consistent interfaces enable independent testing and evolution.

### VII. Business Logic Integrity

**Mastery Calculation (MUST NOT CHANGE without ADR)**
- Exercise completion: 40%
- Quiz scores: 30%
- Code quality ratings: 20%
- Consistency (streak): 10%

**Mastery Levels (Fixed Thresholds)**
- 0-40%: Beginner (Red)
- 41-70%: Learning (Yellow)
- 71-90%: Proficient (Green)
- 91-100%: Mastered (Blue)

**Struggle Detection Triggers**
- Same error type occurs 3+ times
- Student stuck on exercise > 10 minutes
- Quiz score < 50%
- Student explicitly says "I don't understand" or "I'm stuck"
- 5+ failed code executions in a row

**Code Execution Sandbox Constraints (MVP)**
- Timeout: 5 seconds
- Memory limit: 50MB
- No file system access (except temp directory)
- No network access
- Allowed imports: Python standard library only

**Rationale:** Business logic consistency ensures fair student assessment. Struggle detection enables timely teacher intervention. Sandbox constraints prevent abuse.

## Development Workflow

**Branching Strategy — GitHub Flow**
```
main  ←  always deployable, branch-protected
  └── feature/llm-provider-abstraction
  └── fix/streaming-timeout-on-slow-responses
  └── chore/upgrade-sqlalchemy-2
  └── experiment/gemini-integration
```
- Every change goes through a PR — even solo dev
- Review your own diff after a break
- Use `experiment/` branches for LLM provider trials

**Commit Conventions — Conventional Commits**
```
feat: add streaming AI feedback to code editor
fix: handle LLM timeout with graceful fallback message
chore: update FastAPI to 0.115 and regenerate lockfile
docs: add ADR for LLM provider abstraction pattern
test: add integration tests for lesson progress endpoint
experiment: test Claude Haiku for hint latency
```
Enforce with `commitlint`. Enables automatic changelogs.

**CI Pipeline (GitHub Actions — under 3 min)**
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

**Review Process**
- Write PR description: What changed? Why? How tested?
- Let PRs sit for a few hours before merging (async self-review)
- For AI/LLM features: manually test with 5+ real prompts before merging
- Keep PRs under 300 lines (split if larger)
- Tag PRs with `[EXPERIMENT]` for LLM provider trials

**Rationale:** GitHub Flow is simple and effective for solo dev. Conventional commits enable automation. Fast CI encourages frequent commits.

## Governance

**Constitution Authority**
- This constitution supersedes all other practices
- Amendments require documentation, approval, and migration plan
- All PRs/reviews MUST verify compliance
- Complexity MUST be justified

**Amendment Process**
1. Propose change via GitHub Issue with rationale
2. Document impact on existing code/tests
3. Update constitution with version bump (semantic versioning)
4. Update dependent templates and documentation
5. Create migration plan if breaking changes
6. Merge only after validation

**Version Semantics**
- MAJOR: Backward incompatible governance/principle removals or redefinitions
- MINOR: New principle/section added or materially expanded guidance
- PATCH: Clarifications, wording, typo fixes, non-semantic refinements

**Compliance Review**
- Quarterly review of constitution adherence
- Update constitution to reflect evolved practices
- Archive outdated principles with rationale

**Runtime Development Guidance**
- Use `CLAUDE.md` for agent-specific development guidance
- Constitution defines "what" and "why", CLAUDE.md defines "how"

**Rationale:** Living constitution evolves with project. Semantic versioning tracks governance changes. Compliance reviews prevent drift.

**Version**: 1.0.0 | **Ratified**: 2026-03-14 | **Last Amended**: 2026-03-14
