"""Blinded review and annotation services for Phase 3."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from app.database import connect, init_db
from app.evaluator_models import (
    AnnotationRequest,
    AnnotationResponse,
    BlindedEvaluationView,
    BlindedReviewResponse,
)
from app.evaluator_runner import EvaluatorRunner


class BlindedReviewService:
    def __init__(self, evaluator_runner: EvaluatorRunner | None = None) -> None:
        self.evaluator_runner = evaluator_runner or EvaluatorRunner()
        init_db()

    def create_review(
        self,
        *,
        transcript_id: str,
        reviewer_id: str,
        evaluation_ids: list[str],
    ) -> BlindedReviewResponse:
        if len(evaluation_ids) != 2:
            raise ValueError("Exactly two evaluation IDs are required for A/B blinded review")

        # Deterministic but condition-hidden order: sort IDs so tests are stable.
        labels = ["Evaluation A", "Evaluation B"]
        ordered = sorted(evaluation_ids)
        with connect() as conn:
            for label, evaluation_id in zip(labels, ordered):
                evaluation = conn.execute(
                    "SELECT * FROM evaluation_runs WHERE evaluation_id = ?", (evaluation_id,)
                ).fetchone()
                if not evaluation:
                    raise KeyError(f"Unknown evaluation_id: {evaluation_id}")
                conn.execute(
                    """
                    INSERT OR REPLACE INTO blinding_mappings
                    (mapping_id, transcript_id, reviewer_id, display_label, actual_condition,
                     evaluation_id, revealed)
                    VALUES (?, ?, ?, ?, ?, ?, 0)
                    """,
                    (
                        f"blind_{transcript_id}_{reviewer_id}_{label.replace(' ', '_')}",
                        transcript_id,
                        reviewer_id,
                        label,
                        evaluation["evaluator_condition"],
                        evaluation_id,
                    ),
                )
            conn.commit()
        return self.get_review(transcript_id=transcript_id, reviewer_id=reviewer_id)

    def get_review(self, *, transcript_id: str, reviewer_id: str) -> BlindedReviewResponse:
        with connect() as conn:
            mappings = conn.execute(
                """
                SELECT * FROM blinding_mappings
                WHERE transcript_id = ? AND reviewer_id = ?
                ORDER BY display_label ASC
                """,
                (transcript_id, reviewer_id),
            ).fetchall()
        views = []
        for mapping in mappings:
            views.append(
                BlindedEvaluationView(
                    display_label=mapping["display_label"],
                    evaluation_id=mapping["evaluation_id"],
                    feedback_items=self.evaluator_runner.get_feedback_items(mapping["evaluation_id"]),
                )
            )
        return BlindedReviewResponse(
            transcript_id=transcript_id,
            reviewer_id=reviewer_id,
            blinded_evaluations=views,
        )

    def reveal_mapping(self, *, transcript_id: str, reviewer_id: str) -> list[dict[str, str]]:
        with connect() as conn:
            conn.execute(
                "UPDATE blinding_mappings SET revealed = 1 WHERE transcript_id = ? AND reviewer_id = ?",
                (transcript_id, reviewer_id),
            )
            rows = conn.execute(
                """
                SELECT display_label, actual_condition, evaluation_id
                FROM blinding_mappings
                WHERE transcript_id = ? AND reviewer_id = ?
                ORDER BY display_label ASC
                """,
                (transcript_id, reviewer_id),
            ).fetchall()
            conn.commit()
        return [dict(row) for row in rows]


class AnnotationService:
    def __init__(self) -> None:
        init_db()

    def save_annotation(self, request: AnnotationRequest) -> AnnotationResponse:
        annotation_id = f"ann_{uuid4().hex[:12]}"
        with connect() as conn:
            conn.execute(
                """
                INSERT INTO human_annotations
                (annotation_id, reviewer_id, evaluation_id, feedback_item_id, blinded_label,
                 criterion, ai_score, human_score, accept, fabricated_evidence,
                 unsupported_inference, pedagogical_disagreement, missed_issue, usefulness,
                 review_time_seconds, comment, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    annotation_id,
                    request.reviewer_id,
                    request.evaluation_id,
                    request.feedback_item_id,
                    request.blinded_label,
                    request.criterion,
                    request.ai_score,
                    request.human_score,
                    int(request.accept),
                    int(request.fabricated_evidence),
                    int(request.unsupported_inference),
                    int(request.pedagogical_disagreement),
                    int(request.missed_issue),
                    request.usefulness,
                    request.review_time_seconds,
                    request.comment,
                    datetime.now(timezone.utc).isoformat(),
                ),
            )
            conn.commit()
        return AnnotationResponse(annotation_id=annotation_id)
