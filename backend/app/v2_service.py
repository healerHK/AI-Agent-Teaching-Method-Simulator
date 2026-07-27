"""PixelClass TIL v2 orchestration service.

V2 keeps Phase 2/3/4 runnable but exposes the refined MVP as a cohesive
Teacher-in-the-Loop benchmark system:

1. Live Mode: 15-30 minute human-teacher micro-lesson with literature-informed
   virtual student behaviour.
2. Transcript Benchmark Mode: fixed transcript -> baseline evaluator -> TIL
   evidence-grounded evaluator -> verifier -> blinded expert review.
"""

from __future__ import annotations

from statistics import mean

from app.benchmark_loader import GoldenBenchmarkLoader
from app.blinding import BlindedReviewService
from app.database import connect, init_db
from app.evaluator_runner import EvaluatorRunner
from app.evidence_verifier import EvidenceVerifier
from app.session_controller import ClassroomSessionController, PERSONAS, SessionNotFound
from app.v2_models import (
    LessonPhase,
    LiveSessionStartResponse,
    LiveTeacherTurnResponse,
    MetricDefinition,
    ReviewMetricsSummary,
    ReviewProtocol,
    ScenarioListResponse,
    ScenarioSpec,
    StudentBehaviourMechanism,
    ThesisPositioning,
    TranscriptBenchmarkRunResponse,
)


DEFAULT_V2_SCENARIO_ID = "python_loops_full_lesson_001"


def thesis_positioning() -> ThesisPositioning:
    return ThesisPositioning(
        title="PixelClass TIL: A Teacher-in-the-Loop benchmark system for evaluating pedagogical feedback in simulated classroom teaching sessions.",
        research_gap=(
            "Existing LLM-based educational simulations can generate classroom-like dialogue, "
            "but they rarely provide a reliable, theory-grounded, evidence-verifiable mechanism "
            "for evaluating pedagogical quality across lesson-style teaching transcripts."
        ),
        contribution=(
            "A controlled transcript benchmark and live micro-lesson testbed that compares generic "
            "LLM feedback with a TIL evidence-grounded evaluator using evidence verification and "
            "blinded human/expert review."
        ),
        safe_claim=(
            "The system aims for stronger alignment with expert pedagogical judgement, fewer unsupported "
            "claims, and more actionable evidence-grounded feedback; it does not claim expert replacement "
            "or real-student behavioural fidelity."
        ),
    )


def metric_definitions() -> list[MetricDefinition]:
    return [
        MetricDefinition(
            metric_id="expert_acceptance_rate",
            label="Expert acceptance rate",
            formula="accepted_feedback_items / reviewed_feedback_items",
            interpretation="Higher means the reviewer accepts more AI feedback items as pedagogically valid.",
        ),
        MetricDefinition(
            metric_id="correction_rate",
            label="Correction rate",
            formula="items_requiring_human_score_change_or_disagreement / reviewed_feedback_items",
            interpretation="Lower means fewer expert corrections are needed.",
        ),
        MetricDefinition(
            metric_id="rejection_rate",
            label="Rejection rate",
            formula="rejected_feedback_items / reviewed_feedback_items",
            interpretation="Lower means fewer AI feedback items are discarded by the reviewer.",
        ),
        MetricDefinition(
            metric_id="evidence_validity_rate",
            label="Evidence validity rate",
            formula="feedback_items_without_fabricated_evidence / reviewed_feedback_items",
            interpretation="Higher means supplied quotes/turn IDs are trusted by the reviewer.",
        ),
        MetricDefinition(
            metric_id="unsupported_inference_rate",
            label="Unsupported inference rate",
            formula="unsupported_inference_flags / reviewed_feedback_items",
            interpretation="Lower means fewer claims go beyond transcript evidence.",
        ),
        MetricDefinition(
            metric_id="usefulness_mean",
            label="Mean usefulness rating",
            formula="mean(usefulness_rating_1_to_5)",
            interpretation="Higher means the feedback is more useful/actionable for teacher reflection.",
        ),
    ]


def review_protocol() -> ReviewProtocol:
    return ReviewProtocol(
        reviewer_role="Professor/supervisor or teaching-experienced expert reviewer",
        blinding="Reviewer sees Evaluation A vs Evaluation B without knowing baseline/TIL condition.",
        rating_dimensions=[
            "pedagogical correctness",
            "evidence validity",
            "actionability",
            "usefulness",
            "unsupported inference",
            "missed pedagogical opportunity coverage",
        ],
        metrics=metric_definitions(),
    )


def _lesson_phases() -> list[LessonPhase]:
    return [
        LessonPhase(
            phase_id="opening_prior_knowledge",
            title="Opening and prior knowledge activation",
            minute_range="0-4",
            teacher_goal="Activate students' existing understanding of repetition and predict what a for-loop might do.",
            expected_student_behaviours=[
                "high achiever answers quickly and may dominate",
                "anxious beginner hesitates before making a prediction",
                "quiet/disengaged student gives minimal response unless invited",
            ],
            evidence_focus=["teacher invites prediction", "teacher distributes participation"],
        ),
        LessonPhase(
            phase_id="explanation_modelling",
            title="Concept explanation and modelling",
            minute_range="4-10",
            teacher_goal="Explain loop variable update and model one trace of `for number in [1, 2, 3]`.",
            expected_student_behaviours=[
                "misconception-heavy student confuses one written print line with one runtime execution",
                "curious student asks an extension question that may pull the class ahead too early",
            ],
            evidence_focus=["conceptual accuracy", "scaffolding", "response to misconception"],
        ),
        LessonPhase(
            phase_id="guided_practice_misconception_event",
            title="Guided practice and misconception event",
            minute_range="10-18",
            teacher_goal="Ask students to complete a trace table and respond to visible misconceptions.",
            expected_student_behaviours=[
                "students reveal confusion about iteration count",
                "anxious beginner needs step-by-step support",
                "peer influence may spread or correct a misconception",
            ],
            evidence_focus=["formative assessment", "missed pedagogical opportunity", "student reasoning elicitation"],
        ),
        LessonPhase(
            phase_id="formative_assessment",
            title="Formative assessment checkpoint",
            minute_range="18-24",
            teacher_goal="Check whether students can predict output and explain why each value is printed.",
            expected_student_behaviours=[
                "overconfident answer without reasoning",
                "quiet student may demonstrate partial understanding when directly prompted",
            ],
            evidence_focus=["checking understanding", "quality of teacher follow-up questions"],
        ),
        LessonPhase(
            phase_id="reflection_closure",
            title="Reflection and closure",
            minute_range="24-30",
            teacher_goal="Summarise the concept and connect student evidence to next teaching action.",
            expected_student_behaviours=[
                "student state shows gradual understanding change",
                "remaining uncertainty is surfaced for the next lesson",
            ],
            evidence_focus=["closure", "next-step teaching action", "remaining misconceptions"],
        ),
    ]


def _student_behaviour_architecture() -> list[StudentBehaviourMechanism]:
    source = "Inspired by Generative Agents (memory stream, retrieval, reflection, planning); adapted only as literature-informed simulation support."
    claim = "Supports literature-informed believable virtual student behaviour, not real-student-data fidelity."
    return [
        StudentBehaviourMechanism(
            mechanism="memory_stream",
            source=source,
            implementation_signal="Each persona keeps recent classroom events such as predictions, confusion, corrections, and confidence changes.",
            thesis_claim=claim,
        ),
        StudentBehaviourMechanism(
            mechanism="retrieval",
            source=source,
            implementation_signal="Responses are influenced by recency, relevance to the current teacher prompt, and pedagogical importance of misconceptions.",
            thesis_claim=claim,
        ),
        StudentBehaviourMechanism(
            mechanism="reflection",
            source=source,
            implementation_signal="Student state can convert repeated evidence into a higher-level belief such as 'I now see print runs once per item'.",
            thesis_claim=claim,
        ),
        StudentBehaviourMechanism(
            mechanism="planning",
            source=source,
            implementation_signal="Personas choose whether to answer, stay silent, ask a question, or reveal confusion based on role and lesson phase.",
            thesis_claim=claim,
        ),
        StudentBehaviourMechanism(
            mechanism="state_update",
            source="Pedagogical simulation layer built for the MVP.",
            implementation_signal="Confidence, misconception strength, participation, and affect are updated after teacher turns.",
            thesis_claim=claim,
        ),
    ]


def scenario_spec(loader: GoldenBenchmarkLoader | None = None) -> ScenarioSpec:
    loader = loader or GoldenBenchmarkLoader()
    available_transcripts = [item["transcript_id"] for item in loader.list_items()]
    return ScenarioSpec(
        scenario_id=DEFAULT_V2_SCENARIO_ID,
        title="Python loops micro-lesson: prediction, tracing, misconception response, and closure",
        mode="live_micro_lesson_and_transcript_benchmark",
        estimated_duration_minutes=25,
        subject_domain="introductory programming",
        education_level="upper-secondary / early undergraduate",
        learning_objective=(
            "Students explain that a Python for-loop executes its body once for each item in a sequence "
            "and can trace how the loop variable changes across iterations."
        ),
        core_misconceptions=[
            "one written print statement means one execution",
            "the loop variable updates before the body runs",
            "the list length and output count are unrelated",
            "students can predict output without explaining the iteration mechanism",
        ],
        lesson_phases=_lesson_phases(),
        virtual_student_behaviour_claim="literature-informed believable virtual student behaviour",
        student_behaviour_architecture=_student_behaviour_architecture(),
        planned_benchmark_variants=[
            "python_loops_strong_teacher",
            "python_loops_weak_teacher",
            "python_loops_missed_misconception",
            "python_loops_poor_scaffolding",
            "python_loops_low_participation",
        ],
        available_transcript_ids=available_transcripts,
        claim_guardrails=[
            "Simulation is the testbed; evidence-grounded pedagogical evaluation is the contribution.",
            "Do not claim AI students reproduce real student behaviour without real data and ethics approval.",
            "Do not claim the evaluator is expert-level or replaces expert judgement.",
            "Use 'stronger alignment with expert pedagogical judgement' after human/expert review evidence.",
        ],
    )


class PixelClassV2Service:
    def __init__(
        self,
        controller: ClassroomSessionController | None = None,
        loader: GoldenBenchmarkLoader | None = None,
        evaluator_runner: EvaluatorRunner | None = None,
        evidence_verifier: EvidenceVerifier | None = None,
        blinded_review_service: BlindedReviewService | None = None,
    ) -> None:
        self.controller = controller or ClassroomSessionController()
        self.loader = loader or GoldenBenchmarkLoader()
        self.evaluator_runner = evaluator_runner or EvaluatorRunner(self.loader)
        self.evidence_verifier = evidence_verifier or EvidenceVerifier(self.loader)
        self.blinded_review_service = blinded_review_service or BlindedReviewService(self.evaluator_runner)
        init_db()

    def list_scenarios(self) -> ScenarioListResponse:
        return ScenarioListResponse(
            thesis_positioning=thesis_positioning(),
            scenarios=[scenario_spec(self.loader)],
            review_protocol=review_protocol(),
        )

    def start_live_session(self, *, scenario_id: str = DEFAULT_V2_SCENARIO_ID, max_teacher_turns: int = 8) -> LiveSessionStartResponse:
        spec = scenario_spec(self.loader)
        if scenario_id != spec.scenario_id:
            raise FileNotFoundError(f"Unknown v2 scenario_id: {scenario_id}")
        self._ensure_v2_scenario_seed(spec)
        session = self.controller.start_session(scenario_id=scenario_id, max_teacher_turns=max_teacher_turns)
        return LiveSessionStartResponse(
            scenario=spec,
            session=session,
            personas=PERSONAS,
            protocol_notes=[
                "Use this live mode for demo/pilot/user-study transcript collection, not the controlled benchmark result.",
                "Recommended Honours MVP duration is 15-30 minutes; this run uses eight teacher turns as a compact proxy.",
            ],
        )

    def live_teacher_turn(self, *, session_id: str, teacher_message: str) -> LiveTeacherTurnResponse:
        teacher, students, state, source = self.controller.handle_teacher_turn(
            session_id=session_id,
            teacher_message=teacher_message,
        )
        return LiveTeacherTurnResponse(
            teacher_turn=teacher,
            student_turns=students,
            session_state=state,
            response_source=source,
            current_phase=_phase_for_turn(state.current_teacher_turn, state.max_teacher_turns),
            protocol_notes=[
                "Current student replies are literature-informed simulation/fallback unless a provider is configured.",
                "Saved transcript can later be evaluated, but fixed transcript mode remains the fair A/B benchmark.",
            ],
        )

    def run_transcript_benchmark(self, *, transcript_id: str, reviewer_id: str) -> TranscriptBenchmarkRunResponse:
        transcript = self.loader.load_transcript(transcript_id)
        baseline_id, experiment_id, _ = self.evaluator_runner.run(
            transcript_id=transcript_id,
            condition="baseline",
        )
        til_id, _, _ = self.evaluator_runner.run(
            transcript_id=transcript_id,
            condition="til",
            experiment_id=experiment_id,
        )
        baseline_verification = self.evidence_verifier.verify_evaluation(baseline_id)
        til_verification = self.evidence_verifier.verify_evaluation(til_id)
        blinded_review = self.blinded_review_service.create_review(
            transcript_id=transcript_id,
            reviewer_id=reviewer_id,
            evaluation_ids=[baseline_id, til_id],
        )
        spec = scenario_spec(self.loader)
        return TranscriptBenchmarkRunResponse(
            thesis_positioning=thesis_positioning(),
            transcript_id=transcript_id,
            transcript=transcript,
            scenario=spec,
            benchmark_protocol={
                "controlled_comparison": True,
                "pipeline": [
                    "fixed transcript",
                    "generic/baseline evaluator",
                    "TIL evidence-grounded evaluator",
                    "evidence verifier",
                    "blinded expert review",
                    "metrics summary",
                ],
                "baseline_condition_hidden_from_reviewer": True,
                "experiment_id": experiment_id,
                "main_claim_scope": "expert-alignment and evidence-grounded feedback quality, not real classroom fidelity",
            },
            baseline_evaluation_id=baseline_id,
            til_evaluation_id=til_id,
            baseline_verification=baseline_verification,
            til_verification=til_verification,
            blinded_review=blinded_review,
            review_metrics=self.review_metrics_summary(reviewer_id=reviewer_id),
            claim_guardrails=spec.claim_guardrails,
        )

    def _ensure_v2_scenario_seed(self, spec: ScenarioSpec) -> None:
        with connect() as conn:
            conn.execute(
                """
                INSERT OR IGNORE INTO scenarios
                (scenario_id, title, domain, education_level, learning_objective, source_path)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    spec.scenario_id,
                    spec.title,
                    spec.subject_domain,
                    spec.education_level,
                    spec.learning_objective,
                    "generated:v2_live_micro_lesson",
                ),
            )
            conn.commit()

    def review_metrics_summary(self, *, reviewer_id: str) -> ReviewMetricsSummary:
        with connect() as conn:
            rows = conn.execute(
                "SELECT * FROM human_annotations WHERE reviewer_id = ?",
                (reviewer_id,),
            ).fetchall()
        total = len(rows)
        if total == 0:
            return ReviewMetricsSummary(
                reviewer_id=reviewer_id,
                annotations_count=0,
                expert_acceptance_rate=0.0,
                correction_rate=0.0,
                rejection_rate=0.0,
                evidence_validity_rate=0.0,
                unsupported_inference_rate=0.0,
                usefulness_mean=None,
                metrics_definition=metric_definitions(),
            )
        accepted = sum(int(row["accept"]) for row in rows)
        rejected = total - accepted
        fabricated = sum(int(row["fabricated_evidence"]) for row in rows)
        unsupported = sum(int(row["unsupported_inference"]) for row in rows)
        disagreements = sum(int(row["pedagogical_disagreement"]) for row in rows)
        score_changes = sum(
            1
            for row in rows
            if row["human_score"] is not None
            and row["ai_score"] is not None
            and row["human_score"] != row["ai_score"]
        )
        usefulness_values = [row["usefulness"] for row in rows if row["usefulness"] is not None]
        return ReviewMetricsSummary(
            reviewer_id=reviewer_id,
            annotations_count=total,
            expert_acceptance_rate=round(accepted / total, 3),
            correction_rate=round((disagreements + score_changes) / total, 3),
            rejection_rate=round(rejected / total, 3),
            evidence_validity_rate=round((total - fabricated) / total, 3),
            unsupported_inference_rate=round(unsupported / total, 3),
            usefulness_mean=round(mean(usefulness_values), 2) if usefulness_values else None,
            metrics_definition=metric_definitions(),
        )


def _phase_for_turn(current_teacher_turn: int, max_teacher_turns: int) -> LessonPhase:
    phases = _lesson_phases()
    if current_teacher_turn <= 0:
        return phases[0]
    safe_max = max(max_teacher_turns, 1)
    index = min((current_teacher_turn - 1) * len(phases) // safe_max, len(phases) - 1)
    return phases[index]
