# Research: Quiz System (F16)

**Branch**: `016-quiz-system` | **Date**: 2026-05-17
**Source**: Codebase analysis of F07 (agent layer), F15 (AI tutor chat), F02 (DB schema), constitution

---

## Research Questions & Resolutions

### R1 — Quiz intent detection in triage

**Question**: How should "quiz" intent be separated from "exercise-generation" in the triage classifier?

**Finding**: The existing `INTENT_PATTERNS["exercise-generation"]` already has `r"\bquiz\s+me\b"` and `r"\bquiz\s+me\s+on\b"`. However, "give me a quiz" (bare noun, no "me") is not covered. The new `quiz-generation` intent needs its own patterns focused on the quiz UI flow, not just exercise generation.

**Decision**: Add a new `"quiz-generation"` intent to `INTENT_PATTERNS` with patterns:
- `r"\bgive me a quiz\b"`, `r"\bquiz\b"`, `r"\btest my knowledge\b"`, `r"\bflashcard(s)?\b"`, `r"\bquick quiz\b"`, `r"\bchallenge me\b"` (if not covered by exercise)

Map `"quiz-generation"` → `"quiz"` in `INTENT_TO_AGENT`. The quiz agent is selected before the exercise agent when these patterns match.

**Alternatives considered**:
- Reuse exercise-generation intent and have the exercise agent return a quiz structure → Rejected: breaks the discriminated-union pattern and conflates exercise (coding challenge) with quiz (MCQ+flashcard).
- Dedicated triage agent handoff via SDK handoffs → Rejected: adds overhead; keyword routing is deterministic and already proven for all other intents.

---

### R2 — QuizResponse structured output schema

**Question**: What fields must `QuizResponse` carry to support all frontend requirements?

**Finding**: The spec requires:
- 3 MCQs: each with `question`, `options` (list of 4), `correct_index` (0-3)
- 3 flashcards: each with `term`, `definition` (sent at generation time for flip reveal)
- `module_slug`: one of the 8 curriculum slugs (constrained in agent prompt)
- `quiz_session_id`: must be set server-side (not by agent) — the agent does not know the DB ID

**Decision**:
```python
class MCQQuestion(BaseModel):
    question: str
    options: list[str]          # exactly 4
    correct_index: int          # 0-3

class FlashcardQuestion(BaseModel):
    term: str
    definition: str

class QuizResponse(BaseModel):
    response_type: Literal["quiz"] = "quiz"
    module_slug: str            # one of 8 constrained slugs
    topic_label: str            # human-readable topic for display
    mcq_questions: list[MCQQuestion]      # len == 3
    flashcard_questions: list[FlashcardQuestion]  # len == 3
    quiz_session_id: Optional[str] = None  # injected server-side after DB write
```

The `quiz_session_id` is `None` in the agent output; the chat endpoint populates it after creating the `quiz_sessions` row and injects it into the SSE payload.

**Alternatives considered**:
- Include `quiz_session_id` in agent output → Rejected: agent has no DB access.
- Use a flat `questions` list with a `type` discriminator → Rejected: harder to render in order (MCQ first, then flashcard); separate lists preserve ordering intent.

---

### R3 — Flashcard AI grading approach

**Question**: Should flashcard grading use the OpenAI Agents SDK or a direct LLM call?

**Finding**: The existing `LlmClient` (src/llm/client.py) wraps LiteLLM with caching. The SDK `Runner.run()` adds overhead (session context, handoff scaffolding) unsuitable for a simple classification call. The spec requires < 5 s P95.

**Decision**: Use a direct async call via `LlmClient.complete()` (or equivalent structured call) with a dedicated grading prompt from `src/llm/prompts.py`. The grading endpoint calls this directly — no SDK overhead.

Grading output schema:
```python
class FlashcardGrade(BaseModel):
    grade: Literal["Correct", "Partial", "Wrong"]
    feedback: str   # one sentence
```

**Alternatives considered**:
- SDK Agent with `output_type=FlashcardGrade` → Rejected: ~300-500 ms SDK overhead per call; overkill for a classify-and-score task.
- Rule-based string matching → Rejected: too brittle for open-ended student answers; defeats the purpose of AI grading.

---

### R4 — Quiz session persistence and JSONB structure

**Question**: What JSONB structure best supports the resume flow and score computation?

**Finding**: The mastery/exercise models (agent_exercise.py) use JSONB for `test_cases` and `component_breakdown`. The same pattern applies.

**Decision**:

```json
// questions (immutable after creation)
[
  {"type": "mcq", "question": "...", "options": ["A","B","C","D"], "correct_index": 2},
  {"type": "mcq", "question": "...", "options": ["A","B","C","D"], "correct_index": 0},
  {"type": "mcq", "question": "...", "options": ["A","B","C","D"], "correct_index": 1},
  {"type": "flashcard", "term": "...", "definition": "..."},
  {"type": "flashcard", "term": "...", "definition": "..."},
  {"type": "flashcard", "term": "...", "definition": "..."}
]

// student_answers (keyed by card index 0-5, null until answered)
{"0": 2, "1": null, "2": 1, "3": "list comprehension is...", "4": null, "5": null}

// grades (keyed by card index 0-5, null until graded; MCQ graded client-side but stored on submit)
{"0": "correct", "1": null, "2": "wrong", "3": "Partial", "4": null, "5": null}
```

MCQ grades are submitted client-side along with the flashcard answers in the `POST /submit` body. Only flashcard grades are written via `POST /grade-flashcard`.

**Alternatives considered**:
- Normalized `quiz_answers` table → Rejected: over-engineered for this scale; JSONB is simpler and sufficient.
- Store MCQ correct answers separately from questions → Rejected: spec sends correct answers to client at generation time (for immediate feedback); already in `questions` JSONB.

---

### R5 — Mastery update strategy (most-recent quiz score)

**Question**: How should the existing `MasteryRepository.update_mastery()` be called with quiz data?

**Finding**: `update_mastery()` takes `score`, `level`, `component_breakdown`. The spec says mastery uses the **most-recent** completed quiz score for a module (not highest/average). The existing `component_breakdown` stores `"quizzes": 0.0`. The full mastery score is recomputed on each update.

**Decision**:
```python
# After quiz submit:
raw_quiz_score = compute_raw_score(answers, grades, questions)  # 0.0 to 1.0
quiz_component = round(raw_quiz_score * 100, 1)  # 0.0 to 100.0

# get_or_create existing record, then recompute:
existing = await mastery_repo.get_or_create_mastery(user_id, module_slug)
breakdown = existing.component_breakdown.copy()
breakdown["quizzes"] = quiz_component
if "quizzes" in breakdown.get("missing_components", []):
    breakdown["missing_components"].remove("quizzes")

new_score = (
    breakdown.get("exercises", 0.0) * 0.4 +
    breakdown["quizzes"] * 0.3 +
    breakdown.get("code_quality", 0.0) * 0.2 +
    breakdown.get("streak", 0.0) * 0.1
)
new_level = compute_level(new_score)
await mastery_repo.update_mastery(user_id, module_slug, new_score, new_level, breakdown)
```

Scoring: MCQ = 1 pt (correct) / 0 pt (wrong); Flashcard = 1 (Correct) / 0.5 (Partial) / 0 (Wrong). Max = 6. Map to 0-100: `(raw_score / 6) * 100`.

**Alternatives considered**:
- Highest score strategy → Rejected: spec mandates most-recent.
- Average of all attempts → Rejected: spec mandates most-recent.

---

### R6 — Frontend quiz state machine

**Question**: How should the frontend manage the sequential card flow and resume state?

**Finding**: The `useStreamChat` hook already manages SSE events and structured output. A new `useQuizSession` hook manages the per-quiz state.

**Decision**: `useQuizSession` maintains:
```ts
type QuizPhase = 'mcq' | 'flashcard' | 'summary'
interface QuizState {
  sessionId: string
  questions: QuizQuestion[]        // 3 MCQ + 3 flashcard
  currentCardIndex: number          // 0-5
  answers: Record<number, unknown>  // MCQ: option index; Flashcard: typed string
  grades: Record<number, FlashcardGradeResult | 'correct' | 'wrong'>
  phase: QuizPhase
  score: number | null
}
```
On resume: state is hydrated from `GET /api/v1/quiz/{session_id}` response. Already-answered cards are rendered in locked state; `currentCardIndex` is set to first unanswered card.

**Alternatives considered**:
- Zustand global store → Rejected: quiz state is local to a single chat message; hook scope is sufficient.
- Redux → Rejected: no Redux in this project.

---

### R7 — Card flip animation approach

**Question**: CSS-only vs library (framer-motion, react-spring) for flashcard flip?

**Finding**: The project has no animation library installed. The frontend uses Tailwind CSS. Card flip with CSS 3D transform is a well-established, zero-dependency approach.

**Decision**: CSS 3D transform with Tailwind utility classes + inline styles for `perspective` and `rotateY`. The flip triggers on "Check" click after answer submission and grade receipt.

```tsx
// FlashCard inner container toggled between:
style={{ transform: isFlipped ? 'rotateY(180deg)' : 'rotateY(0deg)', transition: 'transform 0.5s' }}
```

**Alternatives considered**:
- Framer Motion → Rejected: unnecessary dependency; CSS transform is sufficient.
- No flip (just reveal definition inline) → Rejected: spec explicitly requires card flip.

---

## Summary of All Decisions

| # | Decision | Choice |
|---|----------|--------|
| R1 | Quiz intent detection | New `quiz-generation` intent with dedicated patterns |
| R2 | QuizResponse schema | Separate `mcq_questions` + `flashcard_questions` lists; `quiz_session_id` injected server-side |
| R3 | Flashcard grading | Direct `LlmClient` async call, not SDK Agent |
| R4 | Session persistence | JSONB `questions`/`student_answers`/`grades` on single row |
| R5 | Mastery update | Most-recent score; recompute full mastery on each quiz submit |
| R6 | Frontend state | `useQuizSession` hook with phase-based state machine |
| R7 | Card flip animation | CSS 3D transform + Tailwind |
