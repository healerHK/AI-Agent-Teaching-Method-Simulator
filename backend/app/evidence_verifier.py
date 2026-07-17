"""Deterministic evidence verifier for Phase 3."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from uuid import uuid4

from app.benchmark_loader import GoldenBenchmarkLoader
from app.config import REQUIRED_RUBRIC_CRITERIA, VERIFIER_VERSION
from app.database import connect, init_db
from app.evaluator_models import VerificationItemResult, VerificationRunResponse


def _norm(text: str) -> str:
    return " ".join(text.lower().split())


class EvidenceVerifier:
    def __init__(self, loader: GoldenBenchmarkLoader | None = None) -> None:
        self.loader = loader or GoldenBenchmarkLoader()
        init_db()

    def verify_evaluation(self, evaluation_id: str) -> VerificationRunResponse:
        with connect() as conn:
            evaluation = conn.execute(
                "SELECT * FROM evaluation_runs WHERE evaluation_id = ?", (evaluation_id,)
            ).fetchone()
            if not evaluation:
                raise KeyError(f"Unknown evaluation_id: {evaluation_id}")
            feedback_rows = conn.execute(
                "SELECT * FROM feedback_items WHERE evaluation_id = ? ORDER BY feedback_item_id ASC",
                (evaluation_id,),
            ).fetchall()

        transcript = self.loader.load_transcript(evaluation["transcript_id"])
        turns = transcript.turn_map()
        results: list[VerificationItemResult] = []

        for row in feedback_rows:
            with connect() as conn:
                evidence_rows = conn.execute(
                    "SELECT * FROM evidence_links WHERE feedback_item_id = ? ORDER BY evidence_link_id ASC",
                    (row["feedback_item_id"],),
                ).fetchall()
            result = self._verify_item(row, evidence_rows, turns)
            results.append(result)
            with connect() as conn:
                conn.execute(
                    "UPDATE feedback_items SET verification_status = ? WHERE feedback_item_id = ?",
                    (result.status, row["feedback_item_id"]),
                )
                conn.commit()

        overall = "verified" if all(item.status == "verified" for item in results) else "unsupported"
        response = VerificationRunResponse(
            evaluation_id=evaluation_id,
            verifier_version=VERIFIER_VERSION,
            overall_status=overall,
            items=results,
        )
        self._store_verification_result(evaluation_id, response)
        return response

    def _verify_item(self, row, evidence_rows, turns) -> VerificationItemResult:
        problems: list[str] = []
        status = "verified"

        if row["criterion"] not in REQUIRED_RUBRIC_CRITERIA:
            problems.append("criterion is not in rubric")
            status = "invalid_criterion"
        if row["score"] is None or not 1 <= int(row["score"]) <= 5:
            problems.append("score must be between 1 and 5")
            status = "invalid_score"
        if not evidence_rows:
            problems.append("feedback item has no evidence links")
            status = "missing_evidence"

        for evidence in evidence_rows:
            turn_id = evidence["turn_id"]
            quote = evidence["evidence_quote"]
            if turn_id not in turns:
                problems.append(f"turn_id not found: {turn_id}")
                status = "turn_id_not_found"
                continue
            if not quote.strip():
                problems.append(f"empty quote for {turn_id}")
                status = "missing_evidence"
                continue
            if _norm(quote) not in _norm(turns[turn_id].message):
                problems.append(f"quote not found in {turn_id}")
                status = "quote_not_found"

        return VerificationItemResult(
            feedback_item_id=row["feedback_item_id"],
            criterion=row["criterion"],
            claim=row["claim"],
            status=status,
            problems=problems,
        )

    def _store_verification_result(self, evaluation_id: str, response: VerificationRunResponse) -> None:
        with connect() as conn:
            conn.execute(
                """
                INSERT INTO verification_results
                (verification_id, evaluation_id, verifier_version, status, details_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    f"ver_{uuid4().hex[:12]}",
                    evaluation_id,
                    response.verifier_version,
                    response.overall_status,
                    json.dumps(response.model_dump(), ensure_ascii=False),
                    datetime.now(timezone.utc).isoformat(),
                ),
            )
            conn.commit()
