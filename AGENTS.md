# AGENTS.md

AI agent instructions for LearnFlow — an AI-powered Python tutoring platform with multi-agent architecture.

## Project Status (2026-05-09)

Features **001–007 are complete and validated end-to-end**. The backend agent layer (F07) was validated against live Gemini on 2026-05-09 (T071): all 6 quickstart chat scenarios route correctly through Triage → specialist agents and routing decisions persist to DB. See `CLAUDE.md` "Recent Changes" for the per-feature breakdown.

## Build & Development Commands

### Backend (Python 3.11+ / uv-managed venv at `backend/.venv`)
- Run server: `cd backend && .venv/bin/uvicorn src.main:app --reload`
- Apply migrations: `cd backend && uv run alembic upgrade head`
- Tests: `cd backend && uv run pytest`
- Format/lint: `cd backend && uv run black . && uv run isort .`

### Frontend (Next.js 14+)
- Dev: `npm run dev`
- Tests: `npm test`
- Lint/format: `npm run lint && npm run format`

## Code Style

### Python
- Python 3.11+
- Formatting: `black` (line length 88) + `isort` — MUST run on save + pre-commit
- Functions/variables: `snake_case`
- Classes: `PascalCase`
- LLM provider files: `provider_name.py` (e.g., `openai.py`, `claude.py`)
- All business logic functions MUST have Google-style docstrings (args, returns, raises)
- FastAPI routes MUST include `summary=` and `description=` for Swagger docs

### TypeScript/React
- TypeScript 5.0+
- Formatting: `prettier` + `eslint` with Next.js config — MUST auto-format on save
- React components: `PascalCase`
- Variables/hooks: `camelCase`
- Custom hooks: `use` prefix (e.g., `useUserProgress`)
- React components: JSDoc comment on props interface only

### General
- Database columns: `snake_case`
- Environment variables: `SCREAMING_SNAKE_CASE`
- API routes: `kebab-case` nouns (e.g., `/api/lesson-progress`)
- File names: `kebab-case` for components, `snake_case` for Python modules
- Convert any `# TODO` older than 2 weeks into a GitHub Issue immediately

## Security

### Authentication
- Use BetterAuth — NEVER build auth yourself
- Short-lived JWTs (15 min access + 7 day refresh)
- All FastAPI routes MUST require auth by default via `get_current_user` dependency
- Explicitly whitelist public routes
- Rate-limit login: 5 failures → 15-minute lockout

### Code Execution
- User-submitted Python code MUST run in fully isolated sandbox (Docker container or Piston API)
- NEVER use `exec()` or `eval()` on server — this is non-negotiable
- Sandbox constraints: 5s timeout, 50MB memory, no network, temp filesystem only, Python stdlib imports only

### Secrets Management
- Never hardcode API keys, tokens, or secrets
- Local: `.env.local` (Next.js), `.env` (FastAPI) — both in `.gitignore`
- Install `detect-secrets` as pre-commit hook
- Production: Vercel env vars (frontend) + Railway/Render secret manager (backend)
- All LLM API keys behind single `LLMProviderConfig` class

### Data Handling
- Never log user code or AI conversations in raw production logs
- Store only necessary data: email, hashed preferences, lesson progress (no unnecessary PII)
- Build "Delete My Account" endpoint from the start

## Architecture

### Directory Structure (Planned)
```
/frontend/               - Next.js 16+ App Router
  /app/                 - App Router pages
  /components/          - React components
  /lib/                 - Client utilities
  /hooks/               - Custom React hooks
/backend/               - FastAPI async application
  /api/                 - FastAPI route handlers
  /services/            - Business logic layer
  /repositories/        - Database access (Repository pattern)
  /models/              - SQLAlchemy models
  /schemas/             - Pydantic schemas
  /llm/                 - LLM provider abstraction
    /providers/         - Provider implementations (openai.py, claude.py)
    /prompts/           - Versioned prompt templates
  /sandbox/             - Code execution sandbox
/docs/                  - Documentation
  /decisions/           - Architecture Decision Records (ADRs)
/specs/                 - Feature specifications (Spec-Driven Development)
  /<feature>/           - Per-feature spec, plan, tasks
/history/               - Development history
  /prompts/             - Prompt History Records (PHRs)
  /adr/                 - ADR archive
/.specify/              - SpecKit Plus templates and scripts
  /memory/              - Project memory (constitution.md)
  /templates/           - Development templates
  /scripts/             - Automation scripts
```

### Design Patterns (The Three You Actually Need)

1. **Repository Pattern** — DB access only through repos, never raw queries in routes
2. **LLM Provider Abstraction** — Protocol-based interface for swapping LLM providers via env var
3. **Prompt Template Management** — Load, version, and A/B test prompts without deployments

### Anti-Patterns (Actively Avoid)
- Business logic inside FastAPI route handlers
- Calling LLM APIs synchronously (always stream or background)
- Hardcoding LLM provider anywhere except the factory
- Running user code outside isolated sandbox
- Skipping Alembic migrations — never alter DB schema directly
- Over-engineering early — no microservices, no message queues until users demand them
- Adding error handling for scenarios that can't happen
- Backwards-compatibility hacks (unused _vars, re-exports, // removed comments)

## Multi-Agent Architecture

### Agent Responsibilities (Strict Separation)
- **Triage Agent**: Routes student queries to appropriate specialist agents
- **Concepts Agent**: Explains Python concepts with examples, adapts to student level
- **Code Review Agent**: Analyzes code for correctness, PEP 8 style, efficiency, readability
- **Debug Agent**: Parses error messages, identifies root causes, provides progressive hints
- **Exercise Agent**: Generates coding challenges and provides auto-grading
- **Progress Agent**: Tracks mastery scores across topics and provides progress summaries

### Agent Communication Rules
- Agents MUST communicate via well-defined interfaces (no shared state)
- Each agent MUST have independent prompt templates in `/backend/llm/prompts/`
- Agent responses MUST follow consistent JSON schema
- Triage routing MUST be deterministic and testable

### Implementation Notes (F07, learned during T071 validation)

- **LLM provider wiring**: The agent layer uses the OpenAI Agents SDK with a custom `_ConfiguredLitellmProvider` in [backend/src/api/v1/agents.py](backend/src/api/v1/agents.py) that constructs `LitellmModel(model=settings.LLM_MODEL, base_url=settings.LLM_BASE_URL or None, api_key=settings.LLM_API_KEY)`. Do **not** use the bare `LitellmProvider()` from the SDK — it ignores project settings and falls back to OpenAI/`gpt-4.1`.
- **Streaming is non-streaming**: Use `await Runner.run(...)` (not `Runner.run_streamed`) and emit the final output as a single SSE chunk. `Runner.run_streamed` with `LitellmModel` is broken in the SDK — see [openai/openai-agents-python#601](https://github.com/openai/openai-agents-python/issues/601) (Pydantic `ResponseCreatedEvent.sequence_number` validation error). Revisit when that issue closes.
- **LiteLLM model identifiers**:
  - For Google AI Studio (Gemini): `LLM_MODEL=gemini/gemini-2.5-flash`, `LLM_BASE_URL=` (empty — LiteLLM picks Google's URL).
  - For an OpenAI-compatible endpoint (incl. Gemini's `/v1beta/openai/`): `LLM_MODEL=openai/<model-name>`, `LLM_BASE_URL=<full-base-url>`.
  - Do **not** mix prefixes — passing `gemini/...` with a custom `api_base` triggers `Vertex_ai_betaException` because LiteLLM appends the wrong path.

## Testing

### Coverage Targets
- FastAPI routes: 80% (prioritize auth, progress tracking, lesson delivery)
- LLM adapter layer: 70% (prompt builders, response parsers)
- Database repositories: 85% (data integrity is sacred)
- React components: 65% (user interaction flows, not rendering)
- E2E flows: 5 critical journeys minimum

### Test Types (Execution Order)
1. **Unit** — Pure functions, prompt builders, utilities (`pytest` + `vitest`)
2. **Integration** — FastAPI routes against real test DB (`pytest` + `httpx` async client)
3. **Component** — React with `@testing-library/react`, focus on user events
4. **E2E** — `Playwright` for 5 critical journeys only
5. **LLM contract tests** — Assert response shape (has `explanation`, `code_snippet`), never content

### TDD Approach
- **Strict TDD (ALWAYS)**: Auth flows, billing/progress logic, code sandbox execution
- **Test-after (acceptable)**: UI components, prompt engineering, experimental features
- **Non-negotiable rule**: Every bug fix MUST start with a failing test that reproduces the bug

## Performance

### Latency Budgets (P95)
- Next.js page load (SSR): < 800ms (hard limit: 2s)
- FastAPI response (non-AI): < 150ms (hard limit: 400ms)
- AI first token (streaming): < 1.2s
- AI full response: 30s timeout
- Python code execution: < 3s (hard limit: 8s)
- PostgreSQL query: < 40ms (hard limit: 150ms)

### Resource Limits
- LLM calls: cap input at 1,200 tokens, output at 600 tokens for feedback/hints
- Rate limit AI endpoints: 10 req/min per user via `slowapi` on FastAPI
- Code sandbox: 128MB RAM, 5s CPU, zero network access, temp filesystem only
- Bundle size: Next.js initial JS under 200KB gzipped

### Optimization Rules
- Cache identical LLM prompt+lesson combinations in PostgreSQL (`llm_cache` table with hash key)
- Stream all AI responses using FastAPI `StreamingResponse` + Next.js `ReadableStream`
- Add DB indexes on `user_id`, `lesson_id`, `created_at` from day one
- Run `EXPLAIN ANALYZE` before any new query goes to production
- Use Next.js `<Image>` for all images, `next/dynamic` for heavy components (Monaco editor)
- Profile before optimizing — add `time.perf_counter()` logs around suspected bottlenecks first

## Business Logic (MUST NOT CHANGE without ADR)

### Mastery Calculation Formula
- Exercise completion: 40%
- Quiz scores: 30%
- Code quality ratings: 20%
- Consistency (streak): 10%

### Mastery Levels (Fixed Thresholds)
- 0-40%: Beginner (Red)
- 41-70%: Learning (Yellow)
- 71-90%: Proficient (Green)
- 91-100%: Mastered (Blue)

### Struggle Detection Triggers
- Same error type occurs 3+ times
- Student stuck on exercise > 10 minutes
- Quiz score < 50%
- Student explicitly says "I don't understand" or "I'm stuck"
- 5+ failed code executions in a row

## Git & PR Conventions

### Branching Strategy — GitHub Flow
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

### Commit Conventions — Conventional Commits
```
feat: add streaming AI feedback to code editor
fix: handle LLM timeout with graceful fallback message
chore: update FastAPI to 0.115 and regenerate lockfile
docs: add ADR for LLM provider abstraction pattern
test: add integration tests for lesson progress endpoint
experiment: test Claude Haiku for hint latency
```
Enforce with `commitlint`. Enables automatic changelogs.

### Review Process
- Write PR description: What changed? Why? How tested?
- Let PRs sit for a few hours before merging (async self-review)
- For AI/LLM features: manually test with 5+ real prompts before merging
- Keep PRs under 300 lines (split if larger)
- Tag PRs with `[EXPERIMENT]` for LLM provider trials

## Spec-Driven Development (SDD)

### Workflow
This project follows Spec-Driven Development with Prompt History Records (PHRs) and Architecture Decision Records (ADRs).

### Key Artifacts
- **Constitution** (`.specify/memory/constitution.md`) — Project principles and standards
- **Feature Specs** (`specs/<feature>/spec.md`) — Feature requirements
- **Implementation Plans** (`specs/<feature>/plan.md`) — Architecture decisions
- **Task Lists** (`specs/<feature>/tasks.md`) — Testable tasks with acceptance criteria
- **PHRs** (`history/prompts/`) — Record of all development prompts and decisions
- **ADRs** (`history/adr/`) — Architecture Decision Records for significant decisions

### PHR Creation (MANDATORY)
After every user prompt that involves implementation, planning, debugging, or spec work:
1. Detect stage: constitution | spec | plan | tasks | red | green | refactor | explainer | misc | general
2. Generate title (3-7 words) and slug
3. Route to appropriate directory under `history/prompts/`
4. Fill template from `.specify/templates/phr-template.prompt.md`
5. Include full user prompt (verbatim) and assistant response summary

### ADR Suggestions
When architecturally significant decisions are made (typically during planning):
- Test: Impact (long-term)? Alternatives considered? Cross-cutting scope?
- If ALL true, suggest: "📋 Architectural decision detected: [brief]. Document? Run `/sp.adr [title]`"
- Wait for user consent; never auto-create ADRs

## Development Principles

### Clarify and Plan First
- Keep business understanding separate from technical plan
- Carefully architect before implementing
- Do not invent APIs, data, or contracts; ask targeted clarifiers if missing

### Smallest Viable Change
- Prefer the smallest viable diff
- Do not refactor unrelated code
- Cite existing code with references (start:end:path)
- Propose new code in fenced blocks

### Human as Tool Strategy
Invoke the user for input when encountering:
1. **Ambiguous Requirements** — Ask 2-3 targeted clarifying questions
2. **Unforeseen Dependencies** — Surface them and ask for prioritization
3. **Architectural Uncertainty** — Present options with tradeoffs
4. **Completion Checkpoint** — Summarize work and confirm next steps

## Tech Stack

### Technology Summary

| Layer | Technology | Purpose |
|-------|------------|---------|
| AI Coding Agents | Claude Code, Goose (Claude Code Router) | Execute Skills to build the application |
| Frontend | Next.js + Monaco | User interface with embedded code editor |
| Backend | FastAPI + OpenAI SDK | AI-powered tutoring agents as microservices |
| Auth | Better Auth | Authentication framework |
| Service Mesh | Dapr | State management, pub/sub, service invocation |
| Messaging | Kafka on Kubernetes | Asynchronous event-driven communication |
| Database | Neon PostgreSQL | User data, progress, code submissions |
| API Gateway | Kong API Gateway on Kubernetes | Routes traffic and handles JWT authentication |
| AI Context | MCP Servers | Give AI agents real-time access to data |
| Orchestration | Kubernetes | Deploy and manage all containerized services |
| Continuous Delivery | Argo CD + GitHub Actions | GitOps approach with Helm |
| Documentation | Docusaurus | Auto-generated documentation site |
| Testing | pytest + Playwright + Vitest | Comprehensive test coverage |

## Documentation

### Required Documentation
- All Python functions with business logic MUST have Google-style docstrings
- FastAPI routes MUST fill `summary=` and `description=` fields
- Maintain `/docs/decisions/` folder with lightweight ADRs for major architectural decisions
- Update AGENTS.md when architecture or conventions change

### Constitution Authority
- `CLAUDE.md` and `.specify/memory/constitution.md` supersede all other practices
- Amendments require documentation, approval, and migration plan
- All PRs/reviews MUST verify compliance
- Complexity MUST be justified

---

**Generated**: 2026-03-14 | **Project**: LearnFlow (LearnPyByAi) | **Standard**: AAIF (Agentic AI Foundation)
