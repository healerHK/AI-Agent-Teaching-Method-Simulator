"""Models for Phase 3 evaluator, verification, and blinded review workflow."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

Criterion = Literal[
    "pck_conceptual_accuracy",
    "scaffolding",
    "formative_assessment",
    "cognitive_questioning",
    "missed_pedagogical_opportunity",
]
EvaluatorCondition = Literal["baseline", "til"]
VerificationStatus = Literal[
    "verified",
    "missing_evidence",
    "quote_not_found",
    "turn_id_not_found",
    "speaker_mismatch",
    "invalid_score",
    "invalid_criterion",
    "unsupported",
]


class FeedbackItemOutput(BaseModel):
    criterion: Criterion
    claim: str = Field(min_length=1)
    score: int = Field(ge=1, le=5)
    evidence_turn_ids: list[str] = Field(default_factory=list)
    evidence_quotes: list[str] = Field(default_factory=list)
    suggested_action: str = ""
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)


class EvaluationOutput(BaseModel):
    transcript_id: str
    condition: EvaluatorCondition
    summary: str
    feedback_items: list[FeedbackItemOutput]
    response_source: Literal["openai", "anthropic", "gemini", "openai_compatible", "fallback"] = "fallback"


class RunEvaluationRequest(BaseModel):
    transcript_id: str = "python_loops_weak_001"
    condition: EvaluatorCondition = "til"


class RunEvaluationResponse(BaseModel):
    evaluation_id: str
    experiment_id: str
    transcript_id: str
    condition: EvaluatorCondition
    output: EvaluationOutput


class EvidenceLinkView(BaseModel):
    turn_id: str
    evidence_quote: str


class FeedbackItemView(BaseModel):
    feedback_item_id: str
    criterion: str
    claim: str
    score: int | None = None
    suggested_action: str | None = None
    confidence: float | None = None
    verification_status: str | None = None
    evidence: list[EvidenceLinkView] = Field(default_factory=list)


class VerificationItemResult(BaseModel):
    feedback_item_id: str | None = None
    criterion: str
    claim: str
    status: VerificationStatus
    problems: list[str] = Field(default_factory=list)


class VerificationRunResponse(BaseModel):
    evaluation_id: str
    verifier_version: str
    overall_status: VerificationStatus
    items: list[VerificationItemResult]


class CreateBlindedReviewRequest(BaseModel):
    transcript_id: str = "python_loops_weak_001"
    reviewer_id: str = "researcher_phase3"
    evaluation_ids: list[str] | None = None


class BlindedEvaluationView(BaseModel):
    display_label: Literal["Evaluation A", "Evaluation B"]
    evaluation_id: str
    feedback_items: list[FeedbackItemView]


class BlindedReviewResponse(BaseModel):
    transcript_id: str
    reviewer_id: str
    blinded_evaluations: list[BlindedEvaluationView]


class Phase3DemoRequest(BaseModel):
    transcript_id: str = "python_loops_weak_001"
    reviewer_id: str = "researcher_phase3"


class Phase3DemoResponse(BaseModel):
    transcript_id: str
    baseline_evaluation_id: str
    til_evaluation_id: str
    baseline_verification: VerificationRunResponse
    til_verification: VerificationRunResponse
    blinded_review: BlindedReviewResponse


class AnnotationRequest(BaseModel):
    reviewer_id: str = "researcher_phase3"
    evaluation_id: str
    feedback_item_id: str | None = None
    blinded_label: str
    criterion: str
    ai_score: int | None = None
    human_score: int | None = Field(default=None, ge=1, le=5)
    accept: bool = True
    fabricated_evidence: bool = False
    unsupported_inference: bool = False
    pedagogical_disagreement: bool = False
    missed_issue: bool = False
    usefulness: int | None = Field(default=None, ge=1, le=5)
    review_time_seconds: int | None = None
    comment: str | None = None


class AnnotationResponse(BaseModel):
    annotation_id: str
    saved: bool = True
