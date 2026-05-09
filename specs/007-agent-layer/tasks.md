---

description: "Task list for AI Agent Layer (F07-F12) implementation"
---

# Tasks: AI Agent Layer (F07-F12)

**Input**: Design documents from `/specs/007-agent-layer/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/agent-api.yaml, quickstart.md

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `backend/src/`, `backend/tests/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create directory structure and package files for the agent layer

- [x] T001 Create `backend/src/services/agents/` directory with `__init__.py`
- [x] T002 Create `backend/src/models/agent_session.py` and `backend/src/models/agent_exercise.py` (empty, with module docstrings)
- [x] T003 [P] Create `backend/src/schemas/agents.py` (empty, with module docstrings)
- [x] T004 [P] Create `backend/src/repositories/agent_session_repository.py`, `routing_repository.py`, `exercise_repository.py`, `mastery_repository.py` (empty, with module docstrings)
- [x] T005 [P] Create `backend/src/api/v1/agents.py` (empty router with `__init__.py` imports)
- [x] T006 [P] Create test files: `backend/tests/unit/test_triage_routing.py`, `test_concepts_agent.py`, `test_debug_agent.py`, `test_exercise_agent.py`, `test_progress_agent.py`, `test_agent_schemas.py`
- [x] T007 [P] Create test files: `backend/tests/integration/test_agent_routes.py`, `backend/tests/contract/test_agent_api.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**CRITICAL**: No user story work can begin until this phase is complete

- [x] T008 [P] Define `AgentSession`, `RoutingDecision`, `HintProgression` SQLAlchemy models in `backend/src/models/agent_session.py` with all columns, constraints, relationships, and indexes per data-model.md
- [x] T009 [P] Define `Exercise`, `ExerciseSubmission`, `MasteryRecord` SQLAlchemy models in `backend/src/models/agent_exercise.py` with all columns, constraints, relationships, and indexes per data-model.md
- [x] T010 Export all new models from `backend/src/models/__init__.py`
- [x] T011 [P] Define Pydantic schemas in `backend/src/schemas/agents.py`: `AgentChatRequest`, `AgentChatResponse`, `ExerciseGenerationRequest`, `ExerciseResponse`, `ExerciseSubmissionRequest`, `ExerciseSubmissionResponse`, `ProgressSummaryResponse`, `HintAdvanceRequest`, `HintResponse`, `AgentSessionResponse`, `TestCase`, `TestResult`, `TopicMastery`, `StreakInfo`, `ConversationMessage`, `RoutingDecisionRecord`, `AgentErrorResponse`
- [x] T012 Create Alembic migration `backend/alembic/versions/20260403_xxxx_create_agent_tables.py` for all 6 new tables with indexes and constraints
- [x] T013 [P] Implement `AgentSessionRepository` in `backend/src/repositories/agent_session_repository.py` with methods: `create_session()`, `get_session()`, `update_session()`, `add_message_to_history()`, `get_user_sessions()`
- [x] T014 [P] Implement `RoutingRepository` in `backend/src/repositories/routing_repository.py` with methods: `log_routing_decision()`, `get_session_routing_decisions()`, `get_routing_stats()`
- [x] T015 [P] Implement `ExerciseRepository` in `backend/src/repositories/exercise_repository.py` with methods: `create_exercise()`, `get_exercise()`, `list_exercises()`, `update_exercise()`
- [x] T016 [P] Implement `MasteryRepository` in `backend/src/repositories/mastery_repository.py` with methods: `get_or_create_mastery()`, `update_mastery()`, `get_user_mastery_records()`, `get_mastery_by_topic()`
- [x] T017 Enhance agent system prompts in `backend/src/llm/prompts.py`: expand `get_concept_agent_prompt()`, `get_code_review_agent_prompt()`, `get_debug_agent_prompt()`, `get_exercise_agent_prompt()`, `get_triage_agent_prompt()`, `get_progress_agent_prompt()` with detailed instructions per spec requirements
- [x] T018 Implement `BaseAgent` abstract class in `backend/src/services/agents/base.py` with protocol: `handle()`, `build_system_prompt()`, `stream_response()` methods, shared LlmClient/LlmService injection, and conversation history management
- [x] T019 Register agent router in `backend/src/api/__init__.py` and `backend/src/main.py` (include v1/agents router under `/api/v1/agents`)
- [x] T020 Run `alembic upgrade head` and verify all 6 tables created with correct schema

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Student Asks a Question and Gets Routed to the Right Agent (Priority: P1)

**Goal**: Student sends a natural language question, system classifies intent, routes to the appropriate specialist agent, and returns a response. This is the core user-facing flow.

**Independent Test**: Send sample questions of each intent type and verify the correct agent responds with appropriate content.

### Tests for User Story 1

- [x] T021 [P] [US1] Unit tests for deterministic triage routing in `backend/tests/unit/test_triage_routing.py`: test all 5 intent categories + fallback, verify confidence scoring, test 20+ representative queries
- [x] T022 [P] [US1] Integration test for `/api/v1/agents/chat` endpoint in `backend/tests/integration/test_agent_routes.py`: test authenticated request, session creation, streaming response, error handling
- [x] T023 [P] [US1] Schema tests in `backend/tests/unit/test_agent_schemas.py`: validate all request/response schemas, edge cases, validation errors

### Implementation for User Story 1

- [x] T024 [US1] Implement `TriageAgent` service in `backend/src/services/agents/triage.py`: deterministic keyword/regex-based intent classification with confidence scoring for 5 categories (concept-explanation, code-debug, code-review, exercise-generation, progress-summary) + fallback to "general"
- [x] T025 [US1] Implement intent keyword/regex patterns in `backend/src/services/agents/triage.py`: pattern sets for each intent category, confidence calculation based on match count and specificity, minimum confidence threshold for routing
- [x] T026 [US1] Implement `ConceptsAgent` service stub in `backend/src/services/agents/concepts.py`: basic `handle()` method that calls LlmService with concept agent system prompt and student message, returns streaming response
- [x] T027 [US1] Implement `DebugAgent` service stub in `backend/src/services/agents/debug.py`: basic `handle()` method that calls LlmService with debug agent system prompt, student message, and code snippet
- [x] T028 [US1] Implement `CodeReviewAgent` service stub in `backend/src/services/agents/code_review.py`: basic `handle()` method that calls LlmService with code review system prompt and submitted code
- [x] T029 [US1] Implement `ExerciseAgent` service stub in `backend/src/services/agents/exercise.py`: basic `handle()` method that calls LlmService with exercise agent system prompt
- [x] T030 [US1] Implement `ProgressAgent` service stub in `backend/src/services/agents/progress.py`: basic `handle()` method that calls LlmService with progress agent system prompt
- [x] T031 [US1] Implement `POST /api/v1/agents/chat` endpoint in `backend/src/api/v1/agents.py`: accept `AgentChatRequest`, create/reuse `AgentSession`, call `TriageAgent.classify()`, route to specialist agent, stream response via SSE, log routing decision, update conversation history
- [x] T032 [US1] Implement `GET /api/v1/agents/sessions/{session_id}` endpoint in `backend/src/api/v1/agents.py`: return conversation history and routing decisions for a session, verify user ownership
- [x] T033 [US1] Add auth dependency (`get_current_user`) to all agent endpoints in `backend/src/api/v1/agents.py`
- [x] T034 [US1] Add `summary=` and `description=` to all agent route decorators, add error response schemas
- [x] T035 [US1] Add dependency injection for agent services in `backend/src/dependencies.py`: `get_triage_agent()`, `get_concepts_agent()`, `get_debug_agent()`, `get_code_review_agent()`, `get_exercise_agent()`, `get_progress_agent()`
- [x] T036 [US1] Add error handling: LLM provider unavailable → structured error response, invalid session → 404, auth failure → 401

**Checkpoint**: At this point, a student can send any question and get a correctly routed AI response. All 6 acceptance scenarios from US1 should pass.

---

## Phase 4: User Story 2 - Concepts Agent Explains Topics at the Right Level (Priority: P2)

**Goal**: Concepts Agent adapts explanation complexity based on student level (beginner/intermediate/advanced), includes runnable code examples and follow-up questions.

**Independent Test**: Send the same concept question with different student levels and verify explanations differ in complexity and depth.

### Tests for User Story 2

- [x] T037 [P] [US2] Unit tests for Concepts Agent in `backend/tests/unit/test_concepts_agent.py`: test prompt building for each level, verify level-specific instructions are included, test follow-up question generation

### Implementation for User Story 2

- [x] T038 [US2] Enhance `ConceptsAgent` in `backend/src/services/agents/concepts.py`: fetch student level from `UserProfile`, build level-adapted system prompt (beginner=simple analogies, intermediate=moderate depth, advanced=technical details), include code example requirement and follow-up question prompt
- [x] T039 [US2] Update `get_concept_agent_prompt()` in `backend/src/llm/prompts.py`: add level-specific instructions, code example requirement, follow-up question requirement (2-3 questions), visual aid suggestions for complex concepts
- [x] T040 [US2] Add `topic` parameter handling to Concepts Agent: use topic context from request to focus explanation, suggest related topics

**Checkpoint**: Concepts Agent now provides level-appropriate explanations with code examples and follow-up questions.

---

## Phase 5: User Story 3 - Debug Agent Provides Progressive Hints (Priority: P2)

**Goal**: Debug Agent implements a 3-level progressive hint system: high-level error category → specific location and cause → concrete fix suggestion. Solution only revealed after hints exhausted or explicitly requested.

**Independent Test**: Submit code with a known error and verify first response is a hint (not solution), subsequent interactions progressively reveal more detail.

### Tests for User Story 3

- [x] T041 [P] [US3] Unit tests for Debug Agent in `backend/tests/unit/test_debug_agent.py`: test progressive hint state machine, test struggle detection triggers, test hint advancement logic, test solution reveal conditions

### Implementation for User Story 3

- [x] T042 [US3] Implement `HintProgression` tracking in `backend/src/services/agents/debug.py`: create/retrieve `HintProgression` record, manage hint level state (1→2→3→solution), store hints provided in JSONB
- [x] T043 [US3] Implement error parsing in `backend/src/services/agents/debug.py`: extract error type, line number, and root cause from Python error messages, detect common patterns (off-by-one, wrong operator, missing colon, indentation)
- [x] T044 [US3] Implement progressive hint generation in `backend/src/services/agents/debug.py`: level 1 prompt (high-level error category), level 2 prompt (specific location and cause), level 3 prompt (concrete fix), solution prompt (corrected code with explanation)
- [x] T045 [US3] Implement struggle detection in `backend/src/services/agents/debug.py`: detect "I don't understand", "I'm stuck", repeated failed attempts → adapt to simpler explanation level
- [x] T046 [US3] Implement `POST /api/v1/agents/hints/advance` endpoint in `backend/src/api/v1/agents.py`: advance hint level or request solution, return hint text and remaining count
- [x] T047 [US3] Update `get_debug_agent_prompt()` in `backend/src/llm/prompts.py`: add progressive hint instructions, struggle detection triggers, pattern-specific hint guidance

**Checkpoint**: Debug Agent now provides progressive hints, tracks hint state, and detects struggle signals.

---

## Phase 6: User Story 4 - Code Review Agent Analyzes Student Code (Priority: P2)

**Goal**: Code Review Agent evaluates submitted code for correctness, PEP 8 style, efficiency, and readability. Provides constructive feedback with positive reinforcement.

**Independent Test**: Submit code with known style issues, logic bugs, and good practices; verify the agent identifies each correctly.

### Tests for User Story 4

- [x] T048 [P] [US4] Unit tests for Code Review Agent in `backend/tests/unit/test_code_review_agent.py`: test review prompt building, test feedback structure validation, test positive reinforcement inclusion

### Implementation for User Story 4

- [x] T049 [US4] Enhance `CodeReviewAgent` in `backend/src/services/agents/code_review.py`: run static analysis (PEP 8 check) before LLM analysis, build comprehensive review prompt with code, style violations, and analysis instructions
- [x] T050 [US4] Implement static analysis pre-check in `backend/src/services/agents/code_review.py`: use `pycodestyle` or `ruff` to detect PEP 8 violations programmatically, pass results to LLM for contextual feedback
- [x] T051 [US4] Update `get_code_review_agent_prompt()` in `backend/src/llm/prompts.py`: add positive reinforcement requirement, structured feedback format (correctness, style, efficiency, readability), code example suggestions

**Checkpoint**: Code Review Agent now provides comprehensive code analysis with style checking and positive reinforcement.

---

## Phase 7: User Story 5 - Exercise Agent Generates and Grades Challenges (Priority: P3)

**Goal**: Exercise Agent generates coding challenges with descriptions, starter code, and test cases. Auto-grades submissions against test cases with partial credit and constructive feedback.

**Independent Test**: Request an exercise, receive it, submit a solution, and verify grading output matches expected results.

### Tests for User Story 5

- [x] T052 [P] [US5] Unit tests for Exercise Agent in `backend/tests/unit/test_exercise_agent.py`: test exercise generation prompt, test grading logic with known-correct/incorrect/partial solutions, test partial credit calculation

### Implementation for User Story 5

- [x] T053 [US5] Implement exercise generation in `backend/src/services/agents/exercise.py`: generate exercise with topic, difficulty, description, starter code, test cases (JSONB), save via `ExerciseRepository`
- [x] T054 [US5] Implement `POST /api/v1/agents/exercises` endpoint in `backend/src/api/v1/agents.py`: accept topic + difficulty, call Exercise Agent, persist exercise, return `ExerciseResponse`
- [x] T055 [US5] Implement exercise grading in `backend/src/services/agents/exercise.py`: load exercise test cases, execute student code in DockerSandbox, compare outputs, calculate score (partial credit), generate feedback via LLM
- [x] T056 [US5] Implement `POST /api/v1/agents/exercises/{id}/submit` endpoint in `backend/src/api/v1/agents.py`: accept code, grade against test cases, persist `ExerciseSubmission`, return `ExerciseSubmissionResponse` with per-test results and feedback
- [x] T057 [US5] Update `get_exercise_agent_prompt()` in `backend/src/llm/prompts.py`: add difficulty-appropriate generation instructions, test case format requirements, feedback guidelines
- [x] T058 [US5] Integrate DockerSandbox for exercise grading: inject `DockerSandbox` into Exercise Agent, execute student code with test cases, handle timeout/error gracefully, capture execution time

**Checkpoint**: Exercise Agent now generates challenges and auto-grades submissions with partial credit and feedback.

---

## Phase 8: User Story 6 - Progress Agent Summarizes Learning Progress (Priority: P3)

**Goal**: Progress Agent calculates mastery scores per topic using the formula (40% exercises + 30% quizzes + 20% code quality + 10% streak), identifies weak areas, and provides personalized recommendations.

**Independent Test**: Seed progress data for a test user and verify the summary output matches expected mastery calculations.

### Tests for User Story 6

- [x] T059 [P] [US6] Unit tests for Progress Agent in `backend/tests/unit/test_progress_agent.py`: test mastery calculation formula with complete data, test incomplete data handling (proportional redistribution), test level mapping (0-40/41-70/71-90/91-100), test weak area identification

### Implementation for User Story 6

- [x] T060 [US6] Implement mastery calculation in `backend/src/services/agents/progress.py`: fetch exercise completion rates, quiz scores, code quality ratings, streak data; apply 40/30/20/10 formula; handle missing components with proportional redistribution
- [x] T061 [US6] Implement level mapping in `backend/src/services/agents/progress.py`: map score to Beginner (0-40), Learning (41-70), Proficient (71-90), Mastered (91-100), persist to `MasteryRecord`
- [x] T062 [US6] Implement weak area detection and recommendations: identify topics with mastery < 50%, generate personalized study recommendations, include streak acknowledgment
- [x] T063 [US6] Implement `GET /api/v1/agents/progress` endpoint in `backend/src/api/v1/agents.py`: return `ProgressSummaryResponse` with overall mastery, per-topic breakdown, weak areas, streak info, recommendations, missing components
- [x] T064 [US6] Update `get_progress_agent_prompt()` in `backend/src/llm/prompts.py`: add natural language summary generation, encouragement tone, specific practice recommendations
- [x] T065 [US6] Handle no-data case: return encouraging onboarding message with suggested first steps when student has no progress data

**Checkpoint**: All user stories should now be independently functional.

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [x] T066 [P] Contract tests in `backend/tests/contract/test_agent_api.py`: validate all 6 endpoints against OpenAPI spec in `specs/007-agent-layer/contracts/agent-api.yaml`
- [x] T067 [P] Add DB indexes verification: confirm indexes on `user_id`, `session_id`, `created_at` exist on all new tables
- [x] T068 Update `backend/src/models/__init__.py` exports to include all new agent models
- [x] T069 Run `black . && isort .` on all new files in `backend/`
- [x] T070 Run full test suite: `pytest backend/tests/unit/test_triage_routing.py backend/tests/unit/test_concepts_agent.py backend/tests/unit/test_debug_agent.py backend/tests/unit/test_code_review_agent.py backend/tests/unit/test_exercise_agent.py backend/tests/unit/test_progress_agent.py backend/tests/unit/test_agent_schemas.py backend/tests/integration/test_agent_routes.py -v`
- [x] T071 Run quickstart.md validation: execute all curl commands from `specs/007-agent-layer/quickstart.md` and verify responses
- [x] T072 Update `backend/src/api/v1/__init__.py` to export agents router

---

## Dependencies & Execution Order
j
### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-8)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Phase 9)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Integrates with US1 routing, independently testable
- **User Story 3 (P2)**: Can start after Foundational (Phase 2) - Integrates with US1 routing + session management, independently testable
- **User Story 4 (P2)**: Can start after Foundational (Phase 2) - Integrates with US1 routing, independently testable
- **User Story 5 (P3)**: Can start after Foundational (Phase 2) - Integrates with US1 routing + DockerSandbox (F05), independently testable
- **User Story 6 (P3)**: Can start after Foundational (Phase 2) - Depends on existing progress data from F02, independently testable

### Within Each User Story

- Tests MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel (T003-T007)
- All Foundational tasks marked [P] can run in parallel (T008-T016)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together:
Task: "T021 Unit tests for deterministic triage routing in backend/tests/unit/test_triage_routing.py"
Task: "T022 Integration test for /api/v1/agents/chat in backend/tests/integration/test_agent_routes.py"
Task: "T023 Schema tests in backend/tests/unit/test_agent_schemas.py"

# Launch all agent service stubs together (different files):
Task: "T026 ConceptsAgent stub in backend/src/services/agents/concepts.py"
Task: "T027 DebugAgent stub in backend/src/services/agents/debug.py"
Task: "T028 CodeReviewAgent stub in backend/src/services/agents/code_review.py"
Task: "T029 ExerciseAgent stub in backend/src/services/agents/exercise.py"
Task: "T030 ProgressAgent stub in backend/src/services/agents/progress.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (7 tasks)
2. Complete Phase 2: Foundational (13 tasks) — CRITICAL, blocks all stories
3. Complete Phase 3: User Story 1 (16 tasks)
4. **STOP and VALIDATE**: Test US1 independently — send questions, verify routing, check responses
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 (P1) → Test independently → Deploy/Demo (MVP: students can ask questions and get routed answers)
3. Add User Story 2 (P2) → Test independently → Deploy/Demo (level-adapted concept explanations)
4. Add User Story 3 (P2) → Test independently → Deploy/Demo (progressive debugging hints)
5. Add User Story 4 (P2) → Test independently → Deploy/Demo (code review with style checking)
6. Add User Story 5 (P3) → Test independently → Deploy/Demo (exercise generation and auto-grading)
7. Add User Story 6 (P3) → Test independently → Deploy/Demo (progress summaries and recommendations)
8. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (Triage + routing + chat endpoint)
   - Developer B: User Story 2 (Concepts Agent) + User Story 4 (Code Review Agent)
   - Developer C: User Story 3 (Debug Agent) + User Story 5 (Exercise Agent)
   - Developer D: User Story 6 (Progress Agent)
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Total tasks: 72**
- **MVP scope (US1 only): 36 tasks** (T001-T036)
