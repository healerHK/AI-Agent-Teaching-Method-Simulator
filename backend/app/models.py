"""Pydantic models for Phase 1 golden benchmark validation."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from app.config import REQUIRED_RUBRIC_CRITERIA


class Turn(BaseModel):
    turn_id: str = Field(min_length=1)
    speaker_role: Literal["teacher", "student", "controller", "evaluator"]
    speaker_name: str = Field(min_length=1)
    message: str = Field(min_length=1)


class Scenario(BaseModel):
    scenario_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    domain: str = Field(min_length=1)
    education_level: str = Field(min_length=1)
    learning_objective: str = Field(min_length=1)
    common_misconceptions: list[str] = Field(default_factory=list)
    target_concepts: list[str] = Field(default_factory=list)


class BenchmarkTranscript(BaseModel):
    transcript_id: str = Field(min_length=1)
    scenario_id: str = Field(min_length=1)
    variant: Literal["strong", "weak"]
    domain: str = Field(min_length=1)
    education_level: str = Field(min_length=1)
    learning_objective: str = Field(min_length=1)
    turns: list[Turn] = Field(min_length=1)

    @model_validator(mode="after")
    def ensure_unique_turn_ids(self) -> "BenchmarkTranscript":
        turn_ids = [turn.turn_id for turn in self.turns]
        if len(turn_ids) != len(set(turn_ids)):
            raise ValueError("turn_id values must be unique within a transcript")
        return self

    def turn_map(self) -> dict[str, Turn]:
        return {turn.turn_id: turn for turn in self.turns}


class GroundTruth(BaseModel):
    transcript_id: str = Field(min_length=1)
    rubric_version: str = Field(min_length=1)
    created_by: str = Field(min_length=1)
    review_status: Literal[
        "draft",
        "expert_reviewed",
        "adjudicated",
        "researcher_annotated",
        "human_validated_with_domain_flags",
    ]
    summary: str = Field(min_length=1)
    known_issues: list[str] = Field(default_factory=list)


class ExpectedScores(BaseModel):
    transcript_id: str = Field(min_length=1)
    scores: dict[str, int]
    score_scale: Literal["1-5"] = "1-5"
    notes: dict[str, str] = Field(default_factory=dict)

    @field_validator("scores")
    @classmethod
    def validate_scores(cls, scores: dict[str, int]) -> dict[str, int]:
        expected = REQUIRED_RUBRIC_CRITERIA
        missing = expected - set(scores)
        extra = set(scores) - expected
        if missing:
            raise ValueError(f"missing rubric scores: {sorted(missing)}")
        if extra:
            raise ValueError(f"unknown rubric scores: {sorted(extra)}")
        for criterion, score in scores.items():
            if not 1 <= score <= 5:
                raise ValueError(f"score for {criterion} must be between 1 and 5")
        return scores


class MissedOpportunity(BaseModel):
    id: str = Field(min_length=1)
    criterion: Literal["missed_pedagogical_opportunity"]
    description: str = Field(min_length=1)
    evidence_turn_ids: list[str] = Field(min_length=1)
    expected_action: str = Field(min_length=1)


class ExpectedMissedOpportunities(BaseModel):
    transcript_id: str = Field(min_length=1)
    missed_opportunities: list[MissedOpportunity] = Field(default_factory=list)


class DatasetVersion(BaseModel):
    dataset_version: str = Field(min_length=1)
    created_at: str = Field(min_length=1)
    description: str = Field(min_length=1)
    scenario_count: int = Field(ge=1)
    transcript_count: int = Field(ge=1)
    rubric_version: str = Field(min_length=1)


class ReproducibilityManifest(BaseModel):
    experiment_id: str = Field(min_length=1)
    dataset_version: str = Field(min_length=1)
    transcript_id: str = Field(min_length=1)
    scenario_id: str = Field(min_length=1)
    evaluator_condition: Literal["baseline", "til"]
    prompt_version: str = Field(min_length=1)
    rubric_version: str = Field(min_length=1)
    openai_model: str = Field(min_length=1)
    temperature: float = Field(ge=0)
    seed: int | None = None
    git_commit_hash: str = Field(min_length=1)
    code_dirty: bool
    started_at: str = Field(min_length=1)
    completed_at: str = Field(min_length=1)
    raw_response_path: str = Field(min_length=1)
