# Feature Specification: Quiz System

**Feature Branch**: `016-quiz-system`  
**Created**: 2026-05-12  
**Status**: Draft  
**Input**: User description: "F16 Quiz System — 3 MCQs followed by 3 flashcards, AI-generated from current chat topic, structured output rendered inline in the AI Tutor Chat feed"

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Student takes a quiz from chat (Priority: P1)

A student is chatting with the AI Tutor about a Python topic (e.g., for loops). They type "give me a quiz" or the AI offers a quiz at the end of an explanation. A quiz card appears inline inside the chat feed — no navigation away. The card presents 3 multiple-choice questions followed by 3 flashcards, all about the topic just discussed. The student works through all 6 cards and sees a final score.

**Why this priority**: This is the core value of the feature — a lightweight, in-context quiz that reinforces what the student just learned without breaking their flow.

**Independent Test**: Can be tested by triggering a quiz in the chat, completing all 6 cards, and confirming a score summary renders at the end.

**Acceptance Scenarios**:

1. **Given** a student is in an active chat session on any Python topic, **When** they send a message containing "quiz" (or a variant), **Then** the next message in the chat feed is a `QuizCard` containing 3 MCQ cards followed by 3 flashcard cards, all about the current chat topic.
2. **Given** the `QuizCard` is rendered, **When** the student taps an answer option on an MCQ card, **Then** the selected option is locked in, the correct option is highlighted green, the wrong option is highlighted red, and a "Next" button appears.
3. **Given** a flashcard card is shown, **When** the student types their answer and clicks "Check", **Then** the card flips to reveal the correct definition and a grade badge (Correct / Partial / Wrong) plus one-line feedback appears.
4. **Given** the student completes all 6 cards, **Then** a score summary ("You scored X/6") appears with a per-card breakdown and a "Continue Learning" button that returns focus to the chat input.

---

### User Story 2 — Flashcard grading by AI (Priority: P2)

When a student types a written answer for a flashcard (term → definition), the system compares it to the correct definition and returns a graded result (Correct / Partial / Wrong) with a short feedback line. The student sees this immediately after the card flips, without manually self-assessing.

**Why this priority**: Self-assessment is unreliable. AI grading on typed flashcard answers gives students honest, immediate feedback that drives real learning.

**Independent Test**: Can be tested by submitting a flashcard answer via the grading endpoint and confirming the returned grade accurately reflects the quality of the answer.

**Acceptance Scenarios**:

1. **Given** a flashcard shows the term "list comprehension", **When** the student types a correct definition and clicks "Check", **Then** the AI returns grade: "Correct" and a brief confirmation.
2. **Given** the same flashcard, **When** the student types a partially correct answer (captures the idea but misses key details), **Then** the AI returns grade: "Partial" with a hint at what was missing.
3. **Given** the same flashcard, **When** the student types an incorrect or empty answer, **Then** the "Check" button remains disabled (for empty) or the AI returns grade: "Wrong" with a short corrective note.

---

### User Story 3 — Mastery score updated after quiz (Priority: P3)

After a student completes all 6 cards and the score is computed, the system updates the student's mastery record for the relevant topic. The quiz score contributes to the overall mastery calculation (quizzes = 30% weight).

**Why this priority**: Without mastery updates, quizzes are disconnected from progress. This closes the loop so quiz performance influences the student's learning trajectory.

**Independent Test**: Can be tested by completing a quiz, then checking the student's mastery record for the relevant topic to confirm the quiz score component changed.

**Acceptance Scenarios**:

1. **Given** a student completes a quiz on "for loops" and scores 4/6, **When** the quiz is submitted, **Then** the mastery record for the "for loops" topic is updated with a quiz score of approximately 67 (out of 100).
2. **Given** a student has no prior mastery record for the topic, **When** the quiz is submitted, **Then** a new mastery record is created for that topic.
3. **Given** a student already has a mastery record, **When** the quiz is submitted, **Then** the existing record is updated (not duplicated).

---

### User Story 4 — Quiz history persisted (Priority: P4)

Every quiz session — questions generated, student answers, and per-card grades — is stored. This allows future analytics, teacher review, and struggle detection to reference quiz attempts.

**Why this priority**: History enables teacher oversight and struggle detection (F20). Without persistence, the quiz contributes nothing to the platform's analytics layer.

**Independent Test**: Can be tested by completing a quiz and querying the quiz sessions store to confirm the full session (questions + answers + score) is present.

**Acceptance Scenarios**:

1. **Given** a student completes a quiz, **When** the final score is submitted, **Then** a quiz session record exists containing: the topic, all 6 questions (with correct answers), the student's answers, per-card grades, and the final score.
2. **Given** a student starts a quiz but does not complete it, **Then** a partial session record still exists with no score and no answers, only the generated questions.

---

### Edge Cases

- What happens if the AI cannot determine the chat topic? → Falls back to the student's current active module topic.
- What happens if the student sends a quiz request but is discussing a non-Python topic? → The off-topic guardrail responds; no quiz is generated.
- What happens if the student submits an empty flashcard answer? → The "Check" button is disabled until at least 1 character is typed.
- What happens if the AI grading call fails for a flashcard? → The card shows "Could not grade — please try again"; the student can re-submit without losing their answer.
- What happens if quiz generation fails entirely (AI timeout or bad structured output)? → An inline error message appears in the chat feed ("Couldn't generate a quiz right now — try again") with a retry button that re-sends the original quiz request. No partial quiz session is created.
- What happens if the student leaves the chat mid-quiz? → The partial session is saved. On return to the same chat session, the incomplete `QuizCard` is re-rendered at its original position in the chat feed with already-answered cards locked in their completed state; the student can resume from where they left off.

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST generate a quiz session containing exactly 3 MCQ questions followed by 3 flashcard (term → definition) questions, calibrated to the current chat topic.
- **FR-002**: The system MUST render the quiz inline in the AI Tutor Chat feed as an interactive card — no separate page navigation required. While the quiz is being generated, the existing `TypingIndicator` component MUST be shown in the chat feed; the `QuizCard` replaces it upon arrival.
- **FR-003**: The quiz generator MUST emit a structured response (using the same `response_type` discriminated-output pattern as all other specialist agents) so the chat frontend can detect and render the quiz UI.
- **FR-004**: MCQ cards MUST present exactly 4 answer options; selecting one locks it in with immediate visual feedback (correct = green highlight, wrong = red highlight with correct option also highlighted).
- **FR-005**: Flashcard cards MUST show the term on the front; after the student types an answer and clicks "Check", the card MUST flip to reveal the correct definition.
- **FR-006**: After a flashcard flips, the system MUST return an AI grade (Correct / Partial / Wrong) and one-line feedback within the card.
- **FR-007**: The "Check" button on flashcard cards MUST be disabled until the student has typed at least 1 character.
- **FR-008**: The system MUST display a score summary after all 6 cards are completed, showing total score (X/6), per-card result, and a "Continue Learning" button.
- **FR-009**: The system MUST update the student's mastery record for the quiz topic after the quiz is fully submitted, applying the quiz score to the quizzes component (30% weight in mastery formula). The quiz agent's system prompt MUST list all 8 fixed curriculum module slugs (e.g., `control_flow`, `basics`) as constrained choices; the AI MUST select exactly one from that list at generation time and the mastery update uses this slug.
- **FR-010**: The system MUST persist every quiz session: the generated questions, student answers, AI grades, and final score. Persisted quiz sessions MUST be accessible to teachers via the existing student-monitoring/struggle-alert layer; no new teacher UI is required in this feature.
- **FR-011**: The triage layer MUST detect quiz intent from the student's chat message and route to the quiz generator.
- **FR-012**: If the chat topic cannot be determined, the system MUST fall back to the student's current active module topic.
- **FR-013**: MCQ feedback (correct/wrong highlight) MUST be applied client-side — no network round-trip needed for MCQ grading.
- **FR-014**: Quiz generation MUST be triggered via the existing `POST /api/v1/agents/chat` triage route, which returns a `quiz` response type in structured output. All post-generation quiz interactions (flashcard grading, session submission, and state retrieval) MUST use dedicated quiz endpoints: `GET /api/v1/quiz/{session_id}` (full current state for resumption), `POST /api/v1/quiz/{session_id}/grade-flashcard`, and `POST /api/v1/quiz/{session_id}/submit`. These endpoints are excluded from the 15 msg/day chat quota.
- **FR-015**: Every quiz endpoint MUST enforce ownership: the authenticated student's `user_id` (from JWT) MUST match `quiz_sessions.student_id`. Requests where they differ MUST return HTTP 403. Teacher-role users MAY read any student's quiz sessions via the existing monitoring layer without this restriction.

### Key Entities

- **Quiz Session**: A single attempt at a 6-card quiz. Stored as a single `quiz_sessions` row with JSONB columns: `questions` (3 MCQ + 3 flashcard with correct answers), `student_answers`, and `grades`. Additional columns: `topic` (VARCHAR), `module_slug` (VARCHAR, one of the 8 curriculum slugs), `status` (VARCHAR: `generated` | `in_progress` | `completed`), `score` (FLOAT, nullable until completed), `completed_at` (TIMESTAMP, nullable), `chat_session_id` (FK). Transitions: `generated` on creation → `in_progress` on first card answer → `completed` on submit call.
- **MCQ Question**: A multiple-choice question with 4 answer options and a correct option index (known at generation time).
- **Flashcard Question**: A term (front) and definition (back) pair; the definition is sent to the client at generation time (for card-flip reveal) but grading is done by AI against the student's typed answer.
- **Card Grade**: The AI assessment of a student's typed flashcard answer — Correct, Partial, or Wrong — with one-line feedback text.
- **Mastery Record**: The student's mastery data for a topic, including a quizzes score component updated after each completed quiz.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A student can trigger, complete, and receive results for a full 6-card quiz without leaving the chat page, in under 5 minutes.
- **SC-002**: MCQ answer feedback (correct/wrong highlight) appears immediately on tap — no perceptible delay.
- **SC-003**: Flashcard AI grading returns a grade and feedback within 5 seconds of the student clicking "Check" in 95% of cases.
- **SC-004**: After quiz submission, the student's mastery record for the topic reflects the updated quiz score within 10 seconds.
- **SC-005**: 100% of completed quiz sessions are stored with questions, answers, and scores intact — no silent data loss.
- **SC-006**: Quiz generation is blocked for non-Python topics in 100% of cases (off-topic guardrail).

---

## Assumptions

- Quiz sessions are always triggered from the AI Tutor Chat (F15); there is no standalone `/quiz` page entry point in this feature.
- The topic is inferred from the current chat conversation context by the quiz-generating agent; the student does not manually pick a topic.
- MCQ correct answers are embedded in the structured output at generation time; MCQ grading is entirely client-side.
- The flashcard definition (correct answer) is also sent to the client at generation time (for the flip reveal); only the student's typed attempt is sent back to the server for AI grading.
- Quiz interactions (MCQ taps, flashcard submits) do not count toward the 15 messages/day chat quota.
- The quiz score contribution to mastery follows the existing formula: quizzes = 30% of total mastery score.
- A quiz session is "complete" only when all 6 cards have been answered and the final submit call succeeds.
- Students may retake quizzes on the same module topic unlimited times; each attempt is stored as a new, independent quiz session. Mastery is updated using the most recent completed quiz score for that module (not highest or averaged).
- Scoring: MCQ = 1 point if correct, 0 if wrong; Flashcard = 1 for Correct, 0.5 for Partial, 0 for Wrong. Total out of 6, mapped to 0–100 for mastery.

---

## Dependencies

- **F02** (Database Schema): Requires async DB access and migration infrastructure for a new quiz session table.
- **F11** (Exercise Agent): The quiz generator is a new specialist agent that reuses the same structured-output and agent infrastructure patterns.
- **F15** (AI Tutor Chat): Quiz is triggered from and rendered inside the chat feed. Triage must recognize quiz intent. The SSE structured-output renderer must support the new `quiz` response type.
- **F12** (Progress Agent / Mastery): Quiz scores are written to the mastery record store using the existing mastery calculation infrastructure.

---

## Clarifications

### Session 2026-05-17

- Q: How does the AI-inferred chat topic map to a specific module for the mastery update? → A: The quiz agent maps the inferred topic to the closest of the 8 fixed curriculum module slugs at generation time; the mastery update uses this module slug.
- Q: How should the UI handle the quiz generation loading state? → A: Reuse the existing `TypingIndicator` in the chat feed during generation; the `QuizCard` replaces it when the response arrives.
- Q: Can a student retake a quiz on the same topic? → A: Unlimited retakes allowed; each attempt stored as a new quiz session; mastery uses the most recent completed quiz score for the module.
- Q: Should teachers be able to see a student's quiz session history? → A: Yes — quiz sessions are accessible to teachers via the existing student monitoring view; no new dedicated teacher UI in this feature.
- Q: On returning to a chat session with an incomplete quiz, is the quiz re-shown? → A: Yes — the incomplete `QuizCard` is re-rendered at its original position with already-answered cards locked; student resumes from where they left off.
- Q: How should quiz-specific actions (flashcard grading, submission) be exposed via API? → A: Dedicated quiz endpoints (`POST /api/v1/quiz/{session_id}/grade-flashcard`, `POST /api/v1/quiz/{session_id}/submit`) for all post-generation actions; quiz generation is still triggered via the chat triage route (`POST /api/v1/agents/chat`) which returns a `quiz` response type.
- Q: What should the chat feed show if quiz generation fails entirely? → A: Show an inline error message in the chat feed ("Couldn't generate a quiz right now — try again") with a retry button that re-sends the original quiz request.
- Q: How should quiz questions, answers, and grades be stored in the database? → A: JSONB columns on a single `quiz_sessions` row: `questions JSONB`, `student_answers JSONB`, `grades JSONB`. No separate normalized tables for questions or answers.
- Q: What lifecycle states should a quiz session move through? → A: Three states: `generated` (questions created, no answers yet) → `in_progress` (at least one card answered) → `completed` (all 6 answered and submit called). State is stored as a `status` VARCHAR column on `quiz_sessions`.
- Q: What is the authorization rule for quiz endpoints? → A: Ownership check on every quiz endpoint — the authenticated student's `user_id` (from JWT) must match `quiz_sessions.student_id`; return HTTP 403 on mismatch. Teachers may read any student's quiz sessions via the existing monitoring layer.
- Q: How does the frontend retrieve current quiz state when a student returns to a chat with an in-progress quiz? → A: Via a dedicated `GET /api/v1/quiz/{session_id}` endpoint returning full current session state (questions, student_answers, grades, status); the chat session detail response embeds the `quiz_session_id` reference only.
- Q: How does the quiz agent determine the module_slug? → A: The 8 curriculum slugs are listed as constrained choices in the quiz agent's system prompt; the AI selects exactly one from the list at generation time — no post-generation mapping step.
