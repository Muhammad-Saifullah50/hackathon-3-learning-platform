# Feature Specification: Interactive Code Editor

**Feature Branch**: `014-interactive-code-editor`
**Created**: 2026-05-10
**Status**: Draft
**Input**: User description: "014-interactive-code-editor"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Write and Run Python Code (Priority: P1)

A student opens the code editor — either from the navbar "Playground" link or embedded inside a lesson — writes Python code, and clicks Run. They immediately see the output (printed values, errors) and how long the code took to execute. If the code has errors, the specific lines are highlighted directly in the editor.

**Why this priority**: This is the core action the entire feature is built around. Without the ability to write and execute code with visible feedback, no other capability in this feature has meaning.

**Independent Test**: A student opens the Playground, types `print("hello")`, clicks Run, and sees "hello" in the output panel — fully testable without any AI, submission, or lesson context.

**Acceptance Scenarios**:

1. **Given** the editor is open with code that prints output, **When** the student clicks Run, **Then** the output panel shows stdout, stderr (if any), and execution time within 5 seconds.
2. **Given** the student's code has a syntax error on line 4, **When** the student clicks Run, **Then** line 4 is visually highlighted in the editor and the error message appears in the output panel.
3. **Given** the code takes longer than 5 seconds, **When** execution times out, **Then** the output panel shows a timeout message and the editor returns to a ready state.
4. **Given** the student is on a lesson page, **When** the editor loads, **Then** it displays the starter code provided by the lesson (not a blank editor).
5. **Given** the editor is open with no code, **When** the student clicks Run, **Then** a clear message is shown rather than a cryptic execution error.

---

### User Story 2 - Get AI Feedback on Code (Priority: P2)

After writing code, a student clicks "Review with Tutor". The AI analyses the code and responds directly in a conversation section below the editor — styled to match the editor's appearance with a visible boundary line separating it from the code. The student can type follow-up questions in that same section to continue the conversation specifically about their code.

**Why this priority**: The AI feedback loop is the core differentiator of the platform — it turns a basic editor into a tutoring experience. It must be available once the core editor works.

**Independent Test**: A student writes a function, clicks "Review with Tutor", sees a loading indicator in the code feedback section, and within seconds receives structured AI feedback — testable without lesson context or submission.

**Acceptance Scenarios**:

1. **Given** the student has written code and clicks "Review with Tutor", **When** the AI is processing, **Then** a loading indicator appears in the code feedback section below the editor.
2. **Given** the AI responds, **When** the response arrives, **Then** it appears in the code feedback section styled to match the editor (monospace, dark background, separated by a visible boundary line).
3. **Given** the AI has responded, **When** the student types a follow-up question in the code feedback section, **Then** the AI responds in the same section, maintaining conversation context about the current code.
4. **Given** the student's code produced an execution error, **When** the AI reviews it, **Then** the feedback specifically references the error and the relevant line number.
5. **Given** the AI tutor service is unavailable, **When** the student clicks "Review with Tutor", **Then** a user-friendly error message appears in the code feedback section; the editor and Run button remain fully functional.

---

### User Story 3 - General Tutor Chat Panel (Priority: P2)

The student can open a collapsible tutor panel on the right side of the editor for general Python questions unrelated to the specific code they are writing — concept questions, clarifications, or learning context. This panel is a separate conversation channel from the code-specific feedback section below the editor.

**Why this priority**: Students often have conceptual questions while coding that are not directly about the code in front of them. Keeping general and code-specific conversations separate prevents context confusion and mirrors how real tutoring works.

**Independent Test**: A student opens the Playground, expands the right tutor panel, asks "what is a list comprehension?", and receives a general explanation — testable independently of any code execution or review.

**Acceptance Scenarios**:

1. **Given** the editor is open, **When** the student clicks the toggle button, **Then** the right tutor panel expands; clicking again collapses it.
2. **Given** the tutor panel is open, **When** the student sends a general Python question, **Then** the AI responds conversationally in the panel without referencing the code in the editor unless the student explicitly shares it.
3. **Given** the tutor panel is collapsed, **When** the student interacts with the code feedback section below the editor, **Then** those messages do not appear in the right panel and vice versa.
4. **Given** the tutor panel is open on a narrow viewport, **When** the student collapses it, **Then** the editor area expands to fill the available space.

---

### User Story 4 - Submit a Graded Exercise (Priority: P3)

When the editor is embedded in a graded lesson exercise, a Submit button appears alongside Run. The student writes their solution and clicks Submit to have it evaluated against test cases. They receive a graded result indicating whether their code passed.

**Why this priority**: Submission enables measurable progress and mastery scoring, which powers the platform's core learning loop. It applies only in lesson context so it does not affect the standalone Playground.

**Independent Test**: A student on a lesson exercise page writes code satisfying the exercise requirements, clicks Submit, and sees a pass/fail result with feedback — testable within any graded lesson without Playground or general chat.

**Acceptance Scenarios**:

1. **Given** the editor is in embedded mode for a graded exercise, **When** the editor loads, **Then** a Submit button appears alongside the Run button.
2. **Given** the editor is in standalone Playground mode, **When** the editor loads, **Then** no Submit button is visible.
3. **Given** the student clicks Submit, **When** the submission is being evaluated, **Then** the Submit button shows a loading state and is disabled to prevent double-submission.
4. **Given** the submission is evaluated, **When** the result arrives, **Then** the output panel shows whether the solution passed or failed, with details on any failing test cases.
5. **Given** the student's code contains an infinite loop, **When** they submit, **Then** the execution times out after 5 seconds, the submission is marked as failed, and a clear timeout message is shown.

---

### User Story 5 - Code Auto-Save and Persistence (Priority: P3)

The student's code is automatically saved as they type so they never lose their work if the browser closes or they navigate away. Their code is also saved to their account so they can return to it from any device.

**Why this priority**: Losing written code is a significant source of frustration for learners. Auto-save removes this risk with no manual effort required.

**Independent Test**: A student writes code in the Playground, closes the browser, reopens it, navigates to the Playground, and finds their code exactly as they left it — testable without any AI or submission features.

**Acceptance Scenarios**:

1. **Given** the student is typing code, **When** they pause for 5 seconds, **Then** the code is silently saved to local storage with no visible interruption to the editing experience.
2. **Given** the student runs, submits, or requests a review, **When** that action is triggered, **Then** the current code state is also saved to their account on the backend.
3. **Given** the student returns to the Playground on a different device, **When** the editor loads, **Then** their last saved code appears automatically.
4. **Given** the editor is in lesson mode, **When** the student returns to the same lesson later, **Then** their last code for that lesson is restored — not the original starter code.
5. **Given** Playground code and lesson code exist for the same student, **When** either editor loads, **Then** each surfaces only its own saved code; they never overwrite each other.

---

### Edge Cases

- What happens if the student navigates away mid-review while the AI is responding? The in-progress request is cancelled gracefully; no partial response is displayed.
- What happens when the editor is embedded in a lesson but no starter code is provided? The editor opens blank rather than failing.
- What happens when local storage is full or unavailable? The system falls back to backend-only persistence and silently skips local storage without blocking the student.
- What happens if the backend save fails during auto-save? The failure is silently retried; the student is not interrupted, but if repeated failures occur a subtle indicator is shown.
- What happens if the same Playground is open in two browser tabs and both save concurrently? Last-write-wins; whichever tab's save request lands last becomes the stored version. No conflict UI is shown.
- What happens when the tutor panel is open on a narrow viewport (below 1024px)? The panel is collapsed by default on narrow screens to preserve editor space.

---

## Requirements *(mandatory)*

### Functional Requirements

**Editor Core**

- **FR-001**: The system MUST provide a code editing area using **Monaco Editor** with Python syntax highlighting, line numbers, bracket matching, and auto-indentation.
- **FR-002**: The system MUST provide a Run button that executes the student's code and displays stdout, stderr, and execution time in a dedicated output panel below the editor. The frontend sends a synchronous POST request to the execution endpoint and awaits the response (no client-side polling).
- **FR-003**: The system MUST enforce a 5-second execution timeout; code exceeding this limit must be terminated and the student notified with a clear timeout message.
- **FR-004**: The system MUST parse execution error output to extract line numbers and highlight the corresponding lines visually in the editor.
- **FR-005**: The editor MUST support two modes controlled by external configuration: standalone (Playground — no lesson context, blank starting code, no Submit button) and embedded (lesson page — receives lesson/exercise context, starter code, and optional graded mode).
- **FR-006**: The Playground (standalone editor) MUST be accessible via a link in the main navigation bar for authenticated students.

**Code Persistence**

- **FR-007**: The system MUST auto-save the student's code to local storage after 5 seconds of inactivity (debounced), with no visible disruption to the editing experience.
- **FR-008**: The system MUST save the student's code to their backend account whenever they click Run, Submit, or Review with Tutor.
- **FR-009**: The system MUST restore the student's last saved code when they return to the same editor context (Playground or a specific lesson exercise).
- **FR-010**: Playground code and lesson-specific code MUST be stored independently and MUST NOT overwrite each other.

**Rate Limiting**

- **FR-025**: The backend MUST enforce a limit of 3 code execution (Run) requests per student per calendar day; requests exceeding this limit MUST return HTTP 429 with a user-friendly message displayed in the output panel.
- **FR-026**: The backend MUST enforce a limit of 3 "Review with Tutor" AI requests per student per calendar day; requests exceeding this limit MUST return HTTP 429 with a user-friendly message displayed in the code feedback section.
- **FR-027**: The Run button and "Review with Tutor" button MUST be disabled on the client while their respective requests are in-flight to prevent duplicate submissions.

**AI Code Feedback**

- **FR-011**: The system MUST provide a "Review with Tutor" button that sends the current code (and any active execution error) to the AI for analysis.
- **FR-012**: The system MUST display a loading indicator in the code feedback section while the AI is generating a response.
- **FR-013**: AI feedback MUST appear in a dedicated section directly below the code area, visually separated by a boundary line and styled to match the editor (monospace font, consistent color scheme).
- **FR-014**: The student MUST be able to type follow-up messages in the code feedback section to continue an AI conversation about their specific code.
- **FR-015**: The code feedback conversation MUST retain context across multiple exchanges within the same session (the AI sees prior messages in the thread).
- **FR-016**: If the AI service is unavailable, the system MUST display a user-friendly error in the code feedback section without affecting the editor or Run functionality.

**General Tutor Panel**

- **FR-017**: The system MUST provide a collapsible tutor panel on the right side of the editor for general Python questions.
- **FR-018**: The right tutor panel MUST function as a conversation channel fully independent from the code feedback section; messages in one MUST NOT appear in or affect the other.
- **FR-019**: The tutor panel's collapsed/expanded state MUST persist for the duration of the session.
- **FR-020**: On viewports narrower than 1024px, the tutor panel MUST default to collapsed.

**Graded Submission**

- **FR-021**: When in graded exercise mode, a Submit button MUST be visible alongside the Run button.
- **FR-022**: The Submit button MUST NOT appear in standalone Playground mode.
- **FR-023**: The system MUST disable the Submit button and show a loading state while a submission is being evaluated to prevent duplicate submissions.
- **FR-024**: The system MUST display graded results (pass/fail, failing test case details) in the output panel upon submission completion.

---

### Key Entities

- **Code Session**: Represents a student's current editing context. Attributes: student identity (`user_id`), `context_key` (value `"playground"` for standalone mode, or the exercise/lesson ID for embedded mode), current code content, last saved timestamp. The composite key `(user_id, context_key)` uniquely identifies a code slot in the backend.
- **Execution Result**: Represents the outcome of a single code run. Attributes: stdout, stderr, execution time, timeout flag, parsed error line numbers (if any), timestamp.
- **Code Submission**: Represents a graded exercise submission. Attributes: student identity, exercise reference, submitted code, pass/fail result, failing test case details, timestamp.
- **Code Feedback Conversation**: The AI conversation thread tied to a specific code session. Attributes: ordered messages (student and AI turns), code snapshot at time of each review request, execution error context at time of request.
- **General Tutor Conversation**: The AI conversation in the right panel. Attributes: ordered messages (student and AI turns), session reference. Fully independent of the code feedback conversation.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Students can open the editor, write code, and see execution results within 5 seconds of clicking Run in 99% of cases under normal load.
- **SC-002**: Students never lose more than 5 seconds of typed code due to browser crash or accidental navigation.
- **SC-003**: AI code feedback appears within 10 seconds of clicking "Review with Tutor" in 90% of cases.
- **SC-004**: Error line highlighting correctly identifies the highlighted line for 95% of standard Python execution errors.
- **SC-005**: Students can complete a graded exercise from opening the editor to receiving a submission result in under 2 minutes.
- **SC-006**: The editor is fully functional on screens as narrow as 1024px width when the tutor panel is collapsed.
- **SC-007**: Auto-save operates with zero perceptible impact on editor typing responsiveness.

---

## Clarifications

### Session 2026-05-10

- Q: How should the frontend communicate with the code execution sandbox and AI agents — REST polling, SSE, or WebSocket? → A: REST, synchronous (no polling); frontend POSTs and awaits the response directly.
- Q: How should a student's saved code be uniquely keyed in the backend for persistence? → A: Composite key `(user_id, context_key)` where context_key is `"playground"` for standalone mode or the exercise/lesson ID for embedded mode.
- Q: Should Run and "Review with Tutor" be rate-limited per student? → A: Both; backend enforces a hard limit of 3 requests per day per student (HTTP 429 if exceeded) and the button is disabled while a request is in-flight on the client.
- Q: Is Monaco Editor confirmed as the code editing component? → A: Confirmed; Monaco Editor is the required library.
- Q: If the same Playground is open in two tabs and both save concurrently, which version wins? → A: Last-write-wins; no conflict UI required.

---

## Assumptions

- The Python code execution sandbox (F05) is already deployed and accessible; this feature does not re-implement execution logic.
- The Code Review Agent (F09) and Debug Agent (F10) are available and callable; this feature only surfaces their responses in the code feedback section.
- The general tutor panel reuses the chat component built for F15; this feature does not re-implement general conversation infrastructure.
- Lesson starter code and exercise grading test cases are provided by the lesson/exercise system (F11/F16); this feature receives them as configuration and does not generate them.
- Authentication is handled upstream; the editor always has access to a valid authenticated student identity for persistence and submission.
- Standard library-only import enforcement is handled by the sandbox; the editor does not need to validate imports.
