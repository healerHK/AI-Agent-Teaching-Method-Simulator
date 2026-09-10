"""Models for the transcript-first scenario system.

This module is deliberately separate from Live Mode. It supports editable 30-minute
classroom scenarios, student prompt parameters, draft transcript scripts, and
readiness testing before any live classroom simulation is built.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator

EducationLevel = Literal["high_school", "college", "university"]
SpeakerRole = Literal["teacher", "student", "controller"]
CheckStatus = Literal["pass", "warn", "fail"]


class StudentPromptParameters(BaseModel):
    participation_style: str = Field(min_length=1)
    confidence: float = Field(ge=0.0, le=1.0)
    misconception_strength: float = Field(ge=0.0, le=1.0)
    prior_knowledge: str = Field(min_length=1)
    affect: str = Field(min_length=1)
    response_length: Literal["short", "medium", "long"] = "medium"
    language_level: str = Field(min_length=1)
    prompt_instructions: str = Field(min_length=1)


class StudentPromptProfile(BaseModel):
    student_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    role: str = Field(min_length=1)
    background: str = Field(min_length=1)
    learning_needs: list[str] = Field(default_factory=list)
    parameters: StudentPromptParameters


class LessonPhaseDraft(BaseModel):
    phase_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    minute_start: int = Field(ge=0, le=30)
    minute_end: int = Field(ge=0, le=30)
    teacher_goal: str = Field(min_length=1)
    expected_student_events: list[str] = Field(default_factory=list)
    evidence_focus: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_phase_times(self) -> "LessonPhaseDraft":
        if self.minute_end <= self.minute_start:
            raise ValueError("minute_end must be greater than minute_start")
        return self


class TranscriptTurnDraft(BaseModel):
    turn_id: str = Field(min_length=1)
    minute: int = Field(ge=0, le=30)
    speaker_role: SpeakerRole
    speaker_name: str = Field(min_length=1)
    message: str = Field(min_length=1)
    student_id: str | None = None
    pedagogical_tags: list[str] = Field(default_factory=list)


class TranscriptScenario(BaseModel):
    scenario_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    subject: str = Field(min_length=1)
    education_level: EducationLevel
    course_context: str = Field(min_length=1)
    estimated_duration_minutes: int = Field(default=30, ge=1, le=120)
    learning_objectives: list[str] = Field(min_length=1)
    prerequisite_knowledge: list[str] = Field(default_factory=list)
    misconception_targets: list[str] = Field(default_factory=list)
    materials_needed: list[str] = Field(default_factory=list)
    lesson_phases: list[LessonPhaseDraft] = Field(min_length=1)
    student_profiles: list[StudentPromptProfile] = Field(min_length=1)
    transcript_turns: list[TranscriptTurnDraft] = Field(min_length=1)
    teacher_prompt_template: str = Field(min_length=1)
    student_prompt_template: str = Field(min_length=1)
    evaluator_focus: list[str] = Field(default_factory=list)
    editable_notes: str = ""

    @model_validator(mode="after")
    def validate_unique_ids(self) -> "TranscriptScenario":
        student_ids = [student.student_id for student in self.student_profiles]
        if len(student_ids) != len(set(student_ids)):
            raise ValueError("student_id values must be unique")
        turn_ids = [turn.turn_id for turn in self.transcript_turns]
        if len(turn_ids) != len(set(turn_ids)):
            raise ValueError("turn_id values must be unique")
        valid_students = set(student_ids)
        for turn in self.transcript_turns:
            if turn.speaker_role == "student" and not turn.student_id:
                raise ValueError(f"student turn {turn.turn_id} must include student_id")
            if turn.student_id and turn.student_id not in valid_students:
                raise ValueError(f"unknown student_id in turn {turn.turn_id}: {turn.student_id}")
        return self


class TranscriptScenarioSummary(BaseModel):
    scenario_id: str
    title: str
    subject: str
    education_level: EducationLevel
    estimated_duration_minutes: int
    student_count: int
    turn_count: int
    misconception_count: int


class TranscriptScenarioListResponse(BaseModel):
    scenarios: list[TranscriptScenarioSummary]
    library_summary: dict[str, object]


class RenderedStudentPrompt(BaseModel):
    student_id: str
    name: str
    role: str
    prompt: str


class ScenarioValidationCheck(BaseModel):
    check_id: str
    status: CheckStatus
    message: str


class TranscriptScenarioTestResponse(BaseModel):
    scenario_id: str
    passed: bool
    checks: list[ScenarioValidationCheck]
    rendered_student_prompts: list[RenderedStudentPrompt]
    transcript_preview_markdown: str
    next_steps: list[str]


class TranscriptScenarioSaveResponse(BaseModel):
    scenario_id: str
    saved: bool = True
    path: str
