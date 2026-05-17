# Feature Specification: Chat Interface with AI Tutor

**Feature Branch**: `015-ai-tutor-chat`
**Created**: 2026-05-11
**Status**: Draft
**Input**: User description: "Chat Interface with AI Tutor — real-time chat with streaming responses, triage agent routing, context awareness, and Python guardrails"

---

## Overview

Students interact with an AI tutor through a conversational chat interface. Every message is routed through a Triage Agent that determines intent and hands off to the appropriate specialist agent — Concepts, Debug, Exercise, Code Review, or Progress. The tutor responds with streamed text, renders code blocks inline, and maintains context of the student's session. The chat is guarded to keep conversations focused on Python learning.

The feature ships two surfaces:

1. **Standalone Chat Page (`/chat`)** — General-purpose Python learning conversation. No required lesson context. Accessible from the main navigation.
2. **Embedded Chat Panel** — A collapsible sidebar inside the Interactive Code Editor (F14). Automatically includes the student's current code and last execution output as context for the AI tutor.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 — General Python Question via Standalone Chat (Priority: P1)

A student navigates to `/chat` and types a Python question such as "What is a list comprehension?" The Triage Agent classifies the intent and hands off to the Concepts Agent, which responds with an explanation and an inline code example. The response streams in token-by-token so the student sees it appearing in real time. The conversation is saved and visible on the next visit.

**Why this priority**: This is the core value of the feature — a student can ask any Python question and receive an accurate, pedagogically sound answer. Everything else builds on this flow.

**Independent Test**: Navigate to `/chat`, send "Explain Python decorators", and verify a streamed response containing a code block is received and saved.

**Acceptance Scenarios**:

1. **Given** a logged-in student on `/chat`, **When** they send "What is a for loop?", **Then** the Triage Agent routes to the Concepts Agent, a streamed response appears word-by-word, and the message + response are stored in the database.
2. **Given** a student with prior conversation history, **When** they revisit `/chat`, **Then** the previous messages are loaded and displayed in chronological order.
3. **Given** a student sends a message, **When** the AI is generating a response, **Then** a typing indicator is visible until the first token arrives.

---

### User Story 2 — Debug Help via Embedded Chat Panel (Priority: P2)

A student is writing code in the Monaco editor and hits a `TypeError`. They open the embedded chat panel and type "Why is my code failing?" Without copying anything, the tutor already has the student's current code and the last execution error as context. The Triage Agent routes to the Debug Agent, which identifies the root cause and provides progressive hints.

**Why this priority**: The embedded panel is the highest-value integration point — students get debugging help without leaving the editor or manually copying error messages.

**Independent Test**: Open the code editor with a snippet that produces a `NameError`, open the chat panel, send "What's wrong?", and verify the Debug Agent's response references the actual error without the student pasting it.

**Acceptance Scenarios**:

1. **Given** a student has code in the editor and has just run it (producing an error), **When** they open the chat panel and ask "What's wrong?", **Then** the AI response references the specific error from the last execution without requiring the student to paste it.
2. **Given** the chat panel is closed, **When** the student clicks the chat toggle button, **Then** the panel slides open without disrupting the editor layout.
3. **Given** the student is in the embedded panel, **When** they send a message, **Then** the current code (up to 4 KB) and last execution output are automatically attached as context.

---

### User Story 3 — Off-Topic Guardrail (Priority: P3)

A student tries to use the chat for non-Python topics, such as asking the tutor to write an essay or answer a math problem. The system politely declines and redirects the student to ask Python-related questions.

**Why this priority**: Guardrails protect the educational integrity of the platform and prevent misuse of compute resources.

**Independent Test**: Send "Write me a poem about the ocean" and verify the response declines and redirects to Python topics without routing to any specialist agent.

**Acceptance Scenarios**:

1. **Given** a student sends an off-topic message, **When** the Triage Agent evaluates it, **Then** the system responds with a friendly redirect message and does not invoke any specialist agent.
2. **Given** a student asks a borderline question (e.g., "What is recursion?" — which applies to Python), **When** evaluated, **Then** the system treats it as on-topic and routes normally.

---

### User Story 4 — Exercise Request via Chat (Priority: P3)

A student types "Give me a practice problem on dictionaries." The Triage Agent routes to the Exercise Agent, which generates a coding challenge appropriate to the student's current mastery level. The challenge is displayed inline in the chat with a code block showing the starter template.

**Why this priority**: Enables students to self-direct their practice from within the chat — an important learning loop.

**Independent Test**: Send "Give me a Python exercise on lists" and verify an exercise with a description and starter code block is returned, matched to the student's mastery level.

**Acceptance Scenarios**:

1. **Given** a student asks for an exercise, **When** the Exercise Agent generates one, **Then** the response includes a problem description and a fenced code block with starter code.
2. **Given** a student's mastery level for the topic is "Beginner", **When** an exercise is generated, **Then** the difficulty is appropriate for a beginner (simple iteration, not advanced patterns).

---

### Edge Cases

- What happens when the AI response is delayed beyond 30 seconds? → The system displays an error toast and allows the student to retry.
- What happens when the student sends an empty message? → The send button is disabled; no request is made.
- What happens when the student sends a very long message (>2000 characters)? → The input is accepted but truncated to 2000 characters with a visible counter warning.
- What happens when the embedded panel code context exceeds 4 KB? → The code is truncated at 4 KB and a note is included in the context indicating truncation.
- What happens when the student loses network mid-stream? → The partial response is shown with an indicator that the response was cut off; a retry button appears.
- What happens when the database save fails for a message? → The conversation continues in-session; the user is not blocked, but a warning is shown that history may not be saved.
- What happens when the Triage Agent cannot confidently classify intent? → The Concepts Agent is used as the default fallback.

---

## Requirements *(mandatory)*

### Functional Requirements

**Chat Core**

- **FR-001**: System MUST provide a standalone chat page at `/chat` accessible to all authenticated students.
- **FR-002**: System MUST provide a collapsible chat panel embedded within the Interactive Code Editor that can be toggled open and closed.
- **FR-003**: System MUST display AI responses as streaming text — tokens appear progressively as they are generated, not all at once. The streaming transport is **Server-Sent Events (SSE)** over a single long-lived HTTP POST connection.
- **FR-004**: System MUST render fenced code blocks in AI responses with Python syntax highlighting.
- **FR-005**: System MUST show a typing indicator while the AI is generating a response.
- **FR-006**: System MUST persist all chat messages (student and AI) to the database so history survives page reloads and re-logins.
- **FR-007**: System MUST load and display prior conversation history when a student opens a chat session.
- **FR-007a**: The `/chat` page MUST display a list of the student's past chat sessions (title derived from first message or timestamp), allowing them to resume any prior session or start a new one.
- **FR-007b**: Students MUST be able to create a new chat session at any time via a "New Chat" action. The daily message quota (FR-020) applies across all sessions.

**Agent Routing**

- **FR-008**: Every student message MUST be processed by the Triage Agent first, which classifies intent and routes to the appropriate specialist agent.
- **FR-009**: The Triage Agent MUST route to the following specialist agents based on intent:
  - Concept questions → Concepts Agent
  - Error / debugging requests → Debug Agent
  - Code review requests → Code Review Agent
  - Exercise / practice requests → Exercise Agent
  - Progress / mastery questions → Progress Agent
- **FR-010**: Agent routing MUST be transparent to the student — they see only the final response, not the routing mechanism.
- **FR-011**: When intent cannot be classified with confidence, the system MUST default to the Concepts Agent.

**Context**

- **FR-012**: The system MUST include the last 5 messages (student + AI combined) as conversation history with every request to the AI.
- **FR-013**: The embedded chat panel MUST automatically attach the student's current code (up to 4 KB) as context with every message.
- **FR-014**: The embedded chat panel MUST automatically attach the last execution output (stdout + stderr) as context with every message.
- **FR-015**: Both chat surfaces MUST include the student's current module, current lesson, and mastery level for each module as context when available.

**Guardrails**

- **FR-016**: The system MUST detect off-topic messages (unrelated to Python programming or learning) and respond with a polite redirect rather than invoking a specialist agent.
- **FR-017**: The standalone `/chat` page MUST NOT require any lesson or module context to function — it operates as a general Python learning assistant.

**Structured Agent Output**

- **FR-022**: Every specialist agent MUST return a **typed structured response** (not plain text) using the OpenAI Agents SDK `output_type` parameter. The response schema is determined by agent type (see Key Entities). This enables the frontend to render rich, interactive UI elements rather than plain markdown.
- **FR-023**: The backend MUST stream text tokens progressively via SSE (FR-003) and then emit one additional `event: structured` SSE event carrying the complete structured response as JSON once the agent finishes. The frontend MUST use the structured event to replace the streamed text with the fully rendered UI.
- **FR-024**: Structured responses that include a **`send_to_editor`** code block MUST cause the chat UI to display a "Load in Editor" button beneath that code block. When clicked, the button MUST load the code into the Monaco editor (in the embedded panel context) or navigate the student to the editor with that code pre-loaded (in the standalone `/chat` context).
- **FR-025**: Exercise Agent responses MUST use a structured `ExerciseResponse` type that includes: a problem title, problem description, difficulty level, and a starter code block. The starter code MUST be rendered as an interactive exercise card (not a plain code block) with a "Load Starter Code in Editor" button.
- **FR-026**: Debug Agent responses MUST use a structured `DebugResponse` type that includes: the identified error, a plain-language explanation, the fix suggestion as a code block (optional), and a progressive hint (text). When a fix code block is present, a "Apply Fix in Editor" button MUST appear.
- **FR-027**: Code Review Agent responses MUST use a structured `CodeReviewResponse` type that includes: an overall summary, a list of issues (each with line reference and severity), and an optional improved code block. The improved code block, when present, MUST have a "Load Improved Code in Editor" button.

**Input Constraints**

- **FR-018**: The chat input MUST enforce a 2000-character maximum with a visible character counter.
- **FR-019**: The send button MUST be disabled when the input is empty or when a response is already being streamed.
- **FR-021**: The chat UI MUST meet basic accessibility requirements: ARIA labels on all interactive elements (input, send button, session list), Enter key submits a message (Shift+Enter inserts newline), and new AI messages MUST be announced to screen readers via an `aria-live="polite"` region.
- **FR-020**: System MUST enforce a rate limit of **15 chat messages per student per day** (UTC). When the limit is reached, the send button is disabled and a clear message is shown (e.g., "You've used all 15 daily messages. Come back tomorrow!"). The remaining message count MUST be visible in the chat UI.

### Key Entities

- **Chat Session**: A conversation thread tied to a student. Has a unique identifier, creation timestamp, title (derived from the first message or auto-generated timestamp), and belongs to one student. A student may have **multiple saved sessions**; all are persisted. Surface type (standalone vs. embedded) is recorded per session but does not limit how many sessions a student can have.
- **Chat Message**: A single turn in the conversation. Belongs to a chat session. Has a role (student or AI), message content, timestamp, and the agent type that handled it (Triage, Concepts, Debug, etc.). Stores which specialist agent produced the response. The stored content is the structured response JSON (not raw text) for AI messages.
- **Agent Routing Decision**: Records which specialist agent the Triage Agent selected for a given message and with what confidence. Used for observability and future improvement.
- **Chat Quota**: Tracks daily message usage per student. Fields: `student_id`, `messages_sent_today` (integer, max 15), `quota_reset_date` (UTC date). Reset to 0 when the current date exceeds `quota_reset_date`. Stored via the `rate_limit_counters` table in Neon PostgreSQL (reuses existing infrastructure).
- **CodeBlock**: A reusable sub-entity within structured responses. Fields: `code` (the Python source), `language` (always `"python"` for this platform), `caption` (optional label). Present in all response types that include code.
- **ConceptResponse**: Structured output of the Concepts Agent. Fields: `explanation` (prose), `code_blocks` (list of CodeBlock, 0–3 examples), `key_points` (bullet list of takeaways), `related_topics` (list of Python topic names for follow-up).
- **DebugResponse**: Structured output of the Debug Agent. Fields: `error_identified` (the error name/message), `explanation` (why it occurred), `hint` (progressive hint text, shown before fix), `fix_code` (optional CodeBlock with corrected code, included only after the hint), `send_to_editor` (same as `fix_code` when present — triggers "Apply Fix in Editor" button).
- **ExerciseResponse**: Structured output of the Exercise Agent. Fields: `title`, `description`, `difficulty` (`beginner` / `intermediate` / `advanced`), `starter_code` (CodeBlock), `expected_concepts` (list of Python topics this exercise covers). The `starter_code` is always set as `send_to_editor`.
- **CodeReviewResponse**: Structured output of the Code Review Agent. Fields: `summary` (overall assessment), `score` (0–100 quality score), `issues` (list of `{line_ref, severity, message}` objects), `improved_code` (optional CodeBlock with refactored version). When `improved_code` is present it is set as `send_to_editor`.
- **ProgressResponse**: Structured output of the Progress Agent. Fields: `summary` (prose), `modules` (list of `{name, mastery_percent, level}` per Python module), `streak_days`, `next_recommended_topic`.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Students receive the first token of a streamed AI response within 3 seconds of sending a message under normal load.
- **SC-002**: 95% of student messages are routed to the correct specialist agent (validated against a labeled test set of 100 sample queries).
- **SC-003**: Off-topic messages are correctly identified and redirected in 100% of cases for a defined set of 20 guardrail test prompts.
- **SC-004**: Chat history is fully restored on page reload — 0 messages lost for a completed conversation of up to 50 messages.
- **SC-005**: The embedded chat panel opens and closes without any layout shift or disruption to the Monaco editor.
- **SC-006**: Students can complete a full debug help interaction (send code context → receive Debug Agent response) without manually copying any code or error output.
- **SC-007**: The feature supports at least 50 concurrent active chat sessions without response time degradation beyond the SC-001 threshold.
- **SC-008**: 100% of AI responses received by the frontend include a valid structured payload (`event: structured` SSE event) — no response renders as raw unstructured text in production.
- **SC-009**: Students can load agent-suggested code (exercise starter, debug fix, improved code review) into the Monaco editor with a single click, verified across all three agent types that produce `send_to_editor` payloads.

---

## Clarifications

### Session 2026-05-11

- Q: What streaming transport mechanism should be used for token-by-token AI responses? → A: SSE (Server-Sent Events) — HTTP streaming over a single long-lived POST connection.
- Q: What is the per-student rate limit for chat messages? → A: 15 messages per day per student.
- Q: Can students create multiple chat sessions, or is there one persistent thread per surface? → A: Students can create multiple chat sessions; all sessions are saved and remain accessible.
- Q: Where should the daily chat message quota counter be stored? → A: Database — `messages_sent_today` and `quota_reset_date` tracked in a `chat_quota` table in Neon PostgreSQL.
- Q: What level of accessibility is required for the chat UI? → A: Basic — ARIA labels on interactive elements, Enter key to submit, new AI messages announced to screen readers via `aria-live` region.

### Session 2026-05-11 (Amendment — Structured Output)

- Q: Should agents return plain markdown text or typed structured responses? → A: Typed structured responses using the OpenAI Agents SDK `output_type` Pydantic feature. Each specialist agent has its own response schema. Text still streams token-by-token; the structured payload is emitted as a final `event: structured` SSE event after streaming completes.
- Q: How should code from agent responses be loaded into the Monaco editor? → A: Via a "Load in Editor" / "Apply Fix in Editor" button on any code block flagged as `send_to_editor`. In the embedded panel, the button writes directly to the Monaco model. In the standalone `/chat` page, it navigates the student to the editor with the code pre-loaded via a shared state mechanism (React context or URL query param).
- Q: What happens to the streamed text once the structured event arrives? → A: The frontend replaces the in-progress streamed text bubble with the fully rendered structured response card. The streamed text is shown only as a loading placeholder while waiting for the structured event.

---

## Assumptions

- The OpenAI Agents SDK streaming issue (Runner.run_streamed + LiteLLM Pydantic validation error) is resolved in openai-agents v0.13. The project will be upgraded to v0.13 as the first task of this feature.
- The OpenAI Agents SDK `output_type` parameter is compatible with `Runner.run_streamed`; text tokens stream progressively and the final structured output is available at stream completion via `result.final_output`.
- The F14 Interactive Code Editor exposes its current editor state (code content and last execution result) via a shared React context or state management layer that the embedded chat panel can read.
- Students are already authenticated before accessing either chat surface; no anonymous chat is supported.
- Students can create multiple chat sessions across both surfaces. All sessions are persisted and accessible. The `/chat` page shows a session list so students can switch between or continue previous conversations. The rate limit (FR-020) applies across all sessions for the day.
- Mastery data is read from the existing `user_module_mastery` table populated by F12 (Progress Agent). No new mastery logic is introduced in this feature.
- The Triage Agent is already functional (F07 complete) and its routing logic does not need to be modified — only integrated into the chat endpoint.
- Chat message storage does not require end-to-end encryption beyond transport-layer security (TLS) already in place.

---

## Out of Scope

- Teacher access to or monitoring of student chat conversations.
- Multi-modal inputs (image uploads, voice messages).
- Exporting chat history to PDF or other formats.
- Real-time collaborative chat (multiple students in one session).
- Chat within the Quiz System (F16) — that feature handles its own interaction model.
- Push notifications for AI responses (covered by F22).
