# Tasks: Chat Interface with AI Tutor (F15)

**Input**: Design documents from `/specs/015-ai-tutor-chat/`
**Branch**: `015-ai-tutor-chat` | **Date**: 2026-05-11
**Prerequisites**: plan.md ✅ spec.md ✅ research.md ✅ data-model.md ✅ contracts/chat-api.yaml ✅

**User Stories**:
- **US1 (P1)**: General Python Question via Standalone Chat (`/chat` page, streaming, history)
- **US2 (P2)**: Debug Help via Embedded Chat Panel (TutorPanel upgrade with code context)
- **US3 (P3)**: Off-Topic Guardrail (polite redirect, no specialist agent invoked)
- **US4 (P3)**: Exercise Request via Chat (exercise routing renders correctly in chat)

---

## Phase 1: Setup

**Purpose**: SDK upgrade and frontend package installation — unblocks all implementation.

- [X] T001 Upgrade `openai-agents` to `>=0.13` in `backend/pyproject.toml` (or `requirements.txt`) and run `pip install -e .` to pick up the streaming fix for `Runner.run_streamed` + `LitellmModel`
- [X] T002 [P] Install `react-markdown` and `react-syntax-highlighter` (plus `@types/react-syntax-highlighter`) in `frontend/package.json` via `npm install`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: DB schema, service layer, shared hooks, and triage extension that ALL user stories depend on.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [X] T003 Create Alembic migration `backend/alembic/versions/20260511_add_chat_session_title_surface.py` — add `title TEXT NULL` and `surface VARCHAR(20) NULL` columns + check constraint + `idx_agent_session_user_updated` index to `agent_sessions`
- [X] T004 Add `title` and `surface` columns to `AgentSession` SQLAlchemy model in `backend/src/models/agent_session.py` with matching `CheckConstraint` and index
- [X] T005 [P] Add new Pydantic v2 schemas `ChatSessionListItem`, `ChatSessionDetail`, `ChatQuotaStatus` and extend `AgentChatRequest` with `execution_output: Optional[str]` and `surface: Optional[Literal['standalone','embedded']]` in `backend/src/schemas/agents.py`
- [X] T005b [P] Define structured output Pydantic models `CodeBlock`, `IssueItem`, `ConceptResponse`, `DebugResponse`, `ExerciseResponse`, `CodeReviewResponse`, `ProgressResponse` in `backend/src/schemas/agent_responses.py` — each with `response_type` discriminator literal and `send_to_editor: Optional[CodeBlock]` field
- [X] T006 [P] Create `ChatQuotaService` in `backend/src/services/chat_quota_service.py` — wraps `RateLimitCounter` with identifier `{user_id}:chat:{UTC_date}`, exposes `check_and_get_remaining(db, user_id) -> tuple[bool, int]` (returns `allowed, remaining`)
- [X] T007 Add `list_sessions(user_id, limit=20)` and `get_session_detail(session_id)` methods to `AgentSessionRepository` in `backend/src/repositories/agent_session_repository.py`
- [X] T008 Register `get_chat_quota_service` dependency factory in `backend/src/dependencies.py`
- [X] T009 Add `off_topic` intent detection to `classify_intent()` in `backend/src/services/agents/triage.py` — keyword/pattern matching for clearly non-Python requests; return confidence ≥ 0.9 for clear off-topic, route to canned response in endpoint (no specialist agent)
- [X] T010 [P] Create typed fetch helpers `sendMessage()`, `listSessions()`, `getSession()`, `getQuota()` in `frontend/src/lib/api/chat.ts` using `NEXT_PUBLIC_BACKEND_URL`

**Checkpoint**: Migration applied, `ChatQuotaService` unit-testable, triage has `off_topic`, typed API client ready — user story phases can now start.

---

## Phase 3: User Story 1 — General Python Question via Standalone Chat (P1) 🎯 MVP

**Goal**: Student visits `/chat`, sends a Python question, receives a streamed response with syntax-highlighted code blocks, sees their quota remaining, and has their history restored on reload.

**Independent Test**: Navigate to `/chat`, send "Explain Python decorators", verify a streamed response with a code block arrives, the session appears in the sidebar, and history survives a page reload. Quota badge shows 4 remaining.

### Backend — US1

- [X] T010b [P] Wire each specialist agent factory in `backend/src/services/agents/agents.py` to use its corresponding `output_type`: `get_concepts_agent()` → `ConceptResponse`, `get_debug_agent()` → `DebugResponse`, `get_exercise_agent()` → `ExerciseResponse`, `get_code_review_agent()` → `CodeReviewResponse`, `get_progress_agent()` → `ProgressResponse` (import from `src/schemas/agent_responses.py`)
- [X] T011 [US1] Upgrade `POST /api/v1/agents/chat` in `backend/src/api/v1/agents.py`:
  - Replace `Runner.run` with `Runner.run_streamed`
  - Check quota via `ChatQuotaService` before running; return 429 with `RateLimitErrorResponse` if exhausted
  - Short-circuit with canned SSE response when `triage_result.intent == 'off_topic'` (no specialist agent, no `output_type`)
  - Set `session.title` on first message (first 60 chars, word-boundary trim) if currently NULL
  - Emit SSE events in order: `event: session`, `event: quota` (remaining count), `event: handoff`, progressive text `data:` tokens, `event: structured` with `result.final_output.model_dump_json()`, `data: [DONE]`
  - Pass `execution_output` from request into `LearnFlowContext` for Debug Agent
  - Store structured JSON (not raw text) as AI message in `conversation_history`
- [X] T012 [P] [US1] Add `GET /api/v1/agents/sessions` endpoint to `backend/src/api/v1/agents.py` — calls `session_repo.list_sessions()`, returns `list[ChatSessionListItem]`, honours `?limit` (max 50, default 20)
- [X] T013 [P] [US1] Add `GET /api/v1/agents/sessions/{session_id}` endpoint to `backend/src/api/v1/agents.py` — returns `ChatSessionDetail` with full `conversation_history`; 403 if session belongs to another user
- [X] T014 [P] [US1] Add `GET /api/v1/agents/quota` endpoint to `backend/src/api/v1/agents.py` — returns `ChatQuotaStatus` (no side effects, read-only)

### Frontend — US1

- [X] T015 [P] [US1] Create `useStreamChat` hook in `frontend/src/hooks/useStreamChat.ts` — opens SSE stream via `fetch` + `ReadableStream`, handles `event: session`, `event: quota`, `event: handoff`, text `data:` tokens, `event: structured` (parses JSON into `TutorResponse`), and `data: [DONE]`; exposes `{ sendMessage, isStreaming, sessionId, quotaRemaining, structuredResponse }`
- [X] T016 [P] [US1] Create `useChatSessions` hook in `frontend/src/hooks/useChatSessions.ts` — React Query `useQuery` to fetch session list; `createSession` mutation that POSTs first message (session created implicitly by backend)
- [X] T017 [P] [US1] Create `useChatQuota` hook in `frontend/src/hooks/useChatQuota.ts` — React Query `useQuery` for `GET /agents/quota`; invalidated after each `sendMessage`
- [X] T018 [P] [US1] Create `TypingIndicator` component in `frontend/src/components/chat/TypingIndicator.tsx` — animated three-dot indicator; wrapped in `role="status"` + `aria-label="AI is responding"`; shown while `isStreaming && streamedText.length === 0`
- [X] T019 [US1] Create `ChatMessage` component in `frontend/src/components/chat/ChatMessage.tsx`:
  - Accepts `message: ConversationMessage | TutorResponse` (plain text for user, structured for AI)
  - Detects `response_type` discriminator to render the correct card variant:
    - `concept` → `ConceptCard` (explanation prose + code blocks with copy button)
    - `debug` → `DebugCard` (error badge, hint, optional fix code block + "Apply Fix in Editor" button)
    - `exercise` → `ExerciseCard` (title, description, difficulty badge, starter code + "Load Starter Code in Editor" button)
    - `code_review` → `CodeReviewCard` (score badge, issue list, optional improved code + "Load Improved Code in Editor" button)
    - `progress` → `ProgressCard` (summary, module mastery list)
    - Fallback: plain text bubble (for legacy F07 messages and off-topic redirects)
  - All code blocks use `react-syntax-highlighter` Prism Python with copy-to-clipboard button
  - `aria-live="polite"` on AI message container; each card variant keyboard-accessible
- [X] T020 [US1] Create `ChatInput` component in `frontend/src/components/chat/ChatInput.tsx` — `<textarea>` with 2000-char max + visible counter (warns at 1800+); `Enter` submits, `Shift+Enter` inserts newline; send `<button>` disabled when empty, streaming, or quota exhausted; quota badge showing "N of 5 remaining" (red when 0); ARIA labels on all interactive elements
- [X] T021 [US1] Create `ChatWindow` component in `frontend/src/components/chat/ChatWindow.tsx` — scrollable message list using `useChatSessions` for history load, `useStreamChat` for live messages; renders `ChatMessage` list + `TypingIndicator` + partial streamed text as it arrives; auto-scrolls to bottom on new content
- [X] T022 [US1] Create `SessionSidebar` component in `frontend/src/components/chat/SessionSidebar.tsx` — collapsible list of past sessions (title + relative timestamp); "New Chat" button clears active session; active session highlighted; `role="list"` + `aria-label="Chat sessions"`
- [X] T023 [US1] Replace coming-soon stub with full chat page in `frontend/src/app/(student)/chat/page.tsx` — compose `SessionSidebar` + `ChatWindow` + `ChatInput`; wrap in `React.Suspense`; load session from URL param or most recent session on mount; expose `onLoadToEditor(code: string)` callback that navigates to `/playground?code={encoded}` so "Load in Editor" buttons work from standalone chat

**Checkpoint**: Visit `/chat`, send a Python question, see streamed response with code block, quota badge updates, history persists on reload, session appears in sidebar. ✅

**Checkpoint**: Visit `/chat`, send a Python question, see streamed response with code block, quota badge updates, history persists on reload, session appears in sidebar. ✅

---

## Phase 4: User Story 2 — Debug Help via Embedded Chat Panel (P2)

**Goal**: Student with a failing code snippet in the editor opens the tutor panel; their current code and last execution output are automatically sent as context; the Debug Agent references the specific error in its response.

**Independent Test**: Open the code editor with a `NameError`, run it, open the tutor panel, send "What's wrong?", verify the AI response names the specific variable without the student pasting any code.

- [X] T024 [US2] Upgrade `TutorPanel` in `frontend/src/components/editor/TutorPanel.tsx`:
  - Extend `TutorPanelProps` with `code?: string`, `lastOutput?: string`, and `editorRef: React.RefObject<monaco.editor.IStandaloneCodeEditor>`
  - Replace local `fetch` + manual SSE parsing with `useStreamChat` hook (shared with `/chat` page)
  - Truncate `code` to 4096 chars before sending; include `surface: 'embedded'` in request body
  - Render `ChatMessage` component (shared) so structured cards appear in the panel
  - Wire "Load in Editor" / "Apply Fix in Editor" buttons to call `editorRef.current?.getModel()?.setValue(code)` directly — no navigation needed in embedded context
  - Show quota badge (remaining messages) using `useChatQuota`
  - Persist `sessionId` across panel open/close via `useRef` so conversation continues
  - Add `aria-label` to toggle button and `role="region"` to panel container
- [X] T025 [US2] Pass `currentCode`, `lastExecutionOutput`, and `editorRef` from the editor state to `TutorPanel` in `frontend/src/components/editor/CodeEditorPanel.tsx` — read Monaco editor value via `editorRef.current?.getValue()` and the last execution result from local state; pass `editorRef` directly so TutorPanel can call `model.setValue()` for "Load in Editor" buttons

**Checkpoint**: Run broken code in editor → open tutor panel → ask "Why is this failing?" → AI response references the actual error message. ✅

---

## Phase 5: User Story 3 — Off-Topic Guardrail via SDK Input Guardrails (P3)

**Goal**: Non-Python messages receive a polite redirect without invoking any specialist agent; borderline Python-adjacent questions are treated as on-topic. Guardrail uses the OpenAI Agents SDK `@input_guardrail` decorator with an LLM-based classifier — more robust than keyword matching and runs in **parallel** with the first agent LLM call (minimal latency overhead).

**SDK Mechanic**: `@input_guardrail` wraps an async function that receives `(ctx, agent, input)` and returns `GuardrailFunctionOutput`. If `tripwire_triggered=True`, the SDK raises `InputGuardrailTripwireTriggered` before the specialist agent produces output; the endpoint catches this exception inside the streaming generator and emits the canned SSE response instead. Quota is debited and the redirect message is persisted to history regardless.

**Independent Test**: Send "Write me a poem about the ocean" → verify response declines + redirects to Python topics; send "What is recursion?" → verify normal routing to Concepts Agent.

- [X] T026a [US3] Create `backend/src/services/agents/model_provider.py` — extract `_ConfiguredLitellmProvider(ModelProvider)` and a `get_run_config() -> RunConfig` helper from `backend/src/api/v1/agents.py` into this shared module (imports `settings`, `LitellmModel`, `RunConfig`); all other modules import from here to avoid duplication

- [X] T026b [US3] Create `backend/src/services/agents/guardrails.py`:
  - `OffTopicCheck(is_off_topic: bool, reasoning: str)` — Pydantic structured output for the classifier
  - `_off_topic_classifier` — `Agent(name="off-topic-classifier", instructions=..., output_type=OffTopicCheck, model_settings=ModelSettings(temperature=0.0, max_tokens=100))` — instructs the LLM to flag non-Python content (poems, sports, recipes, weather, history, etc.) and pass through anything Python/CS/programming related; when in doubt, treat as on-topic
  - `off_topic_guardrail` — `@input_guardrail` async function; runs `Runner.run(_off_topic_classifier, input, context=ctx.context, run_config=get_run_config())`; returns `GuardrailFunctionOutput(output_info=result.final_output, tripwire_triggered=result.final_output.is_off_topic)`
  - Imports: `Agent, GuardrailFunctionOutput, RunContextWrapper, Runner, TResponseInputItem, input_guardrail, ModelSettings` from `agents`

- [X] T026c [US3] Add `input_guardrails=[off_topic_guardrail]` to **all 6 agent factories** in `backend/src/services/agents/agents.py` (triage, concepts, debug, code_review, exercise, progress) — import `off_topic_guardrail` from `guardrails`; SDK guarantees the guardrail only fires for the **first** agent in the workflow, so attaching to all ensures coverage regardless of which specialist is called directly

- [X] T026d [US3] Update `agent_chat` in `backend/src/api/v1/agents.py`:
  - Add `from agents import InputGuardrailTripwireTriggered`
  - Add `from src.services.agents.model_provider import get_run_config`
  - Remove the local `_ConfiguredLitellmProvider` class; replace all `RunConfig(model_provider=_ConfiguredLitellmProvider())` with `get_run_config()`
  - Remove the `triage_result.intent == "off_topic"` short-circuit block (lines ~229–239) — SDK guardrail handles this now
  - Inside `_generate()`, wrap the `async for chunk in _sse_streamed_generator(...)` loop in `try/except InputGuardrailTripwireTriggered`: on exception, `await session_repo.add_message_to_history(str(session_id), "assistant", OFF_TOPIC_CANNED)` then yield `event: handoff\ndata: none\n\n`, `data: {OFF_TOPIC_CANNED}\n\n`, `data: [DONE]\n\n` — note session/quota SSE events are already emitted by `_sse_streamed_generator` before the exception fires

- [X] T027 [P] [US3] Style off-topic redirect messages with a distinct visual indicator in `frontend/src/components/chat/ChatMessage.tsx` — when `agentType === 'none'` render a subtle info-style bubble (e.g., amber border) rather than the standard AI blue

**Checkpoint**: Send "Tell me about the French Revolution" → guardrail classifier flags it → amber-bordered redirect message appears mid-stream after session/quota events; quota decrements by 1. ✅

---

## Phase 6: User Story 4 — Exercise Request via Chat (P3)

**Goal**: Asking for a practice problem routes to the Exercise Agent, which returns a problem description and a fenced starter-code block rendered in the chat.

**Independent Test**: Send "Give me a Python exercise on lists" → verify response contains a readable problem description and a syntax-highlighted code block with a starter template; no 500 errors.

- [X] T028 [US4] Audit `classify_intent()` in `backend/src/services/agents/triage.py` — verify patterns cover common exercise request phrasings ("give me a problem", "practice exercise", "coding challenge", "quiz me on"); add any missing patterns
- [X] T029 [P] [US4] Verify `ExerciseAgent` prompt in `backend/src/services/agents/agents.py` / prompt templates instructs the agent to include a fenced Python code block (` ```python `) in every exercise response so `ChatMessage.tsx` renders it with syntax highlighting

**Checkpoint**: Chat exercise request → syntax-highlighted starter code block appears in the chat bubble. ✅

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Accessibility audit, error handling edge cases, bundle optimisation, and quickstart validation.

- [X] T030 Audit all new chat components for ARIA compliance per FR-021: verify `aria-label` on input + send button + session list, `aria-live="polite"` on AI message region, `role="status"` on typing indicator — fix any gaps in `frontend/src/components/chat/`
- [X] T031 [P] Implement error boundary / toast notifications for chat-specific failures in `frontend/src/components/chat/ChatWindow.tsx`: 30-second response timeout toast, network-cut partial-response indicator + retry button, DB-save warning (non-blocking)
- [X] T032 [P] Verify `react-syntax-highlighter` uses the light Prism build with only the `python` grammar registered in `frontend/src/components/chat/ChatMessage.tsx`; confirm Next.js bundle analyser reports < 200 KB initial JS gzipped
- [X] T033 Run all smoke tests from `specs/015-ai-tutor-chat/quickstart.md` and fix any failures; confirm `alembic upgrade head` applies cleanly on a fresh DB

---

## Dependencies & Execution Order

### Phase Dependencies

```
Phase 1 (Setup)
  └── Phase 2 (Foundational)  ← BLOCKS all user stories
        ├── Phase 3 (US1) 🎯 MVP  ← start here after Phase 2
        ├── Phase 4 (US2)         ← can start after Phase 2; useStreamChat from US1 must be done first
        ├── Phase 5 (US3)         ← T009 (triage) from Phase 2 is the prerequisite; T026 follows T011
        └── Phase 6 (US4)         ← T019 (ChatMessage) from US1 must be done first
Phase 7 (Polish)  ← after all user stories
```

### User Story Dependencies (within stories)

| Story | Hard Prerequisites |
|-------|--------------------|
| US1   | Phase 2 complete |
| US2   | Phase 2 + T015 (`useStreamChat`) + T019 (`ChatMessage`) |
| US3   | T009 (triage `off_topic`) + T011 (chat endpoint upgrade) |
| US4   | T019 (`ChatMessage` code block rendering) |

### Within Each User Story

- Backend endpoints (T011–T014) and frontend hooks (T015–T017) are independent [P]
- Frontend components build bottom-up: `TypingIndicator` → `ChatMessage` → `ChatInput` → `ChatWindow` → `SessionSidebar` → page
- Session sidebar requires session list endpoint (T012) to be live before it has real data

---

## Parallel Opportunities

### Phase 2 (all can run in parallel after T003/T004 are done)
```
T005 (schemas) ‖ T006 (ChatQuotaService) ‖ T007 (repo methods) ‖ T008 (deps) ‖ T009 (triage) ‖ T010 (TS client)
```

### Phase 3 — Backend vs Frontend
```
Backend:  T011 → T012 ‖ T013 ‖ T014
Frontend: T015 ‖ T016 ‖ T017 ‖ T018
          → T019 → T020 → T021 → T022 → T023
```

### Phase 4 — US2
```
T024 (TutorPanel) ‖ T025 (CodeEditorPanel props)  [merge when both done]
```

---

## Parallel Example: Phase 3 US1

```bash
# Backend (launch together after T003/T004):
Task T011: "Upgrade /chat endpoint to Runner.run_streamed + quota + off_topic in backend/src/api/v1/agents.py"
Task T012: "Add GET /agents/sessions endpoint in backend/src/api/v1/agents.py"
Task T013: "Add GET /agents/sessions/{id} endpoint in backend/src/api/v1/agents.py"
Task T014: "Add GET /agents/quota endpoint in backend/src/api/v1/agents.py"

# Frontend hooks (launch together after T010):
Task T015: "Create useStreamChat hook in frontend/src/hooks/useStreamChat.ts"
Task T016: "Create useChatSessions hook in frontend/src/hooks/useChatSessions.ts"
Task T017: "Create useChatQuota hook in frontend/src/hooks/useChatQuota.ts"
Task T018: "Create TypingIndicator component in frontend/src/components/chat/TypingIndicator.tsx"
```

---

## Implementation Strategy

### MVP First (US1 Only — 23 tasks)

1. Complete **Phase 1**: Setup (T001–T002)
2. Complete **Phase 2**: Foundational (T003–T010)
3. Complete **Phase 3**: User Story 1 (T011–T023)
4. **STOP and VALIDATE**: Full standalone `/chat` smoke test from `quickstart.md §3`
5. Deploy/demo: students can ask Python questions and get streamed, persisted answers

### Incremental Delivery

| Step | Adds | Tests |
|------|------|-------|
| MVP (US1) | `/chat` page with streaming, history, quota | Quickstart §3.1–3.2 |
| + US2 | Embedded panel with code context | Quickstart §3.3 |
| + US3 | Off-topic guardrail | Quickstart §3.5 |
| + US4 | Exercise rendering | Send "Give me a list exercise" |
| + Polish | Accessibility, error handling | FR-021 audit |

---

## Notes

- [P] = parallelisable (different files, no shared state)
- [US1/2/3/4] = maps to spec user story for traceability
- Run `alembic upgrade head` before any backend testing (T003 migration required)
- The `openai-agents` v0.13 upgrade (T001) must be done before T011; otherwise `Runner.run_streamed` will still fail
- `useStreamChat` (T015) is the shared building block for both `/chat` (US1) and `TutorPanel` (US2) — implement it before T021 and T024
- All 33 tasks follow the required checklist format: `- [ ] T### [P?] [US?] Description with file path`
