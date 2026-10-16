"""FastAPI app for PixelClass TIL Phase 2/3/4 MVP."""

from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.benchmark_loader import GoldenBenchmarkLoader
from app.blinding import AnnotationService, BlindedReviewService
from app.evaluator_models import (
    AnnotationRequest,
    AnnotationResponse,
    CreateBlindedReviewRequest,
    Phase3DemoRequest,
    Phase3DemoResponse,
    RunEvaluationRequest,
    RunEvaluationResponse,
)
from app.evaluator_runner import EvaluatorRunner
from app.evidence_verifier import EvidenceVerifier
from app.llm_provider import evaluator_provider_status
from app.session_controller import ClassroomSessionController, PERSONAS, SessionNotFound
from app.session_models import (
    StartSessionRequest,
    StartSessionResponse,
    TeacherTurnRequest,
    TeacherTurnResponse,
)
from app.transcript_models import (
    RenderedStudentPrompt,
    TranscriptScenario,
    TranscriptScenarioListResponse,
    TranscriptScenarioSaveResponse,
    TranscriptScenarioTestResponse,
)
from app.transcript_service import TranscriptScenarioNotFound, TranscriptScenarioService
from app.v2_models import (
    LiveSessionStartRequest,
    LiveSessionStartResponse,
    LiveTeacherTurnRequest,
    LiveTeacherTurnResponse,
    ReviewMetricsSummary,
    ScenarioListResponse,
    TranscriptBenchmarkRunRequest,
    TranscriptBenchmarkRunResponse,
)
from app.v2_service import PixelClassV2Service

app = FastAPI(title="PixelClass TIL API", version="0.5.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

controller = ClassroomSessionController()
benchmark_loader = GoldenBenchmarkLoader()
evaluator_runner = EvaluatorRunner(benchmark_loader)
evidence_verifier = EvidenceVerifier(benchmark_loader)
blinded_review_service = BlindedReviewService(evaluator_runner)
annotation_service = AnnotationService()
transcript_scenario_service = TranscriptScenarioService()
v2_service = PixelClassV2Service(
    controller=controller,
    loader=benchmark_loader,
    evaluator_runner=evaluator_runner,
    evidence_verifier=evidence_verifier,
    blinded_review_service=blinded_review_service,
)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok", "phase": "phase_3_evaluation_pipeline"}


@app.get("/api/v2/transcript-system/scenarios", response_model=TranscriptScenarioListResponse)
def transcript_system_scenarios() -> TranscriptScenarioListResponse:
    return transcript_scenario_service.list_scenarios()


@app.get("/api/v2/transcript-system/scenarios/{scenario_id}", response_model=TranscriptScenario)
def transcript_system_get_scenario(scenario_id: str) -> TranscriptScenario:
    try:
        return transcript_scenario_service.load_scenario(scenario_id)
    except TranscriptScenarioNotFound:
        raise HTTPException(status_code=404, detail="Transcript scenario not found")


@app.put("/api/v2/transcript-system/scenarios/{scenario_id}", response_model=TranscriptScenarioSaveResponse)
def transcript_system_save_scenario(
    scenario_id: str,
    scenario: TranscriptScenario,
) -> TranscriptScenarioSaveResponse:
    if scenario_id != scenario.scenario_id:
        raise HTTPException(status_code=400, detail="Path scenario_id must match payload scenario_id")
    return transcript_scenario_service.save_scenario(scenario)


@app.get(
    "/api/v2/transcript-system/scenarios/{scenario_id}/prompts",
    response_model=list[RenderedStudentPrompt],
)
def transcript_system_render_prompts(scenario_id: str) -> list[RenderedStudentPrompt]:
    try:
        return transcript_scenario_service.render_student_prompts(scenario_id)
    except TranscriptScenarioNotFound:
        raise HTTPException(status_code=404, detail="Transcript scenario not found")


@app.post(
    "/api/v2/transcript-system/scenarios/{scenario_id}/test",
    response_model=TranscriptScenarioTestResponse,
)
def transcript_system_test_scenario(scenario_id: str) -> TranscriptScenarioTestResponse:
    try:
        return transcript_scenario_service.run_readiness_test(scenario_id)
    except TranscriptScenarioNotFound:
        raise HTTPException(status_code=404, detail="Transcript scenario not found")


@app.post(
    "/api/v2/transcript-system/scenarios/{scenario_id}/til-evaluation",
    response_model=TranscriptBenchmarkRunResponse,
)
def transcript_system_til_evaluation(
    scenario_id: str,
    reviewer_id: str = "expert_reviewer_transcript_system",
) -> TranscriptBenchmarkRunResponse:
    try:
        readiness = transcript_scenario_service.run_readiness_test(scenario_id)
        if not readiness.passed:
            raise HTTPException(status_code=400, detail="Scenario must pass readiness checks before TIL evaluation")
        transcript = transcript_scenario_service.to_benchmark_transcript(scenario_id)
        return v2_service.run_runtime_transcript_benchmark(
            transcript=transcript,
            reviewer_id=reviewer_id,
        )
    except TranscriptScenarioNotFound:
        raise HTTPException(status_code=404, detail="Transcript scenario not found")


@app.get("/api/v2/scenarios", response_model=ScenarioListResponse)
def v2_scenarios() -> ScenarioListResponse:
    return v2_service.list_scenarios()


@app.post("/api/v2/live/sessions", response_model=LiveSessionStartResponse)
def v2_start_live_session(request: LiveSessionStartRequest) -> LiveSessionStartResponse:
    try:
        return v2_service.start_live_session(
            scenario_id=request.scenario_id,
            max_teacher_turns=request.max_teacher_turns,
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@app.post("/api/v2/live/sessions/{session_id}/turn", response_model=LiveTeacherTurnResponse)
def v2_live_teacher_turn(session_id: str, request: LiveTeacherTurnRequest) -> LiveTeacherTurnResponse:
    try:
        return v2_service.live_teacher_turn(
            session_id=session_id,
            teacher_message=request.teacher_message,
        )
    except SessionNotFound:
        raise HTTPException(status_code=404, detail="Session not found")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.post("/api/v2/transcript-benchmark/run", response_model=TranscriptBenchmarkRunResponse)
def v2_run_transcript_benchmark(
    request: TranscriptBenchmarkRunRequest,
) -> TranscriptBenchmarkRunResponse:
    try:
        return v2_service.run_transcript_benchmark(
            transcript_id=request.transcript_id,
            reviewer_id=request.reviewer_id,
        )
    except (FileNotFoundError, KeyError) as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.get("/api/v2/expert-review/summary/{reviewer_id}", response_model=ReviewMetricsSummary)
def v2_expert_review_summary(reviewer_id: str) -> ReviewMetricsSummary:
    return v2_service.review_metrics_summary(reviewer_id=reviewer_id)


@app.get("/api/evaluator/status")
def evaluator_status() -> dict[str, object]:
    """Safe evaluator provider diagnostics for testing.

    No raw API keys are returned. A configured Gemini key can still fail at runtime
    if the Google project lacks model/API permission; live smoke tests handle that
    with deterministic fallback.
    """

    return {
        "conditions": [
            evaluator_provider_status("baseline"),
            evaluator_provider_status("til"),
        ],
        "secrets_redacted": True,
        "fallback_policy": "provider failures fall back to deterministic evaluator output",
    }


@app.get("/api/personas")
def personas():
    return {"personas": PERSONAS}


@app.post("/api/sessions", response_model=StartSessionResponse)
def start_session(request: StartSessionRequest) -> StartSessionResponse:
    session = controller.start_session(
        scenario_id=request.scenario_id,
        max_teacher_turns=request.max_teacher_turns,
    )
    return StartSessionResponse(session=session, personas=PERSONAS)


@app.get("/api/sessions/{session_id}")
def get_session(session_id: str):
    try:
        return {"session": controller.get_session(session_id), "personas": PERSONAS}
    except SessionNotFound:
        raise HTTPException(status_code=404, detail="Session not found")


@app.post("/api/sessions/{session_id}/turn", response_model=TeacherTurnResponse)
def teacher_turn(session_id: str, request: TeacherTurnRequest) -> TeacherTurnResponse:
    try:
        teacher, students, state, source = controller.handle_teacher_turn(
            session_id=session_id,
            teacher_message=request.teacher_message,
        )
    except SessionNotFound:
        raise HTTPException(status_code=404, detail="Session not found")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return TeacherTurnResponse(
        teacher_turn=teacher,
        student_turns=students,
        session_state=state,
        response_source=source,
    )


@app.get("/api/benchmark/items")
def benchmark_items():
    return {"dataset_version": benchmark_loader.dataset_version(), "items": benchmark_loader.list_items()}


@app.get("/api/benchmark/transcripts/{transcript_id}")
def benchmark_transcript(transcript_id: str):
    try:
        transcript = benchmark_loader.load_transcript(transcript_id)
        expected_scores = benchmark_loader.load_expected_scores(transcript_id)
        missed = benchmark_loader.load_expected_missed_opportunities(transcript_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Transcript not found")
    return {
        "transcript": transcript,
        "expected_scores": expected_scores,
        "expected_missed_opportunities": missed,
    }


@app.post("/api/evaluations/run", response_model=RunEvaluationResponse)
def run_evaluation(request: RunEvaluationRequest) -> RunEvaluationResponse:
    try:
        evaluation_id, experiment_id, output = evaluator_runner.run(
            transcript_id=request.transcript_id,
            condition=request.condition,
        )
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Transcript not found")
    return RunEvaluationResponse(
        evaluation_id=evaluation_id,
        experiment_id=experiment_id,
        transcript_id=request.transcript_id,
        condition=request.condition,
        output=output,
    )


@app.get("/api/evaluations/{evaluation_id}")
def get_evaluation(evaluation_id: str):
    items = evaluator_runner.get_feedback_items(evaluation_id)
    if not items:
        raise HTTPException(status_code=404, detail="Evaluation not found or has no feedback items")
    return {"evaluation_id": evaluation_id, "feedback_items": items}


@app.post("/api/evaluations/{evaluation_id}/verify")
def verify_evaluation(evaluation_id: str):
    try:
        return evidence_verifier.verify_evaluation(evaluation_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Evaluation not found")


@app.post("/api/reviews/blind")
def create_blinded_review(request: CreateBlindedReviewRequest):
    try:
        evaluation_ids = request.evaluation_ids
        if not evaluation_ids:
            baseline_id, experiment_id, _ = evaluator_runner.run(
                transcript_id=request.transcript_id,
                condition="baseline",
            )
            til_id, _, _ = evaluator_runner.run(
                transcript_id=request.transcript_id,
                condition="til",
                experiment_id=experiment_id,
            )
            evidence_verifier.verify_evaluation(baseline_id)
            evidence_verifier.verify_evaluation(til_id)
            evaluation_ids = [baseline_id, til_id]
        return blinded_review_service.create_review(
            transcript_id=request.transcript_id,
            reviewer_id=request.reviewer_id,
            evaluation_ids=evaluation_ids,
        )
    except (FileNotFoundError, KeyError) as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.post("/api/annotations", response_model=AnnotationResponse)
def save_annotation(request: AnnotationRequest) -> AnnotationResponse:
    return annotation_service.save_annotation(request)


@app.post("/api/phase3/demo", response_model=Phase3DemoResponse)
def phase3_demo(request: Phase3DemoRequest) -> Phase3DemoResponse:
    try:
        baseline_id, experiment_id, _ = evaluator_runner.run(
            transcript_id=request.transcript_id,
            condition="baseline",
        )
        til_id, _, _ = evaluator_runner.run(
            transcript_id=request.transcript_id,
            condition="til",
            experiment_id=experiment_id,
        )
        baseline_verification = evidence_verifier.verify_evaluation(baseline_id)
        til_verification = evidence_verifier.verify_evaluation(til_id)
        blinded_review = blinded_review_service.create_review(
            transcript_id=request.transcript_id,
            reviewer_id=request.reviewer_id,
            evaluation_ids=[baseline_id, til_id],
        )
    except (FileNotFoundError, KeyError) as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return Phase3DemoResponse(
        transcript_id=request.transcript_id,
        baseline_evaluation_id=baseline_id,
        til_evaluation_id=til_id,
        baseline_verification=baseline_verification,
        til_verification=til_verification,
        blinded_review=blinded_review,
    )
