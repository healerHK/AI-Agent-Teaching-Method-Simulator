from app.openai_client import StudentResponseClient
from app.session_controller import PERSONA_BY_ID


def test_student_response_client_fallback_without_api_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    client = StudentResponseClient()

    reply = client.generate_reply(
        persona=PERSONA_BY_ID["misconception_student"],
        teacher_message="How many times does print execute?",
        learning_objective="Trace for-loops.",
        history=[],
    )

    assert reply.source == "fallback"
    assert "print" in reply.message.lower()
