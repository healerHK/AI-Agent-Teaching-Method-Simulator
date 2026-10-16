from fastapi.testclient import TestClient

from app.main import app


def test_v2_scenarios_expose_refined_thesis_design():
    client = TestClient(app)

    response = client.get("/api/v2/scenarios")

    assert response.status_code == 200
    data = response.json()
    assert "evidence-verifiable" in data["thesis_positioning"]["research_gap"]
    scenario = data["scenarios"][0]
    assert scenario["scenario_id"] == "python_loops_full_lesson_001"
    assert 15 <= scenario["estimated_duration_minutes"] <= 30
    assert scenario["virtual_student_behaviour_claim"] == "literature-informed believable virtual student behaviour"
    phase_ids = {phase["phase_id"] for phase in scenario["lesson_phases"]}
    assert "guided_practice_misconception_event" in phase_ids
    mechanisms = {item["mechanism"] for item in scenario["student_behaviour_architecture"]}
    assert {"memory_stream", "retrieval", "reflection", "planning", "state_update"}.issubset(mechanisms)
    metric_ids = {metric["metric_id"] for metric in data["review_protocol"]["metrics"]}
    assert {"expert_acceptance_rate", "evidence_validity_rate", "unsupported_inference_rate"}.issubset(metric_ids)


def test_v2_live_session_turn_returns_phase_protocol():
    client = TestClient(app)

    start = client.post(
        "/api/v2/live/sessions",
        json={"scenario_id": "python_loops_full_lesson_001", "max_teacher_turns": 8},
    )

    assert start.status_code == 200
    payload = start.json()
    session = payload["session"]
    assert session["scenario_id"] == "python_loops_full_lesson_001"
    assert session["max_teacher_turns"] == 8
    assert "micro-lesson" in session["lesson_title"]
    assert len(payload["scenario"]["lesson_phases"]) >= 5

    turn = client.post(
        f"/api/v2/live/sessions/{session['session_id']}/turn",
        json={"teacher_message": "Predict the output before I run this for-loop."},
    )

    assert turn.status_code == 200
    turn_data = turn.json()
    assert turn_data["teacher_turn"]["speaker_role"] == "teacher"
    assert len(turn_data["student_turns"]) >= 1
    assert turn_data["current_phase"]["phase_id"] == "opening_prior_knowledge"
    assert turn_data["session_state"]["max_teacher_turns"] == 8
    assert "fixed transcript mode" in " ".join(turn_data["protocol_notes"])


def test_v2_transcript_benchmark_runs_controlled_blinded_pipeline(monkeypatch):
    monkeypatch.setenv("EVALUATOR_PROVIDER", "fallback")
    client = TestClient(app)

    response = client.post(
        "/api/v2/transcript-benchmark/run",
        json={"transcript_id": "python_loops_weak_001", "reviewer_id": "expert_reviewer_test_v2"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["benchmark_protocol"]["controlled_comparison"] is True
    assert data["benchmark_protocol"]["baseline_condition_hidden_from_reviewer"] is True
    assert data["baseline_evaluation_id"].startswith("eval_")
    assert data["til_evaluation_id"].startswith("eval_")
    assert data["baseline_verification"]["overall_status"] in {"verified", "missing_evidence", "unsupported"}
    assert data["til_verification"]["overall_status"] == "verified"
    blinded = data["blinded_review"]["blinded_evaluations"]
    assert [item["display_label"] for item in blinded] == ["Evaluation A", "Evaluation B"]
    assert "actual_condition" not in str(data["blinded_review"])
    assert data["review_metrics"]["annotations_count"] == 0
    metric_ids = {metric["metric_id"] for metric in data["review_metrics"]["metrics_definition"]}
    assert "correction_rate" in metric_ids
    assert "stronger alignment with expert pedagogical judgement" in " ".join(data["claim_guardrails"])
