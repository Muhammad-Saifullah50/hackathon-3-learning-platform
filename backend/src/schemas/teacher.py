"""Teacher-facing Pydantic schemas for F18 Teacher Dashboard."""

import uuid
from typing import Optional
from pydantic import BaseModel, Field


# --- Class schemas ---

class ClassCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)


class ClassResponse(BaseModel):
    id: uuid.UUID
    name: str
    teacher_id: uuid.UUID
    member_count: int = 0

    model_config = {"from_attributes": True}


class ClassMember(BaseModel):
    student_id: uuid.UUID
    display_name: str
    email: str
    status: str

    model_config = {"from_attributes": True}


class ClassDetail(BaseModel):
    id: uuid.UUID
    name: str
    teacher_id: uuid.UUID
    members: list[ClassMember] = []

    model_config = {"from_attributes": True}


# --- Student search ---

class StudentSearchResult(BaseModel):
    id: uuid.UUID
    display_name: str
    email: str

    model_config = {"from_attributes": True}


# --- Invitation ---

class InviteStudentRequest(BaseModel):
    student_id: uuid.UUID


# --- Exercise schemas ---

class ExerciseQuestion(BaseModel):
    index: int
    description: str
    starter_code: str


class TeacherExercise(BaseModel):
    id: uuid.UUID
    title: str
    topic: str
    difficulty: str
    target_module: str
    questions: list[ExerciseQuestion]

    model_config = {"from_attributes": True}


class ExerciseGenerateRequest(BaseModel):
    prompt: str = Field(..., min_length=10, max_length=2000)


class GuardrailRejection(BaseModel):
    code: str
    message: str
    missing: list[str] = []


class AssignExerciseRequest(BaseModel):
    class_id: uuid.UUID


class AssignResponse(BaseModel):
    class_exercise_id: uuid.UUID
    assigned_to_count: int
    warning: Optional[str] = None
