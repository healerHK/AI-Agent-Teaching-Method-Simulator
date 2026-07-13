"""Runtime models for Phase 2 interactive classroom sessions."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class StudentPersona(BaseModel):
    persona_id: str
    name: str
    display_role: str
    learning_profile: str
    misconception_bias: str
    avatar_variant: str


class ClassroomTurn(BaseModel):
    turn_id: str
    speaker_role: Literal["teacher", "student", "controller"]
    speaker_name: str
    persona_id: str | None = None
    message: str
    turn_index: int


class SessionState(BaseModel):
    session_id: str
    scenario_id: str
    lesson_title: str
    learning_objective: str
    current_teacher_turn: int = 0
    max_teacher_turns: int = 12
    status: Literal["active", "completed"] = "active"
    turns: list[ClassroomTurn] = Field(default_factory=list)


class StartSessionRequest(BaseModel):
    scenario_id: str = "python_loops_001"
    max_teacher_turns: int = 12


class StartSessionResponse(BaseModel):
    session: SessionState
    personas: list[StudentPersona]


class TeacherTurnRequest(BaseModel):
    teacher_message: str = Field(min_length=1)


class TeacherTurnResponse(BaseModel):
    teacher_turn: ClassroomTurn
    student_turns: list[ClassroomTurn]
    session_state: SessionState
    response_source: Literal["openai", "fallback"]
