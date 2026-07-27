"""PixelClass TIL v2 research MVP models.

These models expose the refined thesis direction:
- simulation/live mode is a testbed;
- transcript benchmark mode is the controlled comparison;
- evidence-grounded, expert-aligned evaluation is the main contribution.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from app.evaluator_models import BlindedReviewResponse, VerificationRunResponse
from app.models import BenchmarkTranscript
from app.session_models import ClassroomTurn, SessionState, StudentPersona


class LessonPhase(BaseModel):
    phase_id: str
    title: str
    minute_range: str
    teacher_goal: str
    expected_student_behaviours: list[str]
    evidence_focus: list[str]


class StudentBehaviourMechanism(BaseModel):
    mechanism: Literal["memory_stream", "retrieval", "reflection", "planning", "state_update"]
    source: str
    implementation_signal: str
    thesis_claim: str


class ScenarioSpec(BaseModel):
    scenario_id: str
    title: str
    mode: Literal["live_micro_lesson_and_transcript_benchmark"]
    estimated_duration_minutes: int = Field(ge=1)
    subject_domain: str
    education_level: str
    learning_objective: str
    core_misconceptions: list[str]
    lesson_phases: list[LessonPhase]
    virtual_student_behaviour_claim: str
    student_behaviour_architecture: list[StudentBehaviourMechanism]
    planned_benchmark_variants: list[str]
    available_transcript_ids: list[str]
    claim_guardrails: list[str]


class MetricDefinition(BaseModel):
    metric_id: str
    label: str
    formula: str
    interpretation: str


class ReviewProtocol(BaseModel):
    reviewer_role: str
    blinding: str
    rating_dimensions: list[str]
    metrics: list[MetricDefinition]


class ThesisPositioning(BaseModel):
    title: str
    research_gap: str
    contribution: str
    safe_claim: str


class ScenarioListResponse(BaseModel):
    thesis_positioning: ThesisPositioning
    scenarios: list[ScenarioSpec]
    review_protocol: ReviewProtocol


class LiveSessionStartRequest(BaseModel):
    scenario_id: str = "python_loops_full_lesson_001"
    max_teacher_turns: int = Field(default=8, ge=1, le=30)


class LiveSessionStartResponse(BaseModel):
    scenario: ScenarioSpec
    session: SessionState
    personas: list[StudentPersona]
    protocol_notes: list[str]


class LiveTeacherTurnRequest(BaseModel):
    teacher_message: str = Field(min_length=1)


class LiveTeacherTurnResponse(BaseModel):
    teacher_turn: ClassroomTurn
    student_turns: list[ClassroomTurn]
    session_state: SessionState
    response_source: str
    current_phase: LessonPhase
    protocol_notes: list[str]


class TranscriptBenchmarkRunRequest(BaseModel):
    transcript_id: str = "python_loops_weak_001"
    reviewer_id: str = "expert_reviewer_mvp"


class ReviewMetricsSummary(BaseModel):
    reviewer_id: str
    annotations_count: int
    expert_acceptance_rate: float
    correction_rate: float
    rejection_rate: float
    evidence_validity_rate: float
    unsupported_inference_rate: float
    usefulness_mean: float | None
    metrics_definition: list[MetricDefinition]


class TranscriptBenchmarkRunResponse(BaseModel):
    thesis_positioning: ThesisPositioning
    transcript_id: str
    transcript: BenchmarkTranscript
    scenario: ScenarioSpec
    benchmark_protocol: dict[str, object]
    baseline_evaluation_id: str
    til_evaluation_id: str
    baseline_verification: VerificationRunResponse
    til_verification: VerificationRunResponse
    blinded_review: BlindedReviewResponse
    review_metrics: ReviewMetricsSummary
    claim_guardrails: list[str]
