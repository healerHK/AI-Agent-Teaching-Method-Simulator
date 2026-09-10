"""Transcript-first scenario library and readiness testing service."""

from __future__ import annotations

import json
from pathlib import Path

from app.config import DATA_ROOT, ensure_data_dirs
from app.models import BenchmarkTranscript, Turn
from app.transcript_dialogue_scripts import get_enriched_dialogue_context
from app.transcript_models import (
    LessonPhaseDraft,
    RenderedStudentPrompt,
    ScenarioValidationCheck,
    StudentPromptParameters,
    StudentPromptProfile,
    TranscriptScenario,
    TranscriptScenarioListResponse,
    TranscriptScenarioSaveResponse,
    TranscriptScenarioSummary,
    TranscriptScenarioTestResponse,
    TranscriptTurnDraft,
)

TRANSCRIPT_SCENARIO_ROOT = DATA_ROOT / "transcript_scenarios"
REQUIRED_TRANSCRIPT_TURNS = 64

STUDENT_PROMPT_TEMPLATE = """You are {name}, a {role} in a {education_level} {subject} class.
Course context: {course_context}
Lesson objective: {learning_objectives}
Student background: {background}
Learning needs: {learning_needs}
Prior knowledge: {prior_knowledge}
Participation style: {participation_style}
Confidence level: {confidence}
Misconception strength: {misconception_strength}
Affect/emotion: {affect}
Language level: {language_level}
Response length: {response_length}
Scenario misconceptions to make visible when relevant: {misconception_targets}
Special behaviour instructions: {prompt_instructions}

Respond as this student only. Stay consistent with the profile. Reveal confusion naturally when the teacher prompt touches your misconception. Do not solve the lesson for other students unless your role indicates high confidence or dominance."""

TEACHER_PROMPT_TEMPLATE = """You are the teacher in a 30-minute {education_level} {subject} classroom dialogue.
Follow the supplied classroom-dialogue style: short greeting/opening, labelled lesson parts, balanced teacher-student questioning, misconception repair, differentiated practice, final review, and homework. Keep the explanation distributed across the full 30-minute dialogue rather than placing a very long lecture at the start.
Do not assume all students understand until the transcript shows evidence."""


class TranscriptScenarioNotFound(FileNotFoundError):
    pass


class TranscriptScenarioService:
    def __init__(self, root: Path = TRANSCRIPT_SCENARIO_ROOT) -> None:
        self.root = root
        ensure_data_dirs()
        self.root.mkdir(parents=True, exist_ok=True)
        self.ensure_seed_scenarios()

    def ensure_seed_scenarios(self) -> None:
        for scenario in build_seed_scenarios():
            path = self._path_for_id(scenario.scenario_id)
            if not path.exists():
                self._write_scenario(path, scenario)
                continue
            existing = TranscriptScenario.model_validate(json.loads(path.read_text(encoding="utf-8")))
            changed = _ensure_minimum_transcript_turns(existing)
            changed = _ensure_short_opening_greeting(existing) or changed
            if changed:
                self._write_scenario(path, existing)

    def list_scenarios(self) -> TranscriptScenarioListResponse:
        scenarios = [self.load_scenario(path.stem) for path in sorted(self.root.glob("*.json"))]
        summaries = [
            TranscriptScenarioSummary(
                scenario_id=scenario.scenario_id,
                title=scenario.title,
                subject=scenario.subject,
                education_level=scenario.education_level,
                estimated_duration_minutes=scenario.estimated_duration_minutes,
                student_count=len(scenario.student_profiles),
                turn_count=len(scenario.transcript_turns),
                misconception_count=len(scenario.misconception_targets),
            )
            for scenario in scenarios
        ]
        subjects = sorted({scenario.subject for scenario in scenarios})
        levels = sorted({scenario.education_level for scenario in scenarios})
        return TranscriptScenarioListResponse(
            scenarios=summaries,
            library_summary={
                "scenario_count": len(scenarios),
                "subjects": subjects,
                "education_levels": levels,
                "duration_policy": "Every seed scenario is designed as a 30-minute editable transcript draft.",
                "live_mode_scope": "Not used here; this module prepares fixed transcripts before live-mode work.",
            },
        )

    def load_scenario(self, scenario_id: str) -> TranscriptScenario:
        path = self._path_for_id(scenario_id)
        if not path.exists():
            raise TranscriptScenarioNotFound(scenario_id)
        return TranscriptScenario.model_validate(json.loads(path.read_text(encoding="utf-8")))

    def save_scenario(self, scenario: TranscriptScenario) -> TranscriptScenarioSaveResponse:
        path = self._path_for_id(scenario.scenario_id)
        self._write_scenario(path, scenario)
        return TranscriptScenarioSaveResponse(scenario_id=scenario.scenario_id, path=str(path))

    def render_student_prompts(self, scenario_id: str) -> list[RenderedStudentPrompt]:
        scenario = self.load_scenario(scenario_id)
        return [_render_prompt(scenario, student) for student in scenario.student_profiles]

    def run_readiness_test(self, scenario_id: str) -> TranscriptScenarioTestResponse:
        scenario = self.load_scenario(scenario_id)
        checks = _validate_scenario_readiness(scenario)
        prompts = [_render_prompt(scenario, student) for student in scenario.student_profiles]
        passed = all(check.status != "fail" for check in checks)
        return TranscriptScenarioTestResponse(
            scenario_id=scenario.scenario_id,
            passed=passed,
            checks=checks,
            rendered_student_prompts=prompts,
            transcript_preview_markdown=_transcript_markdown(scenario),
            next_steps=_next_steps(scenario, passed),
        )

    def to_benchmark_transcript(self, scenario_id: str) -> BenchmarkTranscript:
        scenario = self.load_scenario(scenario_id)
        return scenario_to_benchmark_transcript(scenario)

    def _path_for_id(self, scenario_id: str) -> Path:
        safe = scenario_id.replace("/", "_").replace("\\", "_")
        return self.root / f"{safe}.json"

    def _write_scenario(self, path: Path, scenario: TranscriptScenario) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(scenario.model_dump_json(indent=2), encoding="utf-8")


def scenario_to_benchmark_transcript(scenario: TranscriptScenario) -> BenchmarkTranscript:
    turns = [
        Turn(
            turn_id=turn.turn_id,
            speaker_role=turn.speaker_role,
            speaker_name=turn.speaker_name,
            message=turn.message,
        )
        for turn in sorted(scenario.transcript_turns, key=lambda item: (item.minute, item.turn_id))
    ]
    return BenchmarkTranscript(
        transcript_id=f"scenario_{scenario.scenario_id}",
        scenario_id=scenario.scenario_id,
        variant="weak",
        domain=scenario.subject,
        education_level=scenario.education_level.replace("_", " "),
        learning_objective="; ".join(scenario.learning_objectives),
        turns=turns,
    )


def _render_prompt(scenario: TranscriptScenario, student: StudentPromptProfile) -> RenderedStudentPrompt:
    params = student.parameters
    prompt = scenario.student_prompt_template.format(
        name=student.name,
        role=student.role,
        education_level=scenario.education_level.replace("_", " "),
        subject=scenario.subject,
        course_context=scenario.course_context,
        learning_objectives="; ".join(scenario.learning_objectives),
        background=student.background,
        learning_needs="; ".join(student.learning_needs),
        prior_knowledge=params.prior_knowledge,
        participation_style=params.participation_style,
        confidence=params.confidence,
        misconception_strength=params.misconception_strength,
        affect=params.affect,
        response_length=params.response_length,
        language_level=params.language_level,
        misconception_targets="; ".join(scenario.misconception_targets),
        prompt_instructions=params.prompt_instructions,
    )
    return RenderedStudentPrompt(
        student_id=student.student_id,
        name=student.name,
        role=student.role,
        prompt=prompt,
    )


def _validate_scenario_readiness(scenario: TranscriptScenario) -> list[ScenarioValidationCheck]:
    checks: list[ScenarioValidationCheck] = []

    def add(check_id: str, status: str, message: str) -> None:
        checks.append(ScenarioValidationCheck(check_id=check_id, status=status, message=message))

    add(
        "duration_30_minutes",
        "pass" if scenario.estimated_duration_minutes == 30 else "fail",
        f"Estimated duration is {scenario.estimated_duration_minutes} minutes; target is exactly 30 minutes.",
    )
    add(
        "phase_count",
        "pass" if len(scenario.lesson_phases) >= 5 else "fail",
        f"Scenario has {len(scenario.lesson_phases)} lesson phases; target is at least 5.",
    )
    sorted_phases = sorted(scenario.lesson_phases, key=lambda phase: phase.minute_start)
    phase_covers_30 = bool(sorted_phases) and sorted_phases[0].minute_start == 0 and sorted_phases[-1].minute_end == 30
    no_phase_gaps = all(a.minute_end == b.minute_start for a, b in zip(sorted_phases, sorted_phases[1:]))
    add(
        "phase_coverage",
        "pass" if phase_covers_30 and no_phase_gaps else "warn",
        "Lesson phases cover 0-30 minutes without gaps." if phase_covers_30 and no_phase_gaps else "Check phase minute ranges for gaps or endpoints that do not cover the full 30 minutes.",
    )
    add(
        "student_profiles",
        "pass" if len(scenario.student_profiles) >= 4 else "fail",
        f"Scenario has {len(scenario.student_profiles)} student prompt profiles; target is at least 4.",
    )
    prompt_ready = all(student.parameters.prompt_instructions.strip() for student in scenario.student_profiles)
    add(
        "student_prompt_parameters",
        "pass" if prompt_ready else "fail",
        "Every student has editable prompt instructions and behaviour parameters." if prompt_ready else "One or more students is missing prompt instructions.",
    )
    turn_count_ok = len(scenario.transcript_turns) == REQUIRED_TRANSCRIPT_TURNS
    add(
        "transcript_turn_count",
        "pass" if turn_count_ok else "fail",
        f"Scenario has {len(scenario.transcript_turns)} draft transcript turns; target is exactly {REQUIRED_TRANSCRIPT_TURNS} for a 30-minute lesson.",
    )
    sorted_turns = sorted(scenario.transcript_turns, key=lambda item: (item.minute, item.turn_id))
    dialogue_text = "\n".join(turn.message for turn in sorted_turns)
    required_parts = [f"PART {index}" for index in range(1, 8)]
    has_required_parts = all(part in dialogue_text for part in required_parts)
    has_class_voice = any(turn.speaker_name == "Class" for turn in sorted_turns)
    opening_is_short = bool(sorted_turns) and _word_count(sorted_turns[0].message) <= 40
    dialogue_ok = has_required_parts and has_class_voice and opening_is_short
    add(
        "balanced_dialogue_structure",
        "pass" if dialogue_ok else "fail",
        (
            "Transcript uses a balanced 30-minute classroom-dialogue structure with short opening, Class voice, and PART 1-7 flow."
            if dialogue_ok
            else "Match the supplied dialogue format: short opening, Class greeting/closure, and labelled PART 1-7 lesson flow."
        ),
    )
    tags = {tag for turn in scenario.transcript_turns for tag in turn.pedagogical_tags}
    add(
        "misconception_event",
        "pass" if "misconception_event" in tags else "fail",
        "Transcript includes at least one misconception event." if "misconception_event" in tags else "Add a student misconception event before testing.",
    )
    add(
        "formative_assessment",
        "pass" if "formative_assessment" in tags else "warn",
        "Transcript includes a formative assessment checkpoint." if "formative_assessment" in tags else "Add a formative assessment checkpoint for better evaluation.",
    )
    add(
        "editable_notes",
        "pass" if scenario.editable_notes.strip() else "warn",
        "Editable notes are present for researcher revisions." if scenario.editable_notes.strip() else "Add notes about what should be checked before expert testing.",
    )
    return checks


def _transcript_markdown(scenario: TranscriptScenario) -> str:
    lines = [
        f"# {scenario.title}",
        f"Subject: {scenario.subject}",
        f"Level: {scenario.education_level}",
        f"Duration: {scenario.estimated_duration_minutes} minutes",
        "",
        "## Draft transcript",
    ]
    for turn in sorted(scenario.transcript_turns, key=lambda item: (item.minute, item.turn_id)):
        tags = f" [{', '.join(turn.pedagogical_tags)}]" if turn.pedagogical_tags else ""
        lines.append(f"- {turn.minute:02d}:00 · {turn.speaker_name} ({turn.speaker_role}){tags}: {turn.message}")
    return "\n".join(lines)


def _next_steps(scenario: TranscriptScenario, passed: bool) -> list[str]:
    steps = [
        "Review the transcript turns and edit any teacher/student wording before evaluator testing.",
        "Open rendered student prompts and adjust confidence, misconception strength, participation style, and special instructions.",
        "Keep the scenario fixed/frozen before running baseline vs TIL evaluation so comparisons are fair.",
    ]
    if not passed:
        steps.insert(0, "Fix failed readiness checks before using this scenario for benchmark testing.")
    if "requires_source_materials" in scenario.evaluator_focus:
        steps.append("Attach or summarise relevant lesson materials before finalising this scenario.")
    return steps


def build_seed_scenarios() -> list[TranscriptScenario]:
    specs = [
        {
            "id": "hs_python_loops_30m",
            "title": "Python for-loops: iterator protocol, tracing, and correctness reasoning",
            "subject": "Computer Science",
            "level": "college",
            "context": "First-year college programming class analysing Python iteration semantics through a data-cleaning script.",
            "concept": "Python for-loops consume iterables through the iterator protocol, bind target names each iteration, and require state tracing plus invariants for correctness reasoning.",
            "example": "for index, reading in enumerate(readings): total += reading",
            "misconceptions": [
                "One written loop-body line means only one execution.",
                "range stop values are included, so range(3) yields 1, 2, 3.",
                "A loop that works on one representative input is proven correct.",
            ],
            "materials": ["Python iterator-protocol snippet", "state trace and loop-invariant worksheet", "edge-case test checklist"],
        },
        {
            "id": "hs_quadratic_functions_30m",
            "title": "Quadratic functions: structural forms, discriminant, and modelling interpretation",
            "subject": "Mathematics",
            "level": "college",
            "context": "College algebra class connecting standard, factored, and vertex forms to graph structure and modelling interpretation.",
            "concept": "Equivalent quadratic forms reveal intercepts, vertex, axis of symmetry, discriminant information, and transformation behaviour.",
            "example": "y = x^2 - 4x + 3",
            "misconceptions": [
                "The constant term is always the x-intercept.",
                "A negative b value means the parabola opens downward.",
                "The vertex can be found by guessing from the graph only.",
            ],
            "materials": ["quadratic form comparison sheet", "graphing calculator or plotting grid", "discriminant and completing-square worksheet"],
        },
        {
            "id": "hs_newton_laws_30m",
            "title": "Newtonian mechanics: free-body diagrams, net force, and system boundaries",
            "subject": "Physics",
            "level": "college",
            "context": "First-year university physics class analysing motion with free-body diagrams in inertial reference frames.",
            "concept": "Net external force determines acceleration after system boundary, force directions, and reference frame are specified.",
            "example": "A dynamics cart pulled across a low-friction track while kinetic friction opposes motion.",
            "misconceptions": [
                "An object moving forward must have a forward net force.",
                "Heavier objects always fall faster in normal classroom examples.",
                "Action-reaction forces cancel because they are equal and opposite.",
            ],
            "materials": ["free-body diagram worksheet", "force sensor/dynamics-cart demonstration", "Newton's laws misconception checklist"],
        },
        {
            "id": "college_cellular_respiration_30m",
            "title": "Cellular respiration: ATP production and energy transfer",
            "subject": "Biology",
            "level": "college",
            "context": "First-year biology class reviewing how cells convert glucose into usable ATP.",
            "concept": "Cellular respiration transfers energy from glucose to ATP through linked stages.",
            "example": "glycolysis -> Krebs cycle -> electron transport chain",
            "misconceptions": [
                "Energy is created from nothing during respiration.",
                "Respiration and breathing are the same biological process.",
                "Most ATP is made directly in glycolysis.",
            ],
            "materials": ["respiration pathway diagram", "ATP yield summary"],
        },
        {
            "id": "college_stoichiometry_30m",
            "title": "Stoichiometry: mole ratios and limiting reactants",
            "subject": "Chemistry",
            "level": "college",
            "context": "General chemistry class solving reaction-quantity problems.",
            "concept": "Balanced equations define mole ratios used to identify limiting reactants and product yield.",
            "example": "2H2 + O2 -> 2H2O",
            "misconceptions": [
                "Grams in the equation can be compared directly without converting to moles.",
                "The reactant with the smaller mass is always limiting.",
                "Coefficients only balance atoms and do not affect calculations.",
            ],
            "materials": ["balanced equation", "mole conversion table"],
        },
        {
            "id": "uni_hypothesis_testing_30m",
            "title": "Hypothesis testing: p-values, significance, and interpretation",
            "subject": "Statistics",
            "level": "university",
            "context": "Introductory university statistics class interpreting test results from a small study.",
            "concept": "A p-value measures compatibility with the null model; it is not the probability that the null is true.",
            "example": "Two-sample test comparing mean study hours between groups.",
            "misconceptions": [
                "p = 0.03 means a 3% chance the null hypothesis is true.",
                "Statistical significance automatically means practical importance.",
                "Failing to reject the null proves there is no effect.",
            ],
            "materials": ["test output table", "null/alternative hypothesis examples"],
        },
        {
            "id": "uni_microeconomics_elasticity_30m",
            "title": "Microeconomics: price elasticity and revenue reasoning",
            "subject": "Economics",
            "level": "university",
            "context": "First-year microeconomics class analysing demand elasticity and total revenue.",
            "concept": "Price elasticity of demand describes responsiveness of quantity demanded to price changes.",
            "example": "A cafe increases coffee price by 10% and quantity sold falls by 5%.",
            "misconceptions": [
                "Elasticity is the same as slope.",
                "Raising price always increases revenue.",
                "A percentage change in price and quantity should use raw unit differences only.",
            ],
            "materials": ["demand schedule", "revenue calculation worksheet"],
        },
        {
            "id": "uni_primary_source_analysis_30m",
            "title": "Primary source analysis: evidence, context, and historical claims",
            "subject": "History / Humanities",
            "level": "university",
            "context": "University humanities seminar practising how to build a claim from a primary source excerpt.",
            "concept": "Historical claims should connect textual evidence with context, audience, purpose, and limitation.",
            "example": "A wartime speech excerpt used to infer public persuasion strategies.",
            "misconceptions": [
                "A primary source is automatically objective.",
                "Quoting a line is enough without explaining context or purpose.",
                "The author's intent can be known with certainty from one excerpt.",
            ],
            "materials": ["primary source excerpt", "source analysis worksheet"],
        },
    ]
    return [_scenario_from_spec(spec) for spec in specs]


def _scenario_from_spec(spec: dict[str, object]) -> TranscriptScenario:
    scenario_id = str(spec["id"])
    subject = str(spec["subject"])
    level = str(spec["level"])
    concept = str(spec["concept"])
    example = str(spec["example"])
    misconceptions = list(spec["misconceptions"])
    students = _default_students(subject, level)
    return TranscriptScenario(
        scenario_id=scenario_id,
        title=str(spec["title"]),
        subject=subject,
        education_level=level,  # type: ignore[arg-type]
        course_context=str(spec["context"]),
        estimated_duration_minutes=30,
        learning_objectives=[
            concept,
            "Students explain their reasoning using evidence from the worked example.",
            "Students identify and repair at least one common misconception during guided practice.",
        ],
        prerequisite_knowledge=[
            "Basic vocabulary for the topic.",
            "Ability to follow a worked example with teacher support.",
        ],
        misconception_targets=[str(item) for item in misconceptions],
        materials_needed=[str(item) for item in spec["materials"]],
        lesson_phases=_default_phases(subject, concept),
        student_profiles=students,
        transcript_turns=_default_turns(example, misconceptions, students, subject=subject, level=level, concept=concept),
        teacher_prompt_template=TEACHER_PROMPT_TEMPLATE,
        student_prompt_template=STUDENT_PROMPT_TEMPLATE,
        evaluator_focus=[
            "conceptual_accuracy",
            "misconception_response",
            "scaffolding",
            "formative_assessment",
            "evidence_grounding",
        ],
        editable_notes=(
            "Draft 30-minute transcript scenario. Review subject accuracy and student prompts before benchmark testing. "
            "If the topic requires precise curriculum alignment, attach teacher notes, textbook pages, slides, or assessment rubrics."
        ),
    )


def _default_phases(subject: str, concept: str) -> list[LessonPhaseDraft]:
    return [
        LessonPhaseDraft(
            phase_id="opening_diagnostic",
            title="Opening diagnostic question",
            minute_start=0,
            minute_end=5,
            teacher_goal=f"Activate prior knowledge and ask students to predict or explain the core idea: {concept}",
            expected_student_events=["quick confident answer", "hesitation", "surface-level prior knowledge"],
            evidence_focus=["diagnostic_question", "participation_distribution"],
        ),
        LessonPhaseDraft(
            phase_id="concept_modelling",
            title="Concept modelling with worked example",
            minute_start=5,
            minute_end=11,
            teacher_goal=f"Model the key {subject} concept with a concrete worked example.",
            expected_student_events=["students ask for clarification", "one student overgeneralises"],
            evidence_focus=["conceptual_accuracy", "modelling", "teacher_explanation"],
        ),
        LessonPhaseDraft(
            phase_id="guided_practice_misconception",
            title="Guided practice and misconception event",
            minute_start=11,
            minute_end=20,
            teacher_goal="Elicit student reasoning, expose a misconception, and scaffold correction.",
            expected_student_events=["misconception is voiced", "peer comparison", "anxious student needs stepwise support"],
            evidence_focus=["misconception_event", "scaffolding", "student_reasoning"],
        ),
        LessonPhaseDraft(
            phase_id="formative_check",
            title="Formative assessment checkpoint",
            minute_start=20,
            minute_end=26,
            teacher_goal="Check whether students can independently apply the concept and justify the answer.",
            expected_student_events=["exit-style response", "partial reasoning", "remaining uncertainty"],
            evidence_focus=["formative_assessment", "feedback_actionability"],
        ),
        LessonPhaseDraft(
            phase_id="reflection_closure",
            title="Reflection and closure",
            minute_start=26,
            minute_end=30,
            teacher_goal="Summarise the concept, name the misconception repair, and set a next-step learning goal.",
            expected_student_events=["student restates rule", "teacher identifies next step"],
            evidence_focus=["closure", "next_step_teaching_action"],
        ),
    ]


def _default_students(subject: str, level: str) -> list[StudentPromptProfile]:
    level_label = level.replace("_", " ")
    return [
        StudentPromptProfile(
            student_id="student_excellent_quick",
            name="Alice",
            role="excellent student, quick thinker",
            background=f"Consistently performs strongly in {subject} and often sees the main idea quickly.",
            learning_needs=["needs conceptual challenge", "should explain reasoning without dominating"],
            parameters=StudentPromptParameters(
                participation_style="answers quickly and volunteers first when the teacher asks a conceptual question",
                confidence=0.90,
                misconception_strength=0.12,
                prior_knowledge="strong prior knowledge with good conceptual vocabulary",
                affect="confident and engaged",
                response_length="medium",
                language_level=f"clear {level_label} academic language",
                prompt_instructions="Give accurate answers quickly, then add reasoning when Mr. Anderson asks for evidence. Avoid solving every question before weaker students try.",
            ),
        ),
        StudentPromptProfile(
            student_id="student_calculation_strong",
            name="Ben",
            role="good student, strong at calculations",
            background=f"Usually solves quantitative or procedural {subject} tasks accurately.",
            learning_needs=["needs to connect calculations with concepts", "can support peers with step-by-step working"],
            parameters=StudentPromptParameters(
                participation_style="responds confidently to formula, calculation, and worked-example prompts",
                confidence=0.78,
                misconception_strength=0.25,
                prior_knowledge="good procedural knowledge and generally reliable calculation skills",
                affect="focused and practical",
                response_length="medium",
                language_level=f"precise {level_label} student language",
                prompt_instructions="When a calculation or procedure appears, show the formula or sequence clearly. Occasionally need Mr. Anderson to ask for the meaning behind the calculation.",
            ),
        ),
        StudentPromptProfile(
            student_id="student_thoughtful_quiet",
            name="Chloe",
            role="above-average student, quiet but thoughtful",
            background=f"Understands many {subject} ideas but tends to wait before speaking publicly.",
            learning_needs=["needs direct invitation", "benefits from time to phrase careful reasoning"],
            parameters=StudentPromptParameters(
                participation_style="answers after being invited, often with careful reasoning or a clarifying distinction",
                confidence=0.66,
                misconception_strength=0.30,
                prior_knowledge="above-average understanding with thoughtful but sometimes slow verbal responses",
                affect="quiet, attentive, and reflective",
                response_length="medium",
                language_level=f"thoughtful {level_label} academic language",
                prompt_instructions="Do not answer first. When Mr. Anderson invites you, give a careful explanation, comparison, or correction that helps the class see the structure.",
            ),
        ),
        StudentPromptProfile(
            student_id="student_average_distracted",
            name="Daniel",
            role="average student, sometimes distracted",
            background=f"Can follow familiar {subject} examples but loses focus during longer explanations.",
            learning_needs=["needs concrete examples", "needs re-engagement during checks"],
            parameters=StudentPromptParameters(
                participation_style="gives partial or rushed answers unless the example is concrete and relatable",
                confidence=0.48,
                misconception_strength=0.50,
                prior_knowledge="uneven understanding with surface-level shortcuts",
                affect="occasionally distracted but responsive when called by name",
                response_length="short",
                language_level=f"brief {level_label} student language",
                prompt_instructions="Sometimes make a plausible mistake or incomplete claim. Improve when Mr. Anderson redirects you to the example or asks you to compare two cases.",
            ),
        ),
        StudentPromptProfile(
            student_id="student_hardworking_weak",
            name="Lily",
            role="weak in the subject but hardworking",
            background=f"Finds {subject} challenging but tries hard and asks honest clarification questions.",
            learning_needs=["needs patient explanation", "benefits from real-life examples and guided practice"],
            parameters=StudentPromptParameters(
                participation_style="asks clarification questions and attempts practice after scaffolding",
                confidence=0.36,
                misconception_strength=0.62,
                prior_knowledge="basic vocabulary is present but concepts need reinforcement",
                affect="hardworking, careful, and sometimes worried",
                response_length="short",
                language_level=f"simple {level_label} student language",
                prompt_instructions="Ask sincere questions when a term or formula is unclear. With scaffolding, give correct short answers and show gradual confidence growth.",
            ),
        ),
        StudentPromptProfile(
            student_id="student_low_confidence",
            name="Noah",
            role="weak student, lacks confidence",
            background=f"Often doubts his {subject} answers and needs low-pressure prompts to participate.",
            learning_needs=["needs reassurance", "needs step-by-step questioning and successful low-stakes attempts"],
            parameters=StudentPromptParameters(
                participation_style="responds briefly when directly invited and may reveal a misconception or uncertainty",
                confidence=0.28,
                misconception_strength=0.68,
                prior_knowledge="fragile understanding with several common misconceptions",
                affect="nervous but willing to try when encouraged",
                response_length="short",
                language_level=f"simple {level_label} student language",
                prompt_instructions="Reveal uncertainty honestly. Give short answers first, then improve after Mr. Anderson breaks the task into smaller steps.",
            ),
        ),
    ]



def _word_count(text: str) -> int:
    return len([word for word in text.replace("—", " ").replace("/", " ").split() if word.strip()])


def _extract_concept_from_scenario(scenario: TranscriptScenario) -> str:
    if scenario.learning_objectives:
        return scenario.learning_objectives[0]
    return f"the central {scenario.subject} concept for this lesson"


def _ensure_short_opening_greeting(scenario: TranscriptScenario) -> bool:
    turns = sorted(scenario.transcript_turns, key=lambda item: (item.minute, item.turn_id))
    if not turns:
        return False
    first_turn = turns[0]
    first_ready = (
        first_turn.speaker_role == "teacher"
        and first_turn.speaker_name == "Mr. Anderson"
        and _word_count(first_turn.message) <= 40
        and "greeting" in first_turn.pedagogical_tags
    )
    if first_ready:
        return False

    example = _extract_example_from_scenario(scenario)
    concept = _extract_concept_from_scenario(scenario)
    first_turn.minute = 0
    first_turn.speaker_role = "teacher"
    first_turn.speaker_name = "Mr. Anderson"
    first_turn.student_id = None
    first_turn.message = _opening_lecture_message(
        subject=scenario.subject,
        level=scenario.education_level,
        concept=concept,
        example=example,
        misconceptions=scenario.misconception_targets,
    )
    first_turn.pedagogical_tags = [
        "part_1_introduction",
        "greeting",
    ]
    scenario.transcript_turns = sorted(scenario.transcript_turns, key=lambda item: (item.minute, item.turn_id))
    return True


def _opening_lecture_message(
    *,
    subject: str,
    level: str,
    concept: str,
    example: str,
    misconceptions: list[object],
) -> str:
    return "Good morning, everyone."


def _ensure_minimum_transcript_turns(scenario: TranscriptScenario) -> bool:
    """Append richer minute-by-minute draft turns to old scenario JSON files.

    Existing edits are preserved. The function only appends missing canonical turns
    until the scenario has at least REQUIRED_TRANSCRIPT_TURNS turns.
    """

    if len(scenario.transcript_turns) >= REQUIRED_TRANSCRIPT_TURNS:
        return False
    example = _extract_example_from_scenario(scenario)
    concept = _extract_concept_from_scenario(scenario)
    canonical_turns = _default_turns(
        example,
        scenario.misconception_targets,
        scenario.student_profiles,
        subject=scenario.subject,
        level=scenario.education_level,
        concept=concept,
    )
    existing_ids = {turn.turn_id for turn in scenario.transcript_turns}
    for turn in canonical_turns:
        if len(scenario.transcript_turns) >= REQUIRED_TRANSCRIPT_TURNS:
            break
        if turn.turn_id in existing_ids:
            continue
        scenario.transcript_turns.append(turn)
        existing_ids.add(turn.turn_id)
    scenario.transcript_turns = sorted(scenario.transcript_turns, key=lambda item: (item.minute, item.turn_id))
    return len(scenario.transcript_turns) >= REQUIRED_TRANSCRIPT_TURNS


def _extract_example_from_scenario(scenario: TranscriptScenario) -> str:
    markers = [
        ("look at this example:", ". What"),
        ("worked example:", ". First"),
        ("anchor example today is:", ". Treat"),
    ]
    for turn in scenario.transcript_turns:
        lower_message = turn.message.lower()
        for marker, end_marker in markers:
            if marker in lower_message:
                after_marker = turn.message[lower_message.index(marker) + len(marker):]
                return after_marker.split(end_marker, 1)[0].strip()
    if scenario.materials_needed:
        return scenario.materials_needed[0]
    return "the worked example from this lesson"


def _dialogue_context(subject: str, concept: str, example: str) -> dict[str, str]:
    return get_enriched_dialogue_context(subject, concept, example)


def _default_turns(
    example: str,
    misconceptions: list[object],
    students: list[StudentPromptProfile],
    *,
    subject: str = "the subject",
    level: str = "the class",
    concept: str = "the core concept for this lesson",
) -> list[TranscriptTurnDraft]:
    scene = _dialogue_context(subject, concept, example)
    opening_lecture = _opening_lecture_message(
        subject=subject,
        level=level,
        concept=concept,
        example=example,
        misconceptions=misconceptions,
    )
    student_names = {student.student_id: student.name for student in students}
    raw_turns = [
        (0, "teacher", None, opening_lecture, ["part_1_introduction", "greeting"]),
        (1, "controller", None, "Good morning, sir.", ["class_greeting"]),
        (1, "teacher", None, f"PART 1 — INTRODUCTION. Before we practise, connect the explanation to this situation: {scene['real_life']}. {scene['diagnostic_question']}", ["opening", "diagnostic_question"]),
        (2, "student", "student_low_confidence", scene["nam_first"], ["prior_knowledge_probe", "low_confidence"]),
        (2, "teacher", None, "Good attempt, Noah. Why do you think that?", ["probing_reasoning", "reassurance"]),
        (3, "student", "student_low_confidence", scene["reason_gap"], ["reasoning_gap"]),
        (3, "teacher", None, "That uncertainty is useful. Alice, can you make the idea more precise?", ["participation_distribution"]),
        (4, "student", "student_excellent_quick", scene["an_precision"], ["quick_answer", "conceptual_accuracy"]),
        (4, "teacher", None, scene["teacher_bridge"], ["phase_transition", "teacher_explanation"]),
        (5, "student", "student_hardworking_weak", scene["lan_question"], ["clarification_question", "misconception_event"]),
        (5, "teacher", None, scene["misconception1_response"], ["misconception_response", "evidence_grounding"]),
        (6, "student", "student_thoughtful_quiet", scene["chi_support"], ["student_reasoning", "quiet_student_invited"]),
        (6, "student", "student_calculation_strong", scene["binh_support"], ["procedural_reasoning", "peer_support"]),
        (7, "student", "student_low_confidence", scene["noah_uptake"], ["uptake", "metacognitive_question"]),
        (7, "teacher", None, scene["teacher_evidence_explanation"], ["teacher_explanation", "evidence_prompt"]),
        (8, "student", "student_average_distracted", scene["dung_confusion"], ["surface_shortcut", "misconception_event"]),
        (8, "teacher", None, scene["dung_feedback"], ["misconception_response", "scaffolding"]),
        (9, "teacher", None, scene["quick_q1"], ["quick_check", "formative_assessment"]),
        (9, "student", "student_thoughtful_quiet", scene["quick_a1"], ["formative_assessment", "student_reasoning"]),
        (10, "teacher", None, scene["quick_q2"], ["quick_check", "evidence_verification"]),
        (10, "student", "student_calculation_strong", scene["quick_a2"], ["assessment_evidence"]),
        (11, "teacher", None, scene["reengage_q"], ["inclusive_questioning", "participation_distribution"]),
        (11, "student", "student_average_distracted", scene["reengage_a"], ["re_engagement", "misconception_repair"]),
        (12, "teacher", None, scene["teacher_model"], ["phase_transition", "worked_example", "modelling"]),
        (12, "teacher", None, scene["worked_prompt"], ["worked_example", "teacher_question"]),
        (13, "student", "student_excellent_quick", scene["worked_an"], ["worked_example", "student_reasoning"]),
        (13, "teacher", None, "Ben, continue the worked example using the next calculation or procedure step.", ["targeted_question", "procedural_scaffolding"]),
        (14, "student", "student_calculation_strong", scene["worked_binh"], ["worked_example", "calculation_reasoning"]),
        (14, "teacher", None, scene["why_question"], ["scaffolding", "low_confidence_support"]),
        (15, "student", "student_low_confidence", scene["nam_why"], ["uptake", "confidence_growth"]),
        (15, "student", "student_hardworking_weak", scene["lan_transfer"], ["clarification_question", "transfer_probe"]),
        (16, "teacher", None, scene["transfer_teacher"], ["transfer", "teacher_explanation"]),
        (16, "student", "student_thoughtful_quiet", scene["chi_transfer"], ["transfer_reasoning", "student_reasoning"]),
        (17, "student", "student_average_distracted", scene["dung_mistake"], ["secondary_misconception", "misconception_event"]),
        (17, "teacher", None, scene["misconception2_response"], ["misconception_response", "evidence_grounding"]),
        (18, "student", "student_excellent_quick", scene["alice_transfer"], ["peer_reasoning", "transfer"]),
        (18, "teacher", None, scene["phase5_intro"], ["phase_transition", "differentiated_practice"]),
        (19, "teacher", None, scene["practice_lan_q"], ["differentiated_practice", "low_confidence_support"]),
        (19, "student", "student_hardworking_weak", scene["practice_lan_a"], ["scaffolded_success", "formative_assessment"]),
        (20, "teacher", None, scene["practice_dung_q"], ["differentiated_practice", "re_engagement"]),
        (20, "student", "student_average_distracted", scene["practice_dung_a"], ["misconception_repair", "formative_assessment"]),
        (21, "teacher", None, scene["practice_chi_q"], ["differentiated_practice"]),
        (21, "student", "student_thoughtful_quiet", scene["practice_chi_a"], ["student_reasoning", "evidence_use"]),
        (22, "teacher", None, scene["practice_binh_q"], ["differentiated_practice"]),
        (22, "student", "student_calculation_strong", scene["practice_binh_a"], ["calculation_reasoning", "formative_assessment"]),
        (23, "teacher", None, scene["extension_an_q"], ["extension_question"]),
        (23, "student", "student_excellent_quick", scene["extension_an_a"], ["transfer_reasoning", "extension_channelled"]),
        (24, "teacher", None, scene["nam_check_q"], ["low_confidence_support", "metacognition"]),
        (24, "student", "student_low_confidence", scene["nam_check_a"], ["confidence_growth", "metacognition"]),
        (25, "teacher", None, scene["misconception3_prompt"], ["phase_transition", "misconception_event"]),
        (25, "student", "student_hardworking_weak", scene["misconception3_a"], ["misconception_repair", "student_reasoning"]),
        (26, "student", "student_average_distracted", scene["daniel_reflection"], ["reflection", "metacognitive_question"]),
        (26, "teacher", None, scene["teacher_note_action"], ["metacognition", "feedback_actionability"]),
        (27, "teacher", None, scene["final_q1"], ["final_review", "formative_assessment"]),
        (27, "student", "student_excellent_quick", scene["final_law1"], ["closure", "student_summary"]),
        (28, "teacher", None, scene["final_q2"], ["final_review"]),
        (28, "student", "student_calculation_strong", scene["final_law2"], ["closure", "student_summary"]),
        (28, "teacher", None, scene["final_q3"], ["final_review"]),
        (29, "student", "student_thoughtful_quiet", scene["final_law3"], ["closure", "student_summary"]),
        (29, "teacher", None, scene["noah_summary_q"], ["final_review", "low_confidence_support"]),
        (29, "student", "student_low_confidence", scene["noah_summary_a"], ["closure", "confidence_growth"]),
        (30, "student", "student_hardworking_weak", "What is our homework, sir?", ["homework_question"]),
        (30, "teacher", None, scene["homework"], ["homework", "next_step_teaching_action"]),
        (30, "controller", None, "Goodbye, sir.", ["class_closure"]),
    ]
    turns: list[TranscriptTurnDraft] = []
    for index, (minute, role, student_id, message, tags) in enumerate(raw_turns, start=1):
        if role == "teacher":
            speaker_name = "Mr. Anderson"
        elif role == "controller":
            speaker_name = "Class"
        else:
            speaker_name = student_names[str(student_id)]
        turns.append(
            TranscriptTurnDraft(
                turn_id=f"turn_{index:03d}",
                minute=minute,
                speaker_role=role,  # type: ignore[arg-type]
                speaker_name=speaker_name,
                student_id=student_id,
                message=message,
                pedagogical_tags=tags,
            )
        )
    return turns
