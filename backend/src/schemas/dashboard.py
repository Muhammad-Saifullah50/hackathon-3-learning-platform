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
