# LearnFlow Feature Breakdown

This document breaks down the LearnFlow platform into isolated, buildable features following SpecKit Plus methodology. Each feature can be developed independently with clear boundaries and dependencies.

---

## Core Product Philosophy: Dynamic Content Generation

**All curriculum content is AI-generated on demand — there is no pre-authored lesson library.**

The 8 Python modules (Basics, Control Flow, Data Structures, Functions, OOP, Files, Errors, Libraries) serve as a **navigation and progress framework only** — they define what topics exist and anchor the dashboard's progress tracking. They are not a content library.

| Student Action | What Happens |
|---------------|--------------|
| Asks "explain for loops" | Concepts Agent generates an explanation tailored to the student's mastery level |
| Requests practice | Exercise Agent generates a coding challenge calibrated to current mastery |
| Takes a quiz | Exercise Agent generates quiz questions; student works through them in flashcard-style UI |
| Completes exercise | Score feeds mastery formula (40% exercises, 30% quizzes, 20% code quality, 10% streak) |

See **ADR-0001** (`history/adr/0001-ai-generated-dynamic-content-over-pre-authored-curriculum.md`) for the full rationale and tradeoffs.

---

## Demo Scenario

This scenario demonstrates the end-to-end learning flow:

1. Student **Maya** logs in → Dashboard shows: "Module 2: Loops — 60% complete"
2. Maya asks: "How do for loops work in Python?"
3. **Concepts Agent** generates an explanation with code examples adapted to Maya's level
4. Maya writes a for loop in the Monaco editor, runs it successfully
5. Agent offers a quiz → Maya gets 4/5 → Mastery updates to 68%
6. Student **James** struggles with list comprehensions → Gets 3 wrong answers
7. Struggle alert sent to teacher **Mr. Rodriguez**
8. Teacher views James's code attempts, types: "Create easy exercises on list comprehensions"
9. **Exercise Agent** generates targeted exercises → Teacher assigns with one click
10. James receives notification → Completes exercises → Confidence restored

---

## Feature Dependency Graph

```
Foundation Layer (Build First)
├── F01: Authentication & Authorization
├── F02: Database Schema & Migrations
└── F03: API Gateway & Service Mesh Setup

Core Infrastructure (Build Second)
├── F04: User Management
├── F05: Python Code Sandbox
└── F06: LLM Provider Abstraction Layer

Agent Layer (Build Third)
├── F07: Triage Agent
├── F08: Concepts Agent
├── F09: Code Review Agent
├── F10: Debug Agent
├── F11: Exercise Agent
└── F12: Progress Agent

Student Features (Build Fourth)
├── F13: Student Dashboard
├── F14: Interactive Code Editor
├── F15: Chat Interface with AI Tutor
├── F16: Quiz System
└── F17: Progress Tracking

Teacher Features (Build Fifth)
├── F18: Teacher Dashboard
├── F19: Class Analytics
├── F20: Struggle Alert System
└── F21: Exercise Generator

Advanced Features (Build Last)
├── F22: Real-time Notifications
├── F23: Curriculum Management
└── F24: Admin Panel
```

---

## Feature Specifications

### **F01: Authentication & Authorization**
**Priority:** P0 (Foundation)
**Dependencies:** None
**Estimated Complexity:** Medium

**Description:**
Implement secure authentication using Better Auth with JWT tokens, role-based access control (Student/Teacher/Admin), and session management.

**Acceptance Criteria:**
- [ ] User registration with email/password
- [ ] Login with JWT (15min access + 7day refresh)
- [ ] Role-based middleware (Student/Teacher/Admin)
- [ ] Rate limiting (5 failures → 15min lockout)
- [ ] Password reset flow
- [ ] Logout and token revocation

**Tech Stack:**
- Better Auth (Next.js)
- FastAPI JWT dependencies
- PostgreSQL (user credentials)

**API Endpoints:**
- `POST /api/auth/register`
- `POST /api/auth/login`
- `POST /api/auth/refresh`
- `POST /api/auth/logout`
- `POST /api/auth/reset-password`

---

### **F02: Database Schema & Migrations**
**Priority:** P0 (Foundation)
**Dependencies:** None
**Estimated Complexity:** Medium

**Description:**
Design and implement the complete PostgreSQL schema for users, modules (topic scaffold only), progress, AI-generated exercises/quizzes (stored after generation for history), and LLM cache.

> **Note (ADR-0001):** The `Lesson` table stores topic labels and module structure only — no pre-authored content. The `Exercise` and `Quiz` tables store AI-generated content *after* it is produced at runtime, for grading history and teacher review. Content is never pre-authored.

**Acceptance Criteria:**
- [ ] Alembic migration setup
- [ ] Users table (id, email, role, created_at)
- [ ] Modules table (id, name, topic_labels) — navigation scaffold only, no lesson prose
- [ ] Progress table (user_id, module_id, mastery_score, streak)
- [ ] Exercises table (user_id, generated_content, score, timestamp) — stores generated exercises post-creation
- [ ] Code submissions table (user_id, code, result, timestamp)
- [ ] LLM cache table (prompt_hash, response, created_at)
- [ ] Indexes on user_id, module_id, created_at
- [ ] Foreign key constraints

**Tech Stack:**
- Neon PostgreSQL
- Alembic (migrations)
- SQLAlchemy (ORM)

---

### **F03: API Gateway & Service Mesh Setup**
**Priority:** P0 (Foundation)
**Dependencies:** None
**Estimated Complexity:** High

**Description:**
Set up Kong API Gateway on Kubernetes for routing, JWT authentication, and rate limiting. Configure Dapr for service-to-service communication.

**Acceptance Criteria:**
- [ ] Kong deployed on Kubernetes
- [ ] JWT plugin configured
- [ ] Rate limiting rules (10 req/min per user)
- [ ] Dapr sidecars for FastAPI services
- [ ] Service discovery configured
- [ ] Health check endpoints

**Tech Stack:**
- Kong API Gateway
- Dapr (state management, pub/sub)
- Kubernetes
- Helm charts

---

### **F04: User Management**
**Priority:** P0 (Foundation)
**Dependencies:** F01, F02
**Estimated Complexity:** Low

**Description:**
CRUD operations for user profiles, preferences, and account management.

**Acceptance Criteria:**
- [ ] Get user profile
- [ ] Update user preferences (theme, notifications)
- [ ] Delete account (GDPR compliance)
- [ ] List users (admin only)
- [ ] Repository pattern implementation

**Tech Stack:**
- FastAPI
- SQLAlchemy
- PostgreSQL

**API Endpoints:**
- `GET /api/users/me`
- `PATCH /api/users/me`
- `DELETE /api/users/me`
- `GET /api/users` (admin)

---

### **F05: Python Code Sandbox**
**Priority:** P0 (Core Infrastructure)
**Dependencies:** F02
**Estimated Complexity:** High

**Description:**
Isolated Python code execution environment with strict resource limits and security constraints.

**Acceptance Criteria:**
- [ ] Docker-based sandbox (or Piston API integration)
- [ ] 5s timeout enforcement
- [ ] 50MB memory limit
- [ ] Standard library imports only
- [ ] No network/filesystem access
- [ ] Capture stdout, stderr, execution time
- [ ] Error message parsing

**Tech Stack:**
- Docker (isolated containers)
- FastAPI (execution API)
- Python 3.11

**API Endpoints:**
- `POST /api/sandbox/execute`

**Security Constraints:**
- NEVER use `exec()` or `eval()`
- Whitelist allowed imports
- Kill process after timeout

---

### **F06: LLM Provider Abstraction Layer**
**Priority:** P0 (Core Infrastructure)
**Dependencies:** F02
**Estimated Complexity:** Medium

**Description:**
Protocol-based interface for swapping LLM providers (OpenAI, Claude, Gemini) via environment variables with prompt template management.

**Acceptance Criteria:**
- [ ] `LLMProvider` protocol interface
- [ ] OpenAI implementation
- [ ] Claude implementation (optional)
- [ ] Prompt template loader (YAML/JSON)
- [ ] Response streaming support
- [ ] LLM cache integration (PostgreSQL)
- [ ] Token counting and rate limiting

**Tech Stack:**
- OpenAI SDK
- FastAPI StreamingResponse
- PostgreSQL (cache)

**Design Pattern:**
```python
class LLMProvider(Protocol):
    async def generate(self, prompt: str, max_tokens: int) -> AsyncIterator[str]:
        ...
```

---

### **F07: Triage Agent**
**Priority:** P1 (Agent Layer)
**Dependencies:** F06
**Estimated Complexity:** Medium

**Description:**
Routes student queries to appropriate specialist agents based on intent classification.

**Acceptance Criteria:**
- [ ] Intent classification (explain, debug, review, exercise, progress)
- [ ] Routing logic with confidence scores
- [ ] Fallback to general agent
- [ ] Logging and analytics
- [ ] Unit tests for routing rules

**Tech Stack:**
- FastAPI
- LLM Provider (classification)
- OpenAI Agents SDK

**Routing Rules:**
- "explain", "what is" → Concepts Agent
- "error", "bug", "fix" → Debug Agent
- "review my code" → Code Review Agent
- "quiz", "exercise" → Exercise Agent
- "progress", "how am I doing" → Progress Agent

---

### **F08: Concepts Agent**
**Priority:** P1 (Agent Layer)
**Dependencies:** F06, F07
**Estimated Complexity:** Medium

**Description:**
Generates Python concept explanations on demand, adapting to the student's mastery level and session context. All content is AI-generated at request time — no pre-authored lessons are retrieved.

**Acceptance Criteria:**
- [ ] Generates concept explanation with code examples on demand
- [ ] Adapts explanation depth to student mastery level (beginner/intermediate/advanced)
- [ ] Includes visual aids where helpful (ASCII diagrams, tables)
- [ ] Suggests follow-up questions the student might want to explore
- [ ] Streams response tokens progressively

**Tech Stack:**
- FastAPI
- LLM Provider
- Prompt templates

**API Endpoints:**
- `POST /api/agents/concepts/explain`

---

### **F09: Code Review Agent**
**Priority:** P1 (Agent Layer)
**Dependencies:** F06, F07
**Estimated Complexity:** Medium

**Description:**
Analyzes student code for correctness, PEP 8 compliance, efficiency, and readability.

**Acceptance Criteria:**
- [ ] PEP 8 style checking
- [ ] Logic correctness analysis
- [ ] Performance suggestions
- [ ] Readability improvements
- [ ] Positive reinforcement for good code

**Tech Stack:**
- FastAPI
- LLM Provider
- `black`, `pylint` (static analysis)

**API Endpoints:**
- `POST /api/agents/code-review/analyze`

---

### **F10: Debug Agent**
**Priority:** P1 (Agent Layer)
**Dependencies:** F05, F06, F07
**Estimated Complexity:** High

**Description:**
Parses error messages, identifies root causes, provides progressive hints before full solutions.

**Acceptance Criteria:**
- [ ] Error message parsing (SyntaxError, TypeError, etc.)
- [ ] Root cause identification
- [ ] Progressive hint system (3 levels)
- [ ] Solution only after hints exhausted
- [ ] Common error pattern detection

**Tech Stack:**
- FastAPI
- LLM Provider
- Python AST parsing

**API Endpoints:**
- `POST /api/agents/debug/analyze`

---

### **F11: Exercise Agent**
**Priority:** P1 (Agent Layer)
**Dependencies:** F05, F06, F07
**Estimated Complexity:** High

**Description:**
Generates coding challenges and quizzes on demand, calibrated to the student's current module and mastery level. Provides auto-grading and feedback. Generated content is stored in the database after creation for history and teacher review — not pre-authored.

**Acceptance Criteria:**
- [ ] Generates exercise on demand by topic and student mastery level
- [ ] Generates test cases alongside the exercise
- [ ] Auto-grades student submissions with feedback
- [ ] Supports partial credit scoring
- [ ] Stores generated exercise + student result in database post-generation
- [ ] Generates quiz questions in flashcard format for the Quiz System (F16)

**Tech Stack:**
- FastAPI
- LLM Provider
- Python sandbox (F05)

**API Endpoints:**
- `POST /api/agents/exercise/generate`
- `POST /api/agents/exercise/grade`

---

### **F12: Progress Agent**
**Priority:** P1 (Agent Layer)
**Dependencies:** F02, F06, F07
**Estimated Complexity:** Medium

**Description:**
Tracks mastery scores across topics and provides progress summaries.

**Acceptance Criteria:**
- [ ] Mastery score calculation (40% exercises, 30% quizzes, 20% code quality, 10% streak)
- [ ] Progress summary generation
- [ ] Weak area identification
- [ ] Recommendation engine
- [ ] Streak tracking

**Tech Stack:**
- FastAPI
- PostgreSQL
- LLM Provider (summaries)

**API Endpoints:**
- `GET /api/agents/progress/summary`
- `GET /api/agents/progress/recommendations`

---


### **F13: Student Dashboard**
**Priority:** P2 (Student Features)
**Dependencies:** F01, F04, F12
**Estimated Complexity:** Medium

**Description:**
Student landing page showing current module progress, recent activity, and quick actions.

**Acceptance Criteria:**
- [ ] Module progress cards (8 modules)
- [ ] Mastery level indicators (color-coded)
- [ ] Recent code submissions
- [ ] Streak counter
- [ ] Quick action buttons (Start Lesson, Take Quiz)

**Tech Stack:**
- Next.js (SSR)
- Tailwind CSS
- React Query

**Pages:**
- `/dashboard`

---

### **F14: Interactive Code Editor**
**Priority:** P2 (Student Features)
**Dependencies:** F05
**Estimated Complexity:** High

**Description:**
Monaco editor integration with Python syntax highlighting, code execution, and real-time feedback.

**Acceptance Criteria:**
- [ ] Monaco editor with Python mode
- [ ] Syntax highlighting
- [ ] Execute button with loading state
- [ ] Output display (stdout, stderr)
- [ ] Execution time display
- [ ] Error highlighting
- [ ] Code persistence (auto-save)

**Tech Stack:**
- Next.js
- Monaco Editor
- React

**Components:**
- `<CodeEditor />`
- `<ExecutionOutput />`

---

### **F15: Chat Interface with AI Tutor**
**Priority:** P2 (Student Features)
**Dependencies:** F07, F08, F09, F10, F14
**Estimated Complexity:** High

**Description:**
Two-surface chat interface: a standalone `/chat` page for general Python learning conversation, and a collapsible panel embedded in the code editor (F14). Every message routes through the Triage Agent (F07) which hands off to the appropriate specialist — Concepts, Debug, Exercise, Code Review, or Progress. Responses stream token-by-token. Chat history is persisted to the database. Guardrails keep conversations focused on Python learning.

**Acceptance Criteria:**
- [ ] Standalone `/chat` page — general Python assistant, no required lesson context
- [ ] Collapsible chat panel embedded in the F14 code editor
- [ ] Every message routed through Triage Agent → specialist agent (transparent to student)
- [ ] Responses streamed token-by-token (backend SSE fixed as part of this feature)
- [ ] Code blocks in responses rendered with Python syntax highlighting
- [ ] Typing indicator while AI generates response
- [ ] Last 5 messages sent as conversation history context
- [ ] Embedded panel auto-attaches current code (up to 4 KB) + last execution output as context
- [ ] Student's current module, lesson, and mastery level included as context
- [ ] Off-topic (non-Python) messages redirected with a polite guardrail response
- [ ] Chat history persisted to database; restored on page reload
- [ ] 2000-character input limit with visible counter

**Tech Stack:**
- Next.js
- Server-Sent Events (SSE) with true token streaming
- React

**Pages:**
- `/chat`

**Spec:** `specs/015-ai-tutor-chat/spec.md`

---

### **F16: Quiz System**
**Priority:** P2 (Student Features)
**Dependencies:** F02, F11
**Estimated Complexity:** Medium

**Description:**
Interactive quiz experience surfaced as a flashcard-style UI. Quiz questions are AI-generated on demand by the Exercise Agent (F11), calibrated to the student's current module and mastery level. Students work through cards sequentially; results feed the mastery calculation.

**Acceptance Criteria:**
- [ ] Flashcard-style UI — one question per card, student advances through the deck
- [ ] AI-generated quiz questions (fetched from Exercise Agent, not a pre-authored bank)
- [ ] Code input for coding questions; multiple choice for concept questions
- [ ] Auto-grading with immediate per-card feedback
- [ ] Score summary at end of quiz
- [ ] Mastery score updated based on quiz result
- [ ] Quiz history stored (generated questions + student answers + score)

**Tech Stack:**
- Next.js
- FastAPI
- PostgreSQL

**Pages:**
- `/quiz/:lessonId`

---

### **F17: Progress Tracking**
**Priority:** P2 (Student Features)
**Dependencies:** F12, F13
**Estimated Complexity:** Low

**Description:**
Visual progress tracking with charts, mastery levels, and recommendations.

**Acceptance Criteria:**
- [ ] Progress charts (line/bar)
- [ ] Mastery level breakdown
- [ ] Weak area highlights
- [ ] Recommendations display
- [ ] Historical data view

**Tech Stack:**
- Next.js
- Chart.js / Recharts
- React Query

**Pages:**
- `/progress`

---

### **F18: Teacher Dashboard**
**Priority:** P3 (Teacher Features)
**Dependencies:** F01, F04
**Estimated Complexity:** Medium

**Description:**
Teacher landing page showing class overview, recent alerts, and quick actions.

**Acceptance Criteria:**
- [ ] Class roster
- [ ] Average mastery scores
- [ ] Recent struggle alerts
- [ ] Quick action buttons (View Analytics, Generate Exercise)

**Tech Stack:**
- Next.js
- Tailwind CSS
- React Query

**Pages:**
- `/teacher/dashboard`

---

### **F19: Class Analytics**
**Priority:** P3 (Teacher Features)
**Dependencies:** F12, F18
**Estimated Complexity:** High

**Description:**
Detailed analytics on class performance, individual student progress, and topic mastery.

**Acceptance Criteria:**
- [ ] Class-wide mastery distribution
- [ ] Individual student drill-down
- [ ] Topic-wise performance
- [ ] Struggle pattern analysis
- [ ] Export to CSV

**Tech Stack:**
- Next.js
- Chart.js / Recharts
- FastAPI (analytics API)

**Pages:**
- `/teacher/dashboard`

---

### **F20: Struggle Alert System**
**Priority:** P3 (Teacher Features)
**Dependencies:** F10, F18
**Estimated Complexity:** Medium

**Description:**
Real-time alerts to teachers when students struggle, with context and intervention suggestions.

**Acceptance Criteria:**
- [ ] Struggle detection triggers (3+ same errors, 10min stuck, quiz < 50%, 5+ failed executions)
- [ ] Alert notification (in-app)
- [ ] Student context (code attempts, error patterns)
- [ ] Intervention suggestions
- [ ] Alert history

**Tech Stack:**
- FastAPI
- Kafka (event streaming)
- PostgreSQL

**API Endpoints:**
- `GET /api/teacher/alerts`
- `POST /api/teacher/alerts/:id/acknowledge`

---

### **F21: Exercise Generator**
**Priority:** P3 (Teacher Features)
**Dependencies:** F11, F18
**Estimated Complexity:** Medium

**Description:**
Teacher interface to generate custom coding exercises with AI assistance.

**Acceptance Criteria:**
- [ ] Topic selection
- [ ] Difficulty level selection
- [ ] Exercise preview
- [ ] Test case editing
- [ ] Assign to students
- [ ] Exercise library

**Tech Stack:**
- Next.js
- FastAPI
- LLM Provider

**Pages:**
- `/teacher/exercises/generate`
- `/teacher/exercises/library`

---

### **F22: Real-time Notifications**
**Priority:** P4 (Advanced)
**Dependencies:** F20
**Estimated Complexity:** Medium

**Description:**
WebSocket-based real-time notifications for struggle alerts, quiz completions, and system messages.

**Acceptance Criteria:**
- [ ] WebSocket connection management
- [ ] Notification toast UI
- [ ] Notification history
- [ ] Mark as read
- [ ] Notification preferences

**Tech Stack:**
- FastAPI WebSockets
- Next.js
- Redis (pub/sub)

---

## Development Sequence Recommendation

### Phase 1: Foundation (Weeks 1-2)
Build F01, F02, F03, F04 in parallel. These are prerequisites for everything else.

### Phase 2: Core Infrastructure (Weeks 3-4)
Build F05, F06. These enable agent development.

### Phase 3: Agent Layer (Weeks 5-7)
Build F07 first, then F08-F12 in parallel (each agent is independent).

### Phase 4: Student MVP (Weeks 8-10)
Build F13, F14, F15, F16, F17. This delivers core student value.

### Phase 5: Teacher Features (Weeks 11-12)
Build F18, F19, F20, F21. This completes the teacher experience.

### Phase 6: Advanced Features (Weeks 13-14)
Build F22, F23, F24 as polish and admin capabilities.

---

## SpecKit Plus Workflow for Each Feature

For each feature, follow this workflow:

1. **Specify:** Run `/sp.specify <feature-name>` to create `specs/<feature-name>/spec.md`
2. **Plan:** Run `/sp.plan <feature-name>` to create `specs/<feature-name>/plan.md`
3. **Tasks:** Run `/sp.tasks <feature-name>` to create `specs/<feature-name>/tasks.md`
4. **Implement:** Run `/sp.implement <feature-name>` to execute tasks
5. **Review:** Run `/sp.analyze <feature-name>` for consistency checks
6. **Commit:** Run `/sp.git.commit_pr <feature-name>` to create PR

---

## Notes

- Each feature is designed to be independently testable
- Dependencies are explicitly listed to enable parallel development
- Complexity estimates help with sprint planning
- All features follow the constitution principles (see `.specify/memory/constitution.md`)
- Use PHRs to track all development decisions
- Create ADRs for significant architectural choices

**Last Updated:** 2026-03-14
