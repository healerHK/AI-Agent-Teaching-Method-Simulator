from fastapi.testclient import TestClient

from app.main import app


def test_health_endpoint_reports_phase2():
    client = TestClient(app)

    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json()["phase"] == "phase_2_interactive_demo"


def test_interactive_demo_session_turn_flow():
    client = TestClient(app)

    start = client.post("/api/sessions", json={"scenario_id": "python_loops_001"})
    assert start.status_code == 200
    payload = start.json()
    session_id = payload["session"]["session_id"]
    assert len(payload["personas"]) >= 5

    turn = client.post(
        f"/api/sessions/{session_id}/turn",
        json={"teacher_message": "Before we run it, how many times will print(number) execute?"},
    )

    assert turn.status_code == 200
    data = turn.json()
    assert data["teacher_turn"]["speaker_role"] == "teacher"
    assert len(data["student_turns"]) == 2
    assert data["response_source"] in {"fallback", "openai"}
    assert data["session_state"]["current_teacher_turn"] == 1
    assert len(data["session_state"]["turns"]) == 3


def test_missing_session_returns_404():
    client = TestClient(app)

    response = client.post(
        "/api/sessions/does_not_exist/turn",
        json={"teacher_message": "Hello?"},
    )

    assert response.status_code == 404
