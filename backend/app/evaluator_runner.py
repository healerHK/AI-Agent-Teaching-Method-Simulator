"""Phase 3 evaluator runner.

Runs baseline or TIL evaluator on golden benchmark transcripts, stores raw outputs,
feedback items, and evidence links for verification/blinded review.
"""

from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from app.benchmark_loader import GoldenBenchmarkLoader
from app.config import BACKEND_ROOT, DATA_ROOT, RUBRIC_VERSION
from app.database import connect, init_db
from app.evaluator_models import (
    EvaluationOutput,
    EvaluatorCondition,
    FeedbackItemOutput,
    FeedbackItemView,
    EvidenceLinkView,
)
from app.llm_provider import LLMProviderClient, evaluator_provider_config
from app.models import BenchmarkTranscript

PROMPT_FILES = {
    "baseline": BACKEND_ROOT / "prompts" / "baseline" / "v1.txt",
    "til": BACKEND_ROOT / "prompts" / "evaluators" / "til_v1.txt",
}
PROMPT_VERSIONS = {
    "baseline": "baseline_v1",
    "til": "til_evaluator_v1",
}


class EvaluatorRunner:
    def __init__(self, loader: GoldenBenchmarkLoader | None = None) -> None:
        self.loader = loader or GoldenBenchmarkLoader()
        init_db()

    def run(
        self,
        *,
        transcript_id: str,
        condition: EvaluatorCondition,
        experiment_id: str | None = None,
    ) -> tuple[str, str, EvaluationOutput]:
        transcript = self.loader.load_transcript(transcript_id)
        experiment_id = experiment_id or _new_experiment_id()
        evaluation_id = f"eval_{uuid4().hex[:12]}"
        provider_config = evaluator_provider_config(condition)
        started_at = _now()

        output = self._generate_output(transcript=transcript, condition=condition)
        output.response_source = provider_config.provider
        model_name = provider_config.model_label
        error_message = None
        status = "success"

        if provider_config.provider != "fallback":
            try:
                output = self._generate_provider_output(
                    transcript=transcript,
                    condition=condition,
                    provider_config=provider_config,
                )
                model_name = provider_config.model_label
            except Exception as exc:  # keep pipeline runnable across provider config experiments
                error_message = _provider_error_summary(exc)
                output = self._generate_output(transcript=transcript, condition=condition)
                output.response_source = "fallback"
                model_name = f"{provider_config.provider}:{provider_config.model}->fallback"
                status = "success_with_provider_fallback"

        raw_path = self._write_raw_output(experiment_id, evaluation_id, output, provider_config.provider)
        completed_at = _now()
        self._store_evaluation(
            evaluation_id=evaluation_id,
            experiment_id=experiment_id,
            transcript=transcript,
            condition=condition,
            model_name=model_name,
            prompt_version=PROMPT_VERSIONS[condition],
            temperature=provider_config.temperature,
            started_at=started_at,
            completed_at=completed_at,
            raw_response_path=raw_path,
            status=status,
            error_message=error_message,
            output=output,
        )
        return evaluation_id, experiment_id, output

    def get_feedback_items(self, evaluation_id: str) -> list[FeedbackItemView]:
        with connect() as conn:
            rows = conn.execute(
                "SELECT * FROM feedback_items WHERE evaluation_id = ? ORDER BY feedback_item_id ASC",
                (evaluation_id,),
            ).fetchall()
            views: list[FeedbackItemView] = []
            for row in rows:
                evidence_rows = conn.execute(
                    "SELECT * FROM evidence_links WHERE feedback_item_id = ? ORDER BY evidence_link_id ASC",
                    (row["feedback_item_id"],),
                ).fetchall()
                views.append(
                    FeedbackItemView(
                        feedback_item_id=row["feedback_item_id"],
                        criterion=row["criterion"],
                        claim=row["claim"],
                        score=row["score"],
                        suggested_action=row["suggested_action"],
                        confidence=row["confidence"],
                        verification_status=row["verification_status"],
                        evidence=[
                            EvidenceLinkView(
                                turn_id=evidence["turn_id"],
                                evidence_quote=evidence["evidence_quote"],
                            )
                            for evidence in evidence_rows
                        ],
                    )
                )
        return views

    def _generate_provider_output(self, *, transcript: BenchmarkTranscript, condition: EvaluatorCondition, provider_config) -> EvaluationOutput:
        system_prompt = PROMPT_FILES[condition].read_text(encoding="utf-8")
        user_prompt = _transcript_prompt(transcript)
        client = LLMProviderClient(provider_config)
        data = client.complete_json(system_prompt=system_prompt, user_prompt=user_prompt)
        feedback_items = [FeedbackItemOutput.model_validate(item) for item in data.get("feedback_items", [])]
        return EvaluationOutput(
            transcript_id=transcript.transcript_id,
            condition=condition,
            summary=data.get("summary", ""),
            feedback_items=feedback_items,
            response_source=provider_config.provider,
        )

    def _generate_output(self, *, transcript: BenchmarkTranscript, condition: EvaluatorCondition) -> EvaluationOutput:
        if condition == "baseline":
            return self._fallback_baseline(transcript)
        return self._fallback_til(transcript)

    def _fallback_baseline(self, transcript: BenchmarkTranscript) -> EvaluationOutput:
        if transcript.variant == "weak":
            items = [
                FeedbackItemOutput(
                    criterion="scaffolding",
                    claim="The teacher could give clearer step-by-step support before moving on.",
                    score=2,
                    evidence_turn_ids=[],
                    evidence_quotes=[],
                    suggested_action="Use a simple trace table before introducing while-loops.",
                    confidence=0.58,
                ),
                FeedbackItemOutput(
                    criterion="formative_assessment",
                    claim="The teacher should check whether students understand the loop output.",
                    score=2,
                    evidence_turn_ids=[],
                    evidence_quotes=[],
                    suggested_action="Ask students to explain why the output is 1, 2, 3.",
                    confidence=0.55,
                ),
            ]
            summary = "Generic feedback: the teacher should slow down, check understanding, and use a clearer example."
        else:
            items = [
                FeedbackItemOutput(
                    criterion="scaffolding",
                    claim="The teacher uses a helpful trace-based explanation.",
                    score=4,
                    evidence_turn_ids=[],
                    evidence_quotes=[],
                    suggested_action="Continue asking students to predict loop values before running code.",
                    confidence=0.62,
                )
            ]
            summary = "Generic feedback: the teacher explains the loop reasonably well and can continue checking understanding."
        return EvaluationOutput(
            transcript_id=transcript.transcript_id,
            condition="baseline",
            summary=summary,
            feedback_items=items,
            response_source="fallback",
        )

    def _fallback_til(self, transcript: BenchmarkTranscript) -> EvaluationOutput:
        turns = transcript.turn_map()
        if transcript.variant == "weak":
            items = [
                FeedbackItemOutput(
                    criterion="pck_conceptual_accuracy",
                    claim="The teacher does not directly correct Mia's misconception that one written print line means one execution.",
                    score=2,
                    evidence_turn_ids=["turn_002", "turn_003"],
                    evidence_quotes=[turns["turn_002"].message, turns["turn_003"].message],
                    suggested_action="Ask Mia to trace each list item and connect each item to one execution of print(number).",
                    confidence=0.86,
                ),
                FeedbackItemOutput(
                    criterion="scaffolding",
                    claim="The teacher misses Sam's need for stepwise tracing of the loop variable.",
                    score=1,
                    evidence_turn_ids=["turn_004", "turn_005"],
                    evidence_quotes=[turns["turn_004"].message, turns["turn_005"].message],
                    suggested_action="Create a two-column trace table with iteration number and value of number.",
                    confidence=0.88,
                ),
                FeedbackItemOutput(
                    criterion="missed_pedagogical_opportunity",
                    claim="The teacher rejects Lina's request to trace the loop and moves on too quickly.",
                    score=1,
                    evidence_turn_ids=["turn_008", "turn_009"],
                    evidence_quotes=[turns["turn_008"].message, turns["turn_009"].message],
                    suggested_action="Pause the topic shift and model one trace before asking students to finish the remaining iterations.",
                    confidence=0.91,
                ),
            ]
            summary = "TIL feedback: the main issues are missed misconception repair, weak scaffolding, and missed trace opportunities."
        else:
            items = [
                FeedbackItemOutput(
                    criterion="pck_conceptual_accuracy",
                    claim="The teacher accurately addresses the misconception that a print line written once only executes once.",
                    score=5,
                    evidence_turn_ids=["turn_003", "turn_004"],
                    evidence_quotes=[turns["turn_003"].message, turns["turn_004"].message],
                    suggested_action="Keep eliciting misconceptions before formal explanation.",
                    confidence=0.89,
                ),
                FeedbackItemOutput(
                    criterion="formative_assessment",
                    claim="The teacher checks student understanding after the explanation.",
                    score=4,
                    evidence_turn_ids=["turn_005", "turn_007", "turn_008"],
                    evidence_quotes=[turns["turn_005"].message, turns["turn_007"].message, turns["turn_008"].message],
                    suggested_action="Ask one additional transfer question with a different list length.",
                    confidence=0.82,
                ),
            ]
            summary = "TIL feedback: the teacher uses accurate misconception repair, trace scaffolding, and formative checks."
        return EvaluationOutput(
            transcript_id=transcript.transcript_id,
            condition="til",
            summary=summary,
            feedback_items=items,
            response_source="fallback",
        )

    def _write_raw_output(self, experiment_id: str, evaluation_id: str, output: EvaluationOutput, provider: str) -> str:
        root = DATA_ROOT / "raw_outputs" / experiment_id
        root.mkdir(parents=True, exist_ok=True)
        path = root / f"{evaluation_id}_{provider}.json"
        path.write_text(output.model_dump_json(indent=2), encoding="utf-8")
        return str(path)

    def _store_evaluation(
        self,
        *,
        evaluation_id: str,
        experiment_id: str,
        transcript: BenchmarkTranscript,
        condition: EvaluatorCondition,
        model_name: str,
        prompt_version: str,
        temperature: float,
        started_at: str,
        completed_at: str,
        raw_response_path: str,
        status: str,
        error_message: str | None,
        output: EvaluationOutput,
    ) -> None:
        with connect() as conn:
            conn.execute(
                """
                INSERT INTO evaluation_runs
                (evaluation_id, experiment_id, transcript_id, scenario_id, evaluator_condition,
                 model_name, prompt_version, rubric_version, temperature, seed, started_at,
                 completed_at, latency_ms, input_tokens, output_tokens, estimated_cost,
                 raw_response_path, status, error_message)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, ?, ?, NULL, NULL, NULL, NULL, ?, ?, ?)
                """,
                (
                    evaluation_id,
                    experiment_id,
                    transcript.transcript_id,
                    transcript.scenario_id,
                    condition,
                    model_name,
                    prompt_version,
                    RUBRIC_VERSION,
                    temperature,
                    started_at,
                    completed_at,
                    raw_response_path,
                    status,
                    error_message,
                ),
            )
            for item_index, item in enumerate(output.feedback_items, start=1):
                feedback_item_id = f"{evaluation_id}_item_{item_index:03d}"
                conn.execute(
                    """
                    INSERT INTO feedback_items
                    (feedback_item_id, evaluation_id, criterion, claim, score, suggested_action,
                     confidence, verification_status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, NULL)
                    """,
                    (
                        feedback_item_id,
                        evaluation_id,
                        item.criterion,
                        item.claim,
                        item.score,
                        item.suggested_action,
                        item.confidence,
                    ),
                )
                for evidence_index, (turn_id, quote) in enumerate(
                    zip(item.evidence_turn_ids, item.evidence_quotes), start=1
                ):
                    conn.execute(
                        """
                        INSERT INTO evidence_links
                        (evidence_link_id, feedback_item_id, turn_id, evidence_quote)
                        VALUES (?, ?, ?, ?)
                        """,
                        (
                            f"{feedback_item_id}_ev_{evidence_index:03d}",
                            feedback_item_id,
                            turn_id,
                            quote,
                        ),
                    )
            conn.commit()


def _transcript_prompt(transcript: BenchmarkTranscript) -> str:
    turns = "\n".join(f"{turn.turn_id} | {turn.speaker_name}: {turn.message}" for turn in transcript.turns)
    return f"""
Transcript ID: {transcript.transcript_id}
Scenario ID: {transcript.scenario_id}
Learning objective: {transcript.learning_objective}

Transcript:
{turns}
""".strip()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _new_experiment_id() -> str:
    return f"exp_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{uuid4().hex[:4]}"


def _provider_error_summary(exc: Exception) -> str:
    """Return a provider error summary without leaking API keys or request URLs."""

    response = getattr(exc, "response", None)
    status_code = getattr(response, "status_code", None)
    if status_code is not None:
        return f"provider_error_fallback_used: {exc.__class__.__name__} status={status_code}"
    return f"provider_error_fallback_used: {exc.__class__.__name__}"


def git_commit_hash() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=BACKEND_ROOT.parent).decode().strip()
    except Exception:
        return "unknown"
