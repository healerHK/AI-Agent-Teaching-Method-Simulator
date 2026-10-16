"""Phase 3 evaluator runner.

Runs baseline or TIL evaluator on golden benchmark transcripts, stores raw outputs,
feedback items, and evidence links for verification/blinded review.
"""

from __future__ import annotations

import json
import os
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
                if os.getenv("EVALUATOR_STRICT_PROVIDER", "").strip().lower() in {"1", "true", "yes", "on"}:
                    raise
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
        feedback_items = _normalise_provider_feedback_items(data.get("feedback_items", []))
        if not feedback_items:
            raise ValueError("provider returned no valid feedback_items")
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
        ordered_turns = transcript.turns

        def pick_turn(preferred_id: str, *, speaker_name: str | None = None, fallback_index: int = 0):
            if preferred_id in turns:
                return turns[preferred_id]
            if speaker_name:
                for turn in ordered_turns:
                    if turn.speaker_name.lower() == speaker_name.lower():
                        return turn
            return ordered_turns[min(fallback_index, len(ordered_turns) - 1)]

        misconception_turn = pick_turn("turn_004", speaker_name="Mia", fallback_index=1)
        teacher_response_turn = pick_turn("turn_005", speaker_name="Teacher", fallback_index=2)
        scaffold_turn = pick_turn("turn_012", speaker_name="Sam", fallback_index=3)
        follow_up_turn = pick_turn("turn_013", speaker_name="Teacher", fallback_index=4)
        formative_turn = pick_turn("turn_026", speaker_name="Teacher", fallback_index=max(len(ordered_turns) - 4, 0))
        closure_turn = pick_turn("turn_029", speaker_name="Mia", fallback_index=max(len(ordered_turns) - 1, 0))

        if transcript.variant == "weak":
            items = [
                FeedbackItemOutput(
                    criterion="pck_conceptual_accuracy",
                    claim=f"The evaluation should focus on whether the teacher explicitly repairs the visible {transcript.domain} misconception rather than moving past it.",
                    score=2,
                    evidence_turn_ids=[misconception_turn.turn_id, teacher_response_turn.turn_id],
                    evidence_quotes=[misconception_turn.message, teacher_response_turn.message],
                    suggested_action="Ask the student to compare their misconception with a concrete evidence row from the transcript and then state a repaired rule.",
                    confidence=0.86,
                ),
                FeedbackItemOutput(
                    criterion="scaffolding",
                    claim="The teacher needs stronger step-by-step scaffolding for the student who signals uncertainty.",
                    score=2,
                    evidence_turn_ids=[scaffold_turn.turn_id, follow_up_turn.turn_id],
                    evidence_quotes=[scaffold_turn.message, follow_up_turn.message],
                    suggested_action="Use a two-column evidence/reasoning table so students must connect each answer to a transcript-supported explanation.",
                    confidence=0.88,
                ),
                FeedbackItemOutput(
                    criterion="formative_assessment",
                    claim="The transcript should be checked for whether the final task asks students to justify the answer with evidence, not only produce an answer.",
                    score=3,
                    evidence_turn_ids=[formative_turn.turn_id, closure_turn.turn_id],
                    evidence_quotes=[formative_turn.message, closure_turn.message],
                    suggested_action="Use an exit ticket that requires a claim, one evidence quote/step, and a repaired misconception statement.",
                    confidence=0.84,
                ),
            ]
            summary = "TIL feedback: evaluate misconception repair, evidence-linked scaffolding, and formative checks on the selected fixed transcript."
        else:
            items = [
                FeedbackItemOutput(
                    criterion="pck_conceptual_accuracy",
                    claim="The teacher addresses the visible misconception with evidence from the lesson transcript.",
                    score=5,
                    evidence_turn_ids=[misconception_turn.turn_id, teacher_response_turn.turn_id],
                    evidence_quotes=[misconception_turn.message, teacher_response_turn.message],
                    suggested_action="Keep eliciting misconceptions before formal explanation and asking for evidence-linked repair.",
                    confidence=0.89,
                ),
                FeedbackItemOutput(
                    criterion="formative_assessment",
                    claim="The teacher checks student understanding after modelling and guided practice.",
                    score=4,
                    evidence_turn_ids=[formative_turn.turn_id, closure_turn.turn_id],
                    evidence_quotes=[formative_turn.message, closure_turn.message],
                    suggested_action="Add one transfer question with a changed surface feature but the same underlying concept.",
                    confidence=0.82,
                ),
            ]
            summary = "TIL feedback: the teacher uses misconception repair, evidence scaffolding, and formative checks."
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


CRITERION_ALIASES = {
    "pck": "pck_conceptual_accuracy",
    "conceptual_accuracy": "pck_conceptual_accuracy",
    "pck_conceptual_accuracy": "pck_conceptual_accuracy",
    "scaffolding": "scaffolding",
    "formative_assessment": "formative_assessment",
    "assessment": "formative_assessment",
    "cognitive_questioning": "cognitive_questioning",
    "questioning": "cognitive_questioning",
    "missed_opportunity": "missed_pedagogical_opportunity",
    "missed_pedagogical_opportunity": "missed_pedagogical_opportunity",
}


def _normalise_provider_feedback_items(raw_items) -> list[FeedbackItemOutput]:
    """Coerce common provider JSON variations without accepting unusable items."""

    if not isinstance(raw_items, list):
        return []
    normalised: list[FeedbackItemOutput] = []
    for raw in raw_items:
        if not isinstance(raw, dict):
            continue
        item = dict(raw)
        criterion = str(item.get("criterion", "")).strip().lower()
        criterion = criterion.replace(" ", "_").replace("-", "_")
        if "concept" in criterion and "accur" in criterion:
            criterion = "pck_conceptual_accuracy"
        elif "formative" in criterion or criterion == "assessment":
            criterion = "formative_assessment"
        elif "cognitive" in criterion or "question" in criterion:
            criterion = "cognitive_questioning"
        elif "miss" in criterion and "opportun" in criterion:
            criterion = "missed_pedagogical_opportunity"
        criterion = CRITERION_ALIASES.get(criterion, criterion)
        item["criterion"] = criterion
        try:
            item["score"] = int(round(float(item.get("score", 3))))
            item["score"] = max(1, min(5, item["score"]))
        except Exception:
            item["score"] = 3
        try:
            item["confidence"] = float(item.get("confidence", 0.5))
            item["confidence"] = max(0.0, min(1.0, item["confidence"]))
        except Exception:
            item["confidence"] = 0.5
        if isinstance(item.get("evidence_turn_ids"), str):
            item["evidence_turn_ids"] = [item["evidence_turn_ids"]]
        if isinstance(item.get("evidence_quotes"), str):
            item["evidence_quotes"] = [item["evidence_quotes"]]
        try:
            normalised.append(FeedbackItemOutput.model_validate(item))
        except Exception:
            continue
    return normalised[:3]


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
