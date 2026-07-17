"""Metrics for Phase 4 MVP benchmark analysis."""

from __future__ import annotations

from collections import defaultdict
from statistics import mean
from typing import Any

from app.benchmark_loader import GoldenBenchmarkLoader
from app.database import connect


class MetricsService:
    def __init__(self, loader: GoldenBenchmarkLoader | None = None) -> None:
        self.loader = loader or GoldenBenchmarkLoader()

    def compute_experiment_metrics(self, experiment_id: str) -> dict[str, Any]:
        with connect() as conn:
            evaluations = conn.execute(
                "SELECT * FROM evaluation_runs WHERE experiment_id = ? ORDER BY evaluator_condition",
                (experiment_id,),
            ).fetchall()
        by_condition: dict[str, dict[str, Any]] = defaultdict(
            lambda: {
                "evaluation_count": 0,
                "feedback_count": 0,
                "verified_count": 0,
                "missing_evidence_count": 0,
                "invalid_evidence_count": 0,
                "absolute_errors": [],
            }
        )

        for evaluation in evaluations:
            condition = evaluation["evaluator_condition"]
            expected_scores = self.loader.load_expected_scores(evaluation["transcript_id"]).scores
            by_condition[condition]["evaluation_count"] += 1
            with connect() as conn:
                feedback_rows = conn.execute(
                    "SELECT * FROM feedback_items WHERE evaluation_id = ?",
                    (evaluation["evaluation_id"],),
                ).fetchall()
            for feedback in feedback_rows:
                by_condition[condition]["feedback_count"] += 1
                expected = expected_scores.get(feedback["criterion"])
                if expected is not None and feedback["score"] is not None:
                    by_condition[condition]["absolute_errors"].append(abs(int(feedback["score"]) - expected))
                status = feedback["verification_status"]
                if status == "verified":
                    by_condition[condition]["verified_count"] += 1
                elif status == "missing_evidence":
                    by_condition[condition]["missing_evidence_count"] += 1
                elif status:
                    by_condition[condition]["invalid_evidence_count"] += 1

        summary: dict[str, Any] = {"experiment_id": experiment_id, "conditions": {}}
        for condition, values in by_condition.items():
            abs_errors = values.pop("absolute_errors")
            feedback_count = values["feedback_count"] or 1
            summary["conditions"][condition] = {
                **values,
                "mean_absolute_error": round(mean(abs_errors), 4) if abs_errors else None,
                "verified_rate": round(values["verified_count"] / feedback_count, 4),
                "missing_evidence_rate": round(values["missing_evidence_count"] / feedback_count, 4),
                "invalid_evidence_rate": round(values["invalid_evidence_count"] / feedback_count, 4),
            }
        return summary
