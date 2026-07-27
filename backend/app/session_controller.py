"""Deterministic Phase 2 classroom session controller."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from app.database import connect, init_db
from app.openai_client import StudentResponseClient
from app.session_models import ClassroomTurn, SessionState, StudentPersona

DEFAULT_SCENARIO_ID = "python_loops_001"
DEFAULT_LESSON_TITLE = "Python for-loops and iteration tracing"
DEFAULT_LEARNING_OBJECTIVE = (
    "Students explain that a for-loop repeats a block once for each item in a sequence "
    "and can trace the loop variable across iterations."
)
SCENARIO_METADATA = {
    DEFAULT_SCENARIO_ID: {
        "lesson_title": DEFAULT_LESSON_TITLE,
        "learning_objective": DEFAULT_LEARNING_OBJECTIVE,
    },
    "python_loops_full_lesson_001": {
        "lesson_title": "Python loops micro-lesson: prediction, tracing, misconception response, and closure",
        "learning_objective": (
            "Students explain that a Python for-loop executes its body once for each item in a sequence "
            "and can trace how the loop variable changes across iterations."
        ),
    },
}

PERSONAS = [
    StudentPersona(
        persona_id="high_achiever",
        name="Alex",
        display_role="High-achieving student",
        learning_profile="Usually answers quickly and can explain reasoning.",
        misconception_bias="Low misconception; may dominate discussion.",
        avatar_variant="blue",
    ),
    StudentPersona(
        persona_id="misconception_student",
        name="Mia",
        display_role="Misconception-heavy student",
        learning_profile="Often reveals useful conceptual misunderstandings.",
        misconception_bias="Confuses written code lines with runtime repetitions.",
        avatar_variant="pink",
    ),
    StudentPersona(
        persona_id="anxious_beginner",
        name="Sam",
        display_role="Anxious beginner",
        learning_profile="Needs slower scaffolding and reassurance.",
        misconception_bias="Unsure how loop variables update.",
        avatar_variant="green",
    ),
    StudentPersona(
        persona_id="disengaged_student",
        name="Noah",
        display_role="Disengaged student",
        learning_profile="Answers briefly unless invited directly.",
        misconception_bias="May repeat terms without explanation.",
        avatar_variant="orange",
    ),
    StudentPersona(
        persona_id="curious_student",
        name="Lina",
        display_role="Curious/distracted student",
        learning_profile="Asks extension questions and sometimes jumps ahead.",
        misconception_bias="May overgeneralise from one example.",
        avatar_variant="purple",
    ),
]
PERSONA_BY_ID = {persona.persona_id: persona for persona in PERSONAS}


class SessionNotFound(KeyError):
    pass


class ClassroomSessionController:
    def __init__(self, response_client: StudentResponseClient | None = None) -> None:
        self.response_client = response_client or StudentResponseClient()
        self._session_max_turns: dict[str, int] = {}
        init_db()

    def start_session(self, scenario_id: str = DEFAULT_SCENARIO_ID, max_teacher_turns: int = 12) -> SessionState:
        session_id = f"sess_{uuid4().hex[:12]}"
        metadata = _scenario_metadata(scenario_id)
        state = SessionState(
            session_id=session_id,
            scenario_id=scenario_id,
            lesson_title=metadata["lesson_title"],
            learning_objective=metadata["learning_objective"],
            max_teacher_turns=max_teacher_turns,
        )
        self._session_max_turns[session_id] = max_teacher_turns
        with connect() as conn:
            conn.execute(
                """
                INSERT INTO sessions (session_id, scenario_id, mode, created_at, completed_at)
                VALUES (?, ?, ?, ?, NULL)
                """,
                (session_id, scenario_id, "interactive_demo", _now()),
            )
            conn.commit()
        return state

    def get_session(self, session_id: str) -> SessionState:
        with connect() as conn:
            session = conn.execute(
                "SELECT * FROM sessions WHERE session_id = ?", (session_id,)
            ).fetchone()
            if not session:
                raise SessionNotFound(session_id)
            rows = conn.execute(
                "SELECT * FROM turns WHERE session_id = ? ORDER BY turn_index ASC", (session_id,)
            ).fetchall()

        turns = [
            ClassroomTurn(
                turn_id=row["turn_id"],
                speaker_role=row["speaker_role"],
                speaker_name=row["speaker_name"],
                persona_id=None,
                message=row["message"],
                turn_index=row["turn_index"],
            )
            for row in rows
        ]
        teacher_turns = len([turn for turn in turns if turn.speaker_role == "teacher"])
        metadata = _scenario_metadata(session["scenario_id"])
        return SessionState(
            session_id=session_id,
            scenario_id=session["scenario_id"],
            lesson_title=metadata["lesson_title"],
            learning_objective=metadata["learning_objective"],
            current_teacher_turn=teacher_turns,
            max_teacher_turns=self._session_max_turns.get(session_id, 12),
            turns=turns,
            status="completed" if session["completed_at"] else "active",
        )

    def handle_teacher_turn(self, session_id: str, teacher_message: str):
        state = self.get_session(session_id)
        if state.status == "completed":
            raise ValueError("Session is already completed")

        next_index = len(state.turns) + 1
        teacher_turn_number = state.current_teacher_turn + 1
        teacher_turn = ClassroomTurn(
            turn_id=f"{session_id}_turn_{next_index:03d}",
            speaker_role="teacher",
            speaker_name="Teacher",
            message=teacher_message,
            turn_index=next_index,
        )
        self._store_turn(session_id, teacher_turn)
        history = state.turns + [teacher_turn]

        student_turns: list[ClassroomTurn] = []
        response_source = "fallback"
        for persona_id in self._student_plan_for_teacher_turn(teacher_turn_number):
            persona = PERSONA_BY_ID[persona_id]
            reply = self.response_client.generate_reply(
                persona=persona,
                teacher_message=teacher_message,
                learning_objective=state.learning_objective,
                history=history + student_turns,
            )
            response_source = reply.source
            turn = ClassroomTurn(
                turn_id=f"{session_id}_turn_{next_index + len(student_turns) + 1:03d}",
                speaker_role="student",
                speaker_name=persona.name,
                persona_id=persona.persona_id,
                message=reply.message,
                turn_index=next_index + len(student_turns) + 1,
            )
            self._store_turn(session_id, turn)
            student_turns.append(turn)

        if teacher_turn_number >= state.max_teacher_turns:
            self.complete_session(session_id)

        updated_state = self.get_session(session_id)
        return teacher_turn, student_turns, updated_state, response_source

    def complete_session(self, session_id: str) -> None:
        with connect() as conn:
            conn.execute(
                "UPDATE sessions SET completed_at = ? WHERE session_id = ?",
                (_now(), session_id),
            )
            conn.commit()

    def _store_turn(self, session_id: str, turn: ClassroomTurn) -> None:
        with connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO turns
                (turn_key, turn_id, transcript_id, session_id, speaker_role, speaker_name, message, turn_index)
                VALUES (?, ?, NULL, ?, ?, ?, ?, ?)
                """,
                (
                    f"{session_id}:{turn.turn_id}",
                    turn.turn_id,
                    session_id,
                    turn.speaker_role,
                    turn.speaker_name,
                    turn.message,
                    turn.turn_index,
                ),
            )
            conn.commit()

    def _student_plan_for_teacher_turn(self, teacher_turn_number: int) -> list[str]:
        if teacher_turn_number == 1:
            return ["high_achiever", "misconception_student"]
        if teacher_turn_number == 2:
            return ["anxious_beginner"]
        if teacher_turn_number == 3:
            return ["disengaged_student", "curious_student"]
        if teacher_turn_number == 4:
            return ["misconception_student", "anxious_beginner"]
        if teacher_turn_number % 3 == 0:
            return ["disengaged_student"]
        return ["high_achiever"]


def _scenario_metadata(scenario_id: str) -> dict[str, str]:
    return SCENARIO_METADATA.get(
        scenario_id,
        {
            "lesson_title": DEFAULT_LESSON_TITLE,
            "learning_objective": DEFAULT_LEARNING_OBJECTIVE,
        },
    )


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()
