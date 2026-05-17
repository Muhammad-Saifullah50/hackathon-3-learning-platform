# Research: Chat Interface with AI Tutor (F15)

**Date**: 2026-05-11 | **Branch**: `015-ai-tutor-chat`

---

## 1. SSE Streaming — OpenAI Agents SDK Bug Status

**Decision**: Use `Runner.run_streamed` with `LitellmModel` for true token-by-token streaming. Replace the `_sse_result_generator` workaround in `agents.py` with an async generator that consumes `StreamedRunResult` events and emits each text delta as an SSE `data:` chunk.

**Rationale**: The upstream bug ([openai/openai-agents-python#601](https://github.com/openai/openai-agents-python/issues/601)) — `Runner.run_streamed` + `LitellmModel` raising a Pydantic `ResponseCreatedEvent.sequence_number` validation error — is **fixed in openai-agents v0.13** (confirmed by upgrading from v0.12). The project is pinned to v0.12; upgrading to v0.13 unblocks real streaming. This matches FR-003 exactly and improves SC-001 (first token latency).

**Migration steps**:
1. Upgrade `openai-agents` to `>=0.13` in `pyproject.toml` / `requirements.txt`
2. Replace `Runner.run` call with `Runner.run_streamed` in `/chat` endpoint
3. Stream `RawResponsesStreamEvent` text deltas as SSE `data:` chunks; emit `AgentUpdatedStreamEvent` as SSE `event: handoff`

**Alternatives considered**:
- Keep `Runner.run` + word-drip — rejected; real streaming is now available and strictly better
- Direct LiteLLM streaming without Agents SDK — rejected; bypasses handoff and hook logic

---

## 11. Structured Agent Output — OpenAI Agents SDK `output_type`

**Decision**: Each specialist agent is configured with an `output_type` Pydantic model passed to `Runner.run_streamed`. Text tokens stream progressively as before; `result.final_output` on stream completion is the typed Pydantic instance. The backend serialises it to JSON and emits it as `event: structured\ndata: {json}\n\n` before `data: [DONE]`.

**Agent → output type mapping**:

| Agent | `output_type` |
|-------|--------------|
| Concepts Agent | `ConceptResponse` |
| Debug Agent | `DebugResponse` |
| Exercise Agent | `ExerciseResponse` |
| Code Review Agent | `CodeReviewResponse` |
| Progress Agent | `ProgressResponse` |
| Off-topic (canned) | N/A — emits plain text + handoff `none` |

**`send_to_editor` convention**: Any response type that wants the frontend to offer a "Load in Editor" button includes a `send_to_editor: CodeBlock | None` field. The frontend checks for this field on every structured response and renders the button when non-null.

**Rationale**: Structured output removes the fragility of regex-parsing markdown from plain-text AI responses. Each response type has a defined contract the frontend can type-check. The OpenAI Agents SDK `output_type` parameter is the idiomatic mechanism for this — it instructs the LLM to conform to the schema and validates the response automatically.

**Alternatives considered**:
- Plain text with markdown fenced blocks — rejected; requires brittle frontend parsing; cannot carry metadata like difficulty, score, issues list
- Custom JSON envelope wrapping plain text — rejected; doesn't use SDK-native structured output; loses schema validation

**Frontend SSE handling update**:
```
1. On `data: {token}` → append to streamed text bubble (loading placeholder)
2. On `event: structured` → parse JSON, replace bubble with typed response card
3. On `data: [DONE]` → finalize, show any send_to_editor button
```

---

## 2. Chat Quota Storage — New Table vs. Existing `RateLimitCounter`

**Decision**: Reuse `RateLimitCounter` with identifier pattern `{user_id}:chat:{UTC_date}` (e.g., `abc123:chat:2026-05-11`), limit = 15, window = daily.

**Rationale**: `RateLimitCounter` already implements atomic upsert via `pg_insert ... on_conflict_do_update` and is used for code review rate limiting with exactly the same semantics. The spec names a `chat_quota` table, but that is a logical name, not a schema mandate. Reusing `RateLimitCounter` avoids a new migration for equivalent functionality. The `ChatQuotaService` will wrap this pattern and expose `check_and_get_remaining(user_id)` returning `(allowed: bool, remaining: int)`.

**Alternatives considered**:
- New `chat_quota` table with `messages_sent_today` + `quota_reset_date` — rejected because `RateLimitCounter` already handles this atomically with less code
- Redis-based counter — rejected because Neon PostgreSQL is already the source of truth and the daily scale (≤5 ops/user/day) doesn't justify Redis

---

## 3. Session Title Derivation

**Decision**: The title is set server-side when the **first message** is saved to a session. Title = first 60 characters of the student's first message, trimmed to the nearest word boundary. If no first message yet, title = `"New chat — {session.created_at.strftime('%b %d, %H:%M')}"`.

**Rationale**: Client-side title generation risks inconsistency across devices. Server-side assignment on first message is deterministic and requires no extra API call. 60 chars fits cleanly in a sidebar without truncation ellipsis on most screen widths.

**Alternatives considered**:
- LLM-generated session title (summarise first exchange) — rejected for MVP; adds latency and LLM cost per session creation
- Client sets title via separate PUT — rejected; extra round-trip and frontend complexity

---

## 4. `agent_sessions` Schema Extensions

**Decision**: Add two nullable columns to `agent_sessions` via Alembic migration:
- `title TEXT` — derived from first message (see §3)
- `surface VARCHAR(20)` — `'standalone'` | `'embedded'` | `NULL` (legacy sessions)

**Rationale**: Both fields are required by the spec (FR-007a needs a displayable title; SC-005 requires surface tracking for analytics). Nullable columns with no default safely handle the ~3 existing sessions from F07 development.

**Alternatives considered**:
- Separate `chat_sessions` table — rejected; `agent_sessions` already has all required fields (user_id, conversation_history, timestamps); duplication would require refactoring all of F07's session logic

---

## 5. Frontend Code Block Rendering

**Decision**: Use `react-markdown` with `react-syntax-highlighter` (Prism, `python` grammar only, `oneDark` theme). Load both via `next/dynamic` with `ssr: false` to keep the SSR bundle clean.

**Rationale**: `react-syntax-highlighter` full bundle is ~150 KB; loading only the Prism light build with a single language grammar reduces this to ~35 KB. Dynamic import ensures it does not block initial page render.

**Alternatives considered**:
- `shiki` — produces better highlighting but is heavier and SSR is complex
- Plain `<pre><code>` — rejected; spec FR-004 mandates syntax highlighting
- `highlight.js` — similar weight to Prism; less React-native API

---

## 6. Session Listing — Pagination Strategy

**Decision**: `GET /api/v1/agents/sessions` returns the 20 most recent sessions for the authenticated student, ordered by `updated_at DESC`. No cursor/offset pagination for MVP (students are unlikely to accumulate >20 sessions quickly). Add a `?limit` query param (max 50) for future use.

**Rationale**: Infinite scroll or cursor pagination adds complexity without a clear user need at this scale. Simple recency ordering matches the expected usage pattern (students pick up recent sessions).

**Alternatives considered**:
- Cursor-based pagination — deferred to post-MVP
- Full history list — rejected; renders slowly if a student somehow accumulates hundreds of sessions

---

## 7. Embedded Panel — Editor State Access

**Decision**: Extend `TutorPanelProps` to accept `code: string` and `lastOutput: string` props passed from the parent `CodeEditorPanel`. The parent already manages editor state; it simply passes the current code string and last execution result string down to `TutorPanel`.

**Rationale**: The spec (Assumption 2) says editor state is accessible via shared React context or state. Looking at the existing `CodeEditorPanel.tsx`, editor state is managed locally. Passing via props is simpler than introducing a new context and avoids prop drilling beyond one level.

**Alternatives considered**:
- React Context / Zustand store — deferred; premature for one consumer
- Read Monaco model directly from TutorPanel — tightly coupled to Monaco internals; fragile

---

## 8. Accessibility (FR-021)

**Decision**: Implement the following:
- `aria-label` on chat input (`"Message input, {n} characters remaining"`), send button, and session list (`role="list"`)
- `Enter` submits, `Shift+Enter` inserts newline (already standard textarea behavior with `onKeyDown` intercept)
- AI message container has `aria-live="polite"` so screen readers announce new responses
- Typing indicator wrapped in `role="status"` with `aria-label="AI is responding"`

**Rationale**: WCAG 2.1 AA compliance on interactive controls is required by FR-021 and the constitution.

---

## 9. Off-Topic Guardrail Implementation

**Decision (implemented)**: The Triage Agent uses the OpenAI Agents SDK input guardrail feature (`InputGuardrail`) to detect off-topic messages. When triggered, the SDK raises `InputGuardrailTripwireTriggered`, which the `/chat` endpoint catches and returns a canned redirect response ("I'm here to help with Python learning! Try asking me about Python syntax, debugging, or coding exercises.") directly without spinning up any specialist agent.

**Rationale**: SDK-level guardrails intercept the message before the Triage Agent runs, giving consistent enforcement regardless of triage confidence. The canned response is persisted to conversation history so session continuity is preserved.

**Alternatives considered**:
- Keyword/pattern matching in triage — rejected; superseded by SDK guardrail which is more robust and declarative
- System prompt instruction only — rejected; unreliable when students are adversarial

---

## 10. Resolved NEEDS CLARIFICATION Summary

| Item | Resolution |
|------|-----------|
| Streaming transport for SSE | `Runner.run_streamed` (openai-agents v0.13 fixes #601); upgrade from v0.12 |
| Structured agent output | OpenAI Agents SDK `output_type` Pydantic model per agent; `event: structured` SSE carries JSON |
| `send_to_editor` mechanism | `send_to_editor: CodeBlock \| None` field on response types; "Load in Editor" button when non-null |
| Chat quota storage | `RateLimitCounter` with `{user_id}:chat:{date}` identifier; limit=15/day |
| Session title source | Server-side: first 60 chars of first student message |
| `agent_sessions` schema | Add `title TEXT`, `surface VARCHAR(20)` via new Alembic migration |
| Code block rendering | Rendered from structured `code_blocks` field (Prism Python, dynamic import) — no markdown parsing |
| Session pagination | 20 most recent, `updated_at DESC`, `?limit` up to 50 |
| Embedded panel editor access | Props from `CodeEditorPanel` → `TutorPanel`; editor write via Monaco `model.setValue()` |
| Off-topic guardrail | `off_topic` intent in triage + canned response, no specialist invoked, no `output_type` |
