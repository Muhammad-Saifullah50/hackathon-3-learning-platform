"""Pydantic schemas for the dashboard feature (F017)."""

from typing import Literal, Optional
from pydantic import BaseModel


class MasterySnapshot(BaseModel):
    day: str        # ISO date "YYYY-MM-DD"
    avg_score: float


class MasteryHistoryResponse(BaseModel):
    snapshots: list[MasterySnapshot]


class RecommendationItem(BaseModel):
    text: str
    module_slug: Optional[str] = None


class TopicProgressItem(BaseModel):
    topic: str
    status: Literal["covered", "partial", "remaining"]
    note: Optional[str] = None


# F019: Teacher analytics schemas

class ModuleMasteryItem(BaseModel):
    module_slug: str
    module_name: str
    avg_score: float


class StrugglingStudent(BaseModel):
    student_id: str
    display_name: str
    score: float
    module_slug: str
    topic_label: str


class TeacherAnalyticsResponse(BaseModel):
    total_students: int
    avg_mastery: Optional[float]
    low_quiz_count: int
    module_mastery: list[ModuleMasteryItem]
    struggling_students: list[StrugglingStudent]
