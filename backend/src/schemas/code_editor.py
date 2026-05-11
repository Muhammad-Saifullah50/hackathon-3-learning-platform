"""Pydantic schemas for code editor endpoints."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class SaveCodeRequest(BaseModel):
    code: str = Field(..., max_length=100000)


class CodeSessionResponse(BaseModel):
    context_key: str
    code: str
    updated_at: datetime

    model_config = {"from_attributes": True}


class RateLimitErrorResponse(BaseModel):
    error: str = "rate_limit_exceeded"
    message: str
    retry_after: str
