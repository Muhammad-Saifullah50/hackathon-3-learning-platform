"""Models package - exports all SQLAlchemy models."""

from src.auth.models import EmailVerificationToken, PasswordResetToken, RateLimitCounter, Session
from src.models.agent_exercise import AgentExercise, AgentExerciseSubmission, MasteryRecord
from src.models.agent_session import AgentSession, HintProgression, RoutingDecision
from src.models.base import SoftDeleteMixin, TimestampMixin
from src.models.cache import LLMCache
from src.models.curriculum import Exercise, Lesson, Module, Quiz
from src.models.progress import UserExerciseProgress, UserModuleMastery, UserQuizAttempt
from src.models.code_session import CodeSession
from src.models.quiz_session import QuizSession
from src.models.submission import CodeSubmission
from src.models.user import User, UserProfile, UserStreak

__all__ = [
    # Base mixins
    "SoftDeleteMixin",
    "TimestampMixin",
    # User models
    "User",
    "UserProfile",
    "UserStreak",
    # Curriculum models
    "Module",
    "Lesson",
    "Exercise",
    "Quiz",
    # Progress models
    "UserExerciseProgress",
    "UserQuizAttempt",
    "UserModuleMastery",
    # Submission model
    "CodeSubmission",
    # Code session model
    "CodeSession",
    # Quiz session model
    "QuizSession",
    # Cache model
    "LLMCache",
    # Auth models
    "Session",
    "PasswordResetToken",
    "EmailVerificationToken",
    "RateLimitCounter",
    # Agent session models
    "AgentSession",
    "RoutingDecision",
    "HintProgression",
    # Agent exercise models
    "AgentExercise",
    "AgentExerciseSubmission",
    "MasteryRecord",
]
