"""OpenAI-backed student response client with deterministic fallback.

Phase 2 must be demoable without exposing or requiring an API key. If OPENAI_API_KEY
is available, this client calls OpenAI. Otherwise, it returns persona-aware local
fallback responses so the pixel classroom remains functional.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

from app.session_models import ClassroomTurn, StudentPersona


@dataclass
class StudentReply:
    message: str
    source: str


class StudentResponseClient:
    def __init__(self) -> None:
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.model = os.getenv("OPENAI_SIMULATION_MODEL", "gpt-4o-mini")
        self.temperature = float(os.getenv("OPENAI_TEMPERATURE_STUDENT", "0.7"))

    def generate_reply(
        self,
        *,
        persona: StudentPersona,
        teacher_message: str,
        learning_objective: str,
        history: list[ClassroomTurn],
    ) -> StudentReply:
        if self.api_key:
            try:
                return self._generate_openai_reply(
                    persona=persona,
                    teacher_message=teacher_message,
                    learning_objective=learning_objective,
                    history=history,
                )
            except Exception:
                # Keep demo resilient. Later phases should log exceptions explicitly.
                return self._fallback_reply(persona, teacher_message, history)
        return self._fallback_reply(persona, teacher_message, history)

    def _generate_openai_reply(
        self,
        *,
        persona: StudentPersona,
        teacher_message: str,
        learning_objective: str,
        history: list[ClassroomTurn],
    ) -> StudentReply:
        from openai import OpenAI

        client = OpenAI(api_key=self.api_key)
        recent_history = "\n".join(
            f"{turn.speaker_name}: {turn.message}" for turn in history[-8:]
        )
        prompt = f"""
You are simulating one student in a classroom teaching demo.

Learning objective: {learning_objective}
Student persona: {persona.name} — {persona.learning_profile}
Misconception tendency: {persona.misconception_bias}

Recent classroom history:
{recent_history}

Teacher just said:
{teacher_message}

Reply as this student in 1-2 short natural sentences. Do not mention you are an AI.
""".strip()

        response = client.chat.completions.create(
            model=self.model,
            temperature=self.temperature,
            messages=[
                {"role": "system", "content": "You are a concise virtual student in a teacher-training simulation."},
                {"role": "user", "content": prompt},
            ],
        )
        content = response.choices[0].message.content or "I am not sure yet."
        return StudentReply(message=content.strip(), source="openai")

    def _fallback_reply(
        self, persona: StudentPersona, teacher_message: str, history: list[ClassroomTurn]) -> StudentReply:
        turn_count = len([t for t in history if t.speaker_role == "teacher"])
        lower = teacher_message.lower()

        if persona.persona_id == "misconception_student":
            if turn_count <= 2:
                msg = "Does it only print once because there is only one print line?"
            elif "trace" in lower or "step" in lower:
                msg = "Oh, so the same print line runs again for each item in the list?"
            else:
                msg = "I still mix up the written line and how many times it executes."
        elif persona.persona_id == "high_achiever":
            msg = "I think the loop prints 1, then 2, then 3 because number changes each iteration."
        elif persona.persona_id == "anxious_beginner":
            msg = "Could we slow down and make a small trace table? I am not confident yet."
        elif persona.persona_id == "disengaged_student":
            msg = "I am not sure. I understand that it repeats, but I do not know how many times."
        else:
            msg = "What would happen if the list had four numbers instead of three?"

        return StudentReply(message=msg, source="fallback")
