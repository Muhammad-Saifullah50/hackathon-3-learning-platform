"""Triage intent classification utility.

Deterministic keyword/regex-based intent classification used by the
triage agent's handoff descriptions and routing hooks.
"""

import re
from dataclasses import dataclass, field

OFF_TOPIC_PATTERNS: list[str] = [
    r"\bpoem\b",
    r"\brecipe\b",
    r"\bcook(ing)?\b",
    r"\bweather\b",
    r"\bsport(s)?\b",
    r"\bfootball\b",
    r"\bbasketball\b",
    r"\bsoccer\b",
    r"\bhistory\b",
    r"\bgeograph(y|ical)\b",
    r"\bmovie\b",
    r"\bmusic\b",
    r"\bsong\b",
    r"\bpolitics\b",
    r"\bfrance\b",
    r"\bwar\b",
    r"\bocean\b",
    r"\bwrite me a\b(?!.*python)",
    r"\btell me about\b(?!.*python)",
    r"\bjoke\b",
    r"\bhoroscope\b",
]

PYTHON_ANCHOR_PATTERNS: list[str] = [
    r"\bpython\b",
    r"\bcode\b",
    r"\bprogram\b",
    r"\bfunction\b",
    r"\bvariable\b",
    r"\bloop\b",
    r"\bclass\b",
    r"\bimport\b",
    r"\bdef\b",
]

INTENT_PATTERNS: dict[str, list[str]] = {
    "quiz-generation": [
        r"\bgive\s+me\s+a\s+quiz\b",
        r"\bquiz\b",
        r"\btest\s+my\s+knowledge\b",
        r"\bflashcard(s)?\b",
        r"\bquick\s+quiz\b",
        r"\bchallenge\s+me\b",
    ],
    "concept-explanation": [
        r"\bwhat\s+is\b",
        r"\bexplain\b",
        r"\bhow\s+does\b",
        r"\bwhat\s+are\b",
        r"\bwhat\s+do\b",
        r"\bdefine\b",
        r"\bmeaning\s+of\b",
        r"\bunderstand\b",
        r"\bconcept\b",
        r"\bhow\s+do\b",
        r"\bwhat\s+does\b",
    ],
    "code-debug": [
        r"\berror\b",
        r"error\b",
        r"\bbug\b",
        r"\bwhy\s+doesn'?t\b",
        r"\bnot\s+working\b",
        r"\btraceback\b",
        r"\bexception\b",
        r"\bfix\b",
        r"\bbroken\b",
        r"\bfail(ed)?\b",
        r"\bwrong\s+output\b",
        r"\bdoesn'?t\s+work\b",
    ],
    "code-review": [
        r"\breview\b",
        r"\bimprove\b",
        r"\bbetter\s+way\b",
        r"\bclean\s+code\b",
        r"\brefactor\b",
        r"\boptimize\b",
        r"\bstyle\b",
        r"\bpep\s*8\b",
        r"\breadability\b",
        r"\bcode\s+quality\b",
    ],
    "exercise-generation": [
        r"\bexercise\b",
        r"\bpractice\b",
        r"\bchallenge\b",
        r"\btest\s+me\b",
        r"\bquiz\s+me\b",
        r"\bgive\s+me\s+(a\s+)?(problem|exercise|challenge|task)\b",
        r"\bgive\s+me\s+(some\s+)?(practice|exercises)\b",
        r"\bi\s+want\s+to\s+practice\b",
        r"\bcoding\s+(challenge|problem|exercise)\b",
        r"\bpractice\s+exercise\b",
        r"\bgive\s+me\s+a\s+problem\b",
        r"\bquiz\s+me\s+on\b",
        r"\bsomething\s+to\s+practice\b",
    ],
    "progress-summary": [
        r"\bprogress\b",
        r"\bhow\s+am\s+i\s+doing\b",
        r"\bmastery\b",
        r"\bstreak\b",
        r"\bscore\b",
        r"\bhow\s+far\b",
        r"\bwhere\s+am\s+i\b",
        r"\bmy\s+progress\b",
        r"\blevel\b",
    ],
}

INTENT_TO_AGENT: dict[str, str] = {
    "quiz-generation": "quiz",
    "concept-explanation": "concepts",
    "code-debug": "debug",
    "code-review": "code_review",
    "exercise-generation": "exercise",
    "progress-summary": "progress",
    "off_topic": "none",
    "general": "triage",
}


@dataclass
class TriageResult:
    """Result of intent classification."""

    intent: str
    confidence: float
    matched_patterns: list[str] = field(default_factory=list)


def _is_off_topic(message: str) -> bool:
    """Return True if message is clearly off-topic (non-Python) with no Python anchor."""
    compiled_off = [re.compile(p, re.IGNORECASE) for p in OFF_TOPIC_PATTERNS]
    compiled_anchor = [re.compile(p, re.IGNORECASE) for p in PYTHON_ANCHOR_PATTERNS]

    has_off_topic = any(p.search(message) for p in compiled_off)
    has_python_anchor = any(p.search(message) for p in compiled_anchor)

    return has_off_topic and not has_python_anchor


def classify_intent(message: str) -> TriageResult:
    """Classify a student message into an intent category.

    Args:
        message: The student's message text.

    Returns:
        TriageResult with intent, confidence, and matched patterns.
    """
    if _is_off_topic(message):
        return TriageResult(intent="off_topic", confidence=0.95, matched_patterns=[])

    compiled = {
        intent: [re.compile(p, re.IGNORECASE) for p in patterns]
        for intent, patterns in INTENT_PATTERNS.items()
    }

    best_intent = "general"
    best_confidence = 0.0
    best_matched: list[str] = []

    for intent, patterns in compiled.items():
        matched = [p.pattern for p in patterns if p.search(message)]
        if not matched:
            continue

        confidence = min(len(matched) / len(patterns), 0.95)
        if confidence > best_confidence:
            best_intent = intent
            best_confidence = confidence
            best_matched = matched

    if best_confidence < 0.07:
        return TriageResult(intent="general", confidence=0.0)

    return TriageResult(
        intent=best_intent,
        confidence=best_confidence,
        matched_patterns=best_matched,
    )


def get_agent_for_intent(intent: str) -> str:
    """Map intent to agent name."""
    return INTENT_TO_AGENT.get(intent, "triage")
