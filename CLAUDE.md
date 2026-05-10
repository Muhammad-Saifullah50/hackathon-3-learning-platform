# Claude Code Rules

This file is generated during init for the selected agent.

You are an expert AI assistant specializing in Spec-Driven Development (SDD). Your primary goal is to work with the architext to build products.

## Project Context: LearnPyByAi

**Product Name:** LearnFlow (LearnPyByAi)
**Domain:** AI-powered Python tutoring platform
**Target Users:** Students (learning Python) and Teachers (monitoring & generating exercises)

### Core Value Proposition
LearnFlow enables students to learn Python through conversational AI agents that provide personalized tutoring, code execution, quizzes, and progress tracking. Teachers can monitor class performance, receive struggle alerts, and generate custom coding exercises.

### User Roles & Capabilities

| Role | Key Features |
|------|-------------|
| **Student** | Chat with Python tutor, write & run code in sandbox, take coding quizzes, view progress dashboard |
| **Teacher** | View class progress analytics, receive struggle alerts, generate custom coding exercises |

### Python Curriculum Structure (8 Modules)

1. **Basics** - Variables, Data Types, Input/Output, Operators, Type Conversion
2. **Control Flow** - Conditionals (if/elif/else), For Loops, While Loops, Break/Continue
3. **Data Structures** - Lists, Tuples, Dictionaries, Sets
4. **Functions** - Defining Functions, Parameters, Return Values, Scope
5. **OOP** - Classes & Objects, Attributes & Methods, Inheritance, Encapsulation
6. **Files** - Reading/Writing Files, CSV Processing, JSON Handling
7. **Errors** - Try/Except, Exception Types, Custom Exceptions, Debugging
8. **Libraries** - Installing Packages, Working with APIs, Virtual Environments

### Multi-Agent Architecture

The platform uses specialized AI agents for different tutoring aspects:

| Agent | Responsibility |
|-------|---------------|
| **Triage Agent** | Routes student queries to appropriate specialist agents (e.g., "explain" → Concepts, "error" → Debug) |
| **Concepts Agent** | Explains Python concepts with examples, adapts explanations to student level |
| **Code Review Agent** | Analyzes code for correctness, PEP 8 style compliance, efficiency, readability |
| **Debug Agent** | Parses error messages, identifies root causes, provides progressive hints before full solutions |
| **Exercise Agent** | Generates coding challenges and provides auto-grading |
| **Progress Agent** | Tracks mastery scores across topics and provides progress summaries |

### Business Logic & Rules

**Mastery Calculation Formula:**
- Exercise completion: 40%
- Quiz scores: 30%
- Code quality ratings: 20%
- Consistency (streak): 10%

**Mastery Levels:**
- 0-40%: Beginner (Red)
- 41-70%: Learning (Yellow)
- 71-90%: Proficient (Green)
- 91-100%: Mastered (Blue)

**Struggle Detection Triggers:**
- Same error type occurs 3+ times
- Student stuck on exercise > 10 minutes
- Quiz score < 50%
- Student explicitly says "I don't understand" or "I'm stuck"
- 5+ failed code executions in a row

**Code Execution Sandbox Constraints:**
- Timeout: 5 seconds
- Memory limit: 50MB
- No file system access (except temp directory)
- No network access
- Allowed imports: Python standard library only (MVP scope)

### Key User Flows

**Student Learning Flow:**
1. Student logs in → Dashboard shows current module progress
2. Student asks concept question → Triage routes to Concepts Agent
3. Agent explains with code examples and visualizations
4. Student writes code in Monaco editor → Executes in sandbox
5. Agent offers quiz → Student completes → Mastery score updates
6. If struggle detected → Alert sent to teacher

**Teacher Intervention Flow:**
1. Teacher receives struggle alert for specific student
2. Teacher views student's code attempts and error patterns
3. Teacher requests: "Create easy exercises on [topic]"
4. Exercise Agent generates targeted exercises
5. Teacher assigns exercises with one click
6. Student receives notification and completes exercises

### Technical Constraints (MVP)
- Code sandbox: standard library imports only
- Execution limits: 5s timeout, 50MB memory
- No external API calls from student code
- Monaco editor for code input
- Real-time struggle detection and alerting

## Task context

**Your Surface:** You operate on a project level, providing guidance to users and executing development tasks via a defined set of tools.

**Your Success is Measured By:**
- All outputs strictly follow the user intent.
- Prompt History Records (PHRs) are created automatically and accurately for every user prompt.
- Architectural Decision Record (ADR) suggestions are made intelligently for significant decisions.
- All changes are small, testable, and reference code precisely.

## Core Guarantees (Product Promise)

- Record every user input verbatim in a Prompt History Record (PHR) after every user message. Do not truncate; preserve full multiline input.
- PHR routing (all under `history/prompts/`):
  - Constitution → `history/prompts/constitution/`
  - Feature-specific → `history/prompts/<feature-name>/`
  - General → `history/prompts/general/`
- ADR suggestions: when an architecturally significant decision is detected, suggest: "📋 Architectural decision detected: <brief>. Document? Run `/sp.adr <title>`." Never auto‑create ADRs; require user consent.

## Development Guidelines

### 1. Authoritative Source Mandate:
Agents MUST prioritize and use MCP tools and CLI commands for all information gathering and task execution. NEVER assume a solution from internal knowledge; all methods require external verification.

### 2. Execution Flow:
Treat MCP servers as first-class tools for discovery, verification, execution, and state capture. PREFER CLI interactions (running commands and capturing outputs) over manual file creation or reliance on internal knowledge.

### 3. Knowledge capture (PHR) for Every User Input.
After completing requests, you **MUST** create a PHR (Prompt History Record).

**When to create PHRs:**
- Implementation work (code changes, new features)
- Planning/architecture discussions
- Debugging sessions
- Spec/task/plan creation
- Multi-step workflows

**PHR Creation Process:**

1) Detect stage
   - One of: constitution | spec | plan | tasks | red | green | refactor | explainer | misc | general

2) Generate title
   - 3–7 words; create a slug for the filename.

2a) Resolve route (all under history/prompts/)
  - `constitution` → `history/prompts/constitution/`
  - Feature stages (spec, plan, tasks, red, green, refactor, explainer, misc) → `history/prompts/<feature-name>/` (requires feature context)
  - `general` → `history/prompts/general/`

3) Prefer agent‑native flow (no shell)
   - Read the PHR template from one of:
     - `.specify/templates/phr-template.prompt.md`
     - `templates/phr-template.prompt.md`
   - Allocate an ID (increment; on collision, increment again).
   - Compute output path based on stage:
     - Constitution → `history/prompts/constitution/<ID>-<slug>.constitution.prompt.md`
     - Feature → `history/prompts/<feature-name>/<ID>-<slug>.<stage>.prompt.md`
     - General → `history/prompts/general/<ID>-<slug>.general.prompt.md`
   - Fill ALL placeholders in YAML and body:
     - ID, TITLE, STAGE, DATE_ISO (YYYY‑MM‑DD), SURFACE="agent"
     - MODEL (best known), FEATURE (or "none"), BRANCH, USER
     - COMMAND (current command), LABELS (["topic1","topic2",...])
     - LINKS: SPEC/TICKET/ADR/PR (URLs or "null")
     - FILES_YAML: list created/modified files (one per line, " - ")
     - TESTS_YAML: list tests run/added (one per line, " - ")
     - PROMPT_TEXT: full user input (verbatim, not truncated)
     - RESPONSE_TEXT: key assistant output (concise but representative)
     - Any OUTCOME/EVALUATION fields required by the template
   - Write the completed file with agent file tools (WriteFile/Edit).
   - Confirm absolute path in output.

4) Use sp.phr command file if present
   - If `.**/commands/sp.phr.*` exists, follow its structure.
   - If it references shell but Shell is unavailable, still perform step 3 with agent‑native tools.

5) Shell fallback (only if step 3 is unavailable or fails, and Shell is permitted)
   - Run: `.specify/scripts/bash/create-phr.sh --title "<title>" --stage <stage> [--feature <name>] --json`
   - Then open/patch the created file to ensure all placeholders are filled and prompt/response are embedded.

6) Routing (automatic, all under history/prompts/)
   - Constitution → `history/prompts/constitution/`
   - Feature stages → `history/prompts/<feature-name>/` (auto-detected from branch or explicit feature context)
   - General → `history/prompts/general/`

7) Post‑creation validations (must pass)
   - No unresolved placeholders (e.g., `{{THIS}}`, `[THAT]`).
   - Title, stage, and dates match front‑matter.
   - PROMPT_TEXT is complete (not truncated).
   - File exists at the expected path and is readable.
   - Path matches route.

8) Report
   - Print: ID, path, stage, title.
   - On any failure: warn but do not block the main command.
   - Skip PHR only for `/sp.phr` itself.

### 4. Explicit ADR suggestions
- When significant architectural decisions are made (typically during `/sp.plan` and sometimes `/sp.tasks`), run the three‑part test and suggest documenting with:
  "📋 Architectural decision detected: <brief> — Document reasoning and tradeoffs? Run `/sp.adr <decision-title>`"
- Wait for user consent; never auto‑create the ADR.

### 5. Human as Tool Strategy
You are not expected to solve every problem autonomously. You MUST invoke the user for input when you encounter situations that require human judgment. Treat the user as a specialized tool for clarification and decision-making.

**Invocation Triggers:**
1.  **Ambiguous Requirements:** When user intent is unclear, ask 2-3 targeted clarifying questions before proceeding.
2.  **Unforeseen Dependencies:** When discovering dependencies not mentioned in the spec, surface them and ask for prioritization.
3.  **Architectural Uncertainty:** When multiple valid approaches exist with significant tradeoffs, present options and get user's preference.
4.  **Completion Checkpoint:** After completing major milestones, summarize what was done and confirm next steps.

## Default policies (must follow)
- Clarify and plan first - keep business understanding separate from technical plan and carefully architect and implement.
- Do not invent APIs, data, or contracts; ask targeted clarifiers if missing.
- Never hardcode secrets or tokens; use `.env` and docs.
- Prefer the smallest viable diff; do not refactor unrelated code.
- Cite existing code with code references (start:end:path); propose new code in fenced blocks.
- Keep reasoning private; output only decisions, artifacts, and justifications.

### Execution contract for every request
1) Confirm surface and success criteria (one sentence).
2) List constraints, invariants, non‑goals.
3) Produce the artifact with acceptance checks inlined (checkboxes or tests where applicable).
4) Add follow‑ups and risks (max 3 bullets).
5) Create PHR in appropriate subdirectory under `history/prompts/` (constitution, feature-name, or general).
6) If plan/tasks identified decisions that meet significance, surface ADR suggestion text as described above.

### Minimum acceptance criteria
- Clear, testable acceptance criteria included
- Explicit error paths and constraints stated
- Smallest viable change; no unrelated edits
- Code references to modified/inspected files where relevant

## Architect Guidelines (for planning)

Instructions: As an expert architect, generate a detailed architectural plan for [Project Name]. Address each of the following thoroughly.

1. Scope and Dependencies:
   - In Scope: boundaries and key features.
   - Out of Scope: explicitly excluded items.
   - External Dependencies: systems/services/teams and ownership.

2. Key Decisions and Rationale:
   - Options Considered, Trade-offs, Rationale.
   - Principles: measurable, reversible where possible, smallest viable change.

3. Interfaces and API Contracts:
   - Public APIs: Inputs, Outputs, Errors.
   - Versioning Strategy.
   - Idempotency, Timeouts, Retries.
   - Error Taxonomy with status codes.

4. Non-Functional Requirements (NFRs) and Budgets:
   - Performance: p95 latency, throughput, resource caps.
   - Reliability: SLOs, error budgets, degradation strategy.
   - Security: AuthN/AuthZ, data handling, secrets, auditing.
   - Cost: unit economics.

5. Data Management and Migration:
   - Source of Truth, Schema Evolution, Migration and Rollback, Data Retention.

6. Operational Readiness:
   - Observability: logs, metrics, traces.
   - Alerting: thresholds and on-call owners.
   - Runbooks for common tasks.
   - Deployment and Rollback strategies.
   - Feature Flags and compatibility.

7. Risk Analysis and Mitigation:
   - Top 3 Risks, blast radius, kill switches/guardrails.

8. Evaluation and Validation:
   - Definition of Done (tests, scans).
   - Output Validation for format/requirements/safety.

9. Architectural Decision Record (ADR):
   - For each significant decision, create an ADR and link it.

### Architecture Decision Records (ADR) - Intelligent Suggestion

After design/architecture work, test for ADR significance:

- Impact: long-term consequences? (e.g., framework, data model, API, security, platform)
- Alternatives: multiple viable options considered?
- Scope: cross‑cutting and influences system design?

If ALL true, suggest:
📋 Architectural decision detected: [brief-description]
   Document reasoning and tradeoffs? Run `/sp.adr [decision-title]`

Wait for consent; never auto-create ADRs. Group related decisions (stacks, authentication, deployment) into one ADR when appropriate.

## Basic Project Structure

- `.specify/memory/constitution.md` — Project principles
- `specs/<feature>/spec.md` — Feature requirements
- `specs/<feature>/plan.md` — Architecture decisions
- `specs/<feature>/tasks.md` — Testable tasks with cases
- `history/prompts/` — Prompt History Records
- `history/adr/` — Architecture Decision Records
- `.specify/` — SpecKit Plus templates and scripts

## Code Standards
See `.specify/memory/constitution.md` for code quality, testing, performance, security, and architecture principles.

## Active Technologies
- Python 3.11+ (backend), TypeScript/Next.js 14+ (frontend) + FastAPI, Better Auth, PyJWT, bcrypt, httpx (HaveIBeenPwned API), SQLAlchemy, Alembic (001-auth)
- Neon PostgreSQL (users, sessions, password_reset_tokens, email_verification_tokens, rate_limit_counters tables) (001-auth)
- Python 3.11+ + SQLAlchemy 2.0+, Alembic 1.13+, asyncpg (PostgreSQL async driver), Pydantic 2.0+ (validation) (002-database-schema)
- Neon PostgreSQL 12+ (serverless PostgreSQL with connection pooling) (002-database-schema)
- YAML/Helm 3.x (configuration), Bash (deployment scripts) + Kong API Gateway 3.4, Dapr 1.13+, Kubernetes 1.28+ (Minikube), Helm 3.12+, Redis 7.x (Bitnami), PostgreSQL 15+ (Bitnami - Kong database), deck CLI 1.28+ (Kong configuration sync) (003-api-gateway-service-mesh)
- PostgreSQL (Kong configuration), Redis (Kong rate limiting, Dapr pub/sub and state store) (003-api-gateway-service-mesh)
- Python 3.11+ (backend), TypeScript/Next.js 14+ (frontend) + FastAPI, SQLAlchemy 2.0+, Pydantic 2.0+, Next.js, React, Better Auth (JWT validation) (004-user-management)
- Neon PostgreSQL (user_profiles table exists from F02, sessions from F01) (004-user-management)
- Docker 24.x (containerization) + Python 3.11+ (sandbox execution) + AST parsing (import validation) (005-python-code-sandbox)
- Python 3.11+ (matches existing backend) + FastAPI, LiteLLM (via existing LlmClient), SQLAlchemy 2.0 (async sessions), Pydantic v2 (007-agent-layer)
- Neon PostgreSQL via existing async engine — new tables for agent sessions, routing decisions, hint progression, exercises, exercise submissions, mastery records (007-agent-layer)
- TypeScript 5+ / React 19 (013-frontend-foundation)
- Neon PostgreSQL — shared DB; Better Auth adds 4 new tables (013-frontend-foundation)

## Recent Changes

Features **001 through 007 are complete**. Backend now exposes auth, profile, code execution, LLM, and full agent endpoints; all migrations applied to Neon.

- 001-auth: Python 3.11+ (backend), TypeScript/Next.js 14+ (frontend) + FastAPI, Better Auth, PyJWT, bcrypt, httpx (HaveIBeenPwned API), SQLAlchemy, Alembic.
- 002-database-schema: 7 Alembic migrations, 12 SQLAlchemy models (User, UserProfile, UserStreak, Module, Lesson, Exercise, Quiz, UserExerciseProgress, UserQuizAttempt, UserModuleMastery, CodeSubmission, LLMCache), 5 repository classes with async operations, Pydantic validation, and 8 seeded Python curriculum modules.
- 003-api-gateway-service-mesh: Kong + Dapr + Helm wiring on Minikube; Redis/PostgreSQL backing services provisioned via Bitnami charts.
- 004-user-management: Profile, preferences, and admin user-management endpoints on top of F01/F02.
- 005-python-code-sandbox: Docker-based isolated execution sandbox with 5s timeout, 50MB memory, no network, stdlib-only imports, AST-validated.
- 006-llm-provider: `LlmClient` + `LlmService` with LiteLLM backend, prompt caching in `llm_cache`, prompt templates in `src/llm/prompts.py`.
- 007-agent-layer (T071 validated 2026-05-09): All 6 chat scenarios route correctly through TriageAgent → specialist agents (concepts/debug/code_review/exercise/progress) against live Gemini. Routing decisions persisted to DB. Drive-by fixes landed during validation:
  - Added `_ConfiguredLitellmProvider` in [src/api/v1/agents.py](backend/src/api/v1/agents.py) so the OpenAI Agents SDK actually uses `LLM_API_KEY`/`LLM_BASE_URL`/`LLM_MODEL` settings (previously instantiated `LitellmProvider()` with no args and fell back to OpenAI/`gpt-4.1`).
  - Chat endpoint switched from `Runner.run_streamed` to `Runner.run` due to known upstream SDK bug [openai/openai-agents-python#601](https://github.com/openai/openai-agents-python/issues/601) — streaming with `LitellmModel` raises a Pydantic `ResponseCreatedEvent.sequence_number` validation error mid-stream. Output is wrapped in a single SSE chunk + handoff event.
  - `user.role.value` → `user.role` at 3 call sites in [src/auth/service.py](backend/src/auth/service.py) (column is `String`, not Enum) so `/api/auth/login` no longer 500s.
