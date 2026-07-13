"""FastAPI app for PixelClass TIL Phase 2."""

from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.session_controller import ClassroomSessionController, PERSONAS, SessionNotFound
from app.session_models import (
    StartSessionRequest,
    StartSessionResponse,
    TeacherTurnRequest,
    TeacherTurnResponse,
)

app = FastAPI(title="PixelClass TIL API", version="0.2.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

controller = ClassroomSessionController()


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok", "phase": "phase_2_interactive_demo"}


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
