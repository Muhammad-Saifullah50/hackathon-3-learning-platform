import uuid
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class CodeExecutionRequest(BaseModel):
    """Request schema for code execution."""

    code: str = Field(
        ..., min_length=1, max_length=10000, description="Python code to execute"
    )
    module_id: Optional[str] = Field(
        None, description="Optional ID of the curriculum module this code relates to"
    )
    lesson_id: Optional[str] = Field(
        None, description="Optional ID of the lesson this code relates to"
    )
    exercise_id: Optional[str] = Field(
        None, description="Optional ID of the exercise this code is a solution for"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "code": "print('Hello, World!')\nresult = 2 + 2\nprint(f'Result: {result}')",
                "module_id": "123e4567-e89b-12d3-a456-426614174000",
                "lesson_id": "123e4567-e89b-12d3-a456-426614174001",
                "exercise_id": "123e4567-e89b-12d3-a456-426614174002",
            }
        }


class CodeExecutionResponse(BaseModel):
    """Response schema for code execution."""

    id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique identifier for this execution attempt",
    )
    status: str = Field(
        ...,
        description="Execution result status",
        pattern="^(success|timeout|error|blocked|infrastructure_failure)$",
    )
    execution_time_ms: int = Field(
        ..., ge=0, description="Time taken for execution in milliseconds"
    )
    output: Optional[str] = Field(
        None, description="Program output captured during execution"
    )
    error_message: Optional[str] = Field(
        None, description="Student-friendly error message if execution failed"
    )
    error_type: Optional[str] = Field(
        None, description="Classification of error (e.g., SyntaxError, NameError)"
    )
    error_line: Optional[int] = Field(
        None, description="Line number of the error, parsed from stderr (for editor highlighting)"
    )
    memory_used_bytes: Optional[int] = Field(
        None, description="Peak memory usage during execution in bytes"
    )
    code_submission_id: Optional[str] = Field(
        None,
        description="ID of stored code submission (only for successful executions)",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "status": "success",
                "execution_time_ms": 12,
                "output": "Hello, World!\nResult: 4",
                "memory_used_bytes": 24576,
            }
        }


class ValidationErrorItem(BaseModel):
    """Schema for individual validation error items."""

    field: str = Field(..., description="Field that failed validation")
    message: str = Field(..., description="Validation error message")


class ValidationErrorResponse(BaseModel):
    """Schema for validation error responses."""

    error: str = Field("validation_error", description="Error type")
    message: str = Field(..., description="Human-readable error message")
    details: list[ValidationErrorItem] = Field(
        ..., description="List of validation error details"
    )


class CodeExecutionErrorResponse(BaseModel):
    """Schema for code execution error responses."""

    error: str = Field(
        ...,
        description="Error type",
        pattern="^(execution_error|timeout_error|security_violation)$",
    )
    message: str = Field(..., description="Student-friendly error message")
    status: str = Field(
        ...,
        description="Execution status",
        pattern="^(timeout|error|blocked|infrastructure_failure)$",
    )
    execution_time_ms: int = Field(
        ..., description="Time taken before termination in milliseconds"
    )
    allowed_modules: Optional[list[str]] = Field(
        None,
        description="List of allowed standard library modules (for security violations)",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "error": "security_violation",
                "message": "Import blocked for security: 'os' module is restricted. Use allowed modules like 'math', 'json', 'datetime' instead.",
                "status": "blocked",
                "execution_time_ms": 8,
                "allowed_modules": ["math", "json", "datetime", "random"],
            }
        }


class InternalServerErrorResponse(BaseModel):
    """Schema for internal server error responses."""

    error: str = Field("internal_server_error", description="Error type")
    message: str = Field(..., description="Error message suggesting retry")
