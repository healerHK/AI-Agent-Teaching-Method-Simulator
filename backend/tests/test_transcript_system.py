from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app
from app.transcript_service import TranscriptScenarioService


EXPECTED_STUDENT_NAMES = ["Alice", "Ben", "Chloe", "Daniel", "Lily", "Noah"]
EXPECTED_PARTS = [
    "PART 1 — INTRODUCTION",
    "PART 2 — CONCEPT EXPLANATION",
    "PART 3 — QUICK CHECK",
    "PART 4 — WORKED EXAMPLE",
    "PART 5 — DIFFERENTIATED PRACTICE",
    "PART 6 — MISCONCEPTION REPAIR",
    "PART 7 — FINAL REVIEW",
]
SUBJECT_ENRICHMENT_MARKERS = {
    "hs_python_loops_30m": ["iterator", "state trace", "off-by-one"],
    "hs_quadratic_functions_30m": ["axis of symmetry", "discriminant", "completing the square"],
    "hs_newton_laws_30m": ["free-body diagram", "inertial reference frame", "act on different bodies"],
    "college_cellular_respiration_30m": ["NADH", "proton-motive force", "chemiosmosis"],
    "college_stoichiometry_30m": ["stoichiometric coefficients", "limiting reagent", "theoretical yield"],
    "uni_hypothesis_testing_30m": ["sampling distribution", "Type I error", "effect size"],
    "uni_microeconomics_elasticity_30m": ["midpoint formula", "total revenue test", "elasticity is unit-free"],
    "uni_primary_source_analysis_30m": ["sourcing", "contextualization", "corroboration"],
}


def _first_turn_word_count(scenario: dict) -> int:
    first_turn = sorted(scenario["transcript_turns"], key=lambda item: (item["minute"], item["turn_id"]))[0]
    return len(first_turn["message"].split())


def _scenario_text(scenario) -> str:
    return "\n".join(turn.message for turn in sorted(scenario.transcript_turns, key=lambda item: (item.minute, item.turn_id)))


def test_transcript_scenario_library_seeds_diverse_30_minute_scenarios(tmp_path: Path):
    service = TranscriptScenarioService(root=tmp_path)

    response = service.list_scenarios()

    assert response.library_summary["scenario_count"] >= 8
    summaries = response.scenarios
    assert {item.education_level for item in summaries} >= {"college", "university"}
    assert "high_school" not in {item.education_level for item in summaries}
    assert len({item.subject for item in summaries}) >= 6
    assert all(item.estimated_duration_minutes == 30 for item in summaries)
    assert all(item.student_count >= 6 for item in summaries)
    assert all(item.turn_count == 64 for item in summaries)
    loaded_scenarios = [service.load_scenario(item.scenario_id) for item in summaries]
    assert all(
        [student.name for student in scenario.student_profiles] == EXPECTED_STUDENT_NAMES
        for scenario in loaded_scenarios
    )
    assert all(scenario.transcript_turns[0].speaker_name == "Mr. Anderson" for scenario in loaded_scenarios)
    assert all(_first_turn_word_count(scenario.model_dump()) <= 40 for scenario in loaded_scenarios)
    assert all(any(turn.speaker_name == "Class" for turn in scenario.transcript_turns) for scenario in loaded_scenarios)
    for scenario in loaded_scenarios:
        text = _scenario_text(scenario)
        assert all(part in text for part in EXPECTED_PARTS)
        lowered = text.lower()
        for marker in SUBJECT_ENRICHMENT_MARKERS[scenario.scenario_id]:
            assert marker.lower() in lowered


def test_transcript_scenario_prompts_are_editable_and_persisted(tmp_path: Path):
    service = TranscriptScenarioService(root=tmp_path)
    scenario = service.load_scenario("hs_python_loops_30m")
    scenario.student_profiles[1].parameters.confidence = 0.23
    scenario.student_profiles[1].parameters.prompt_instructions = "Reveal the print-line misconception, then ask for a trace table."
    service.save_scenario(scenario)

    reloaded = service.load_scenario("hs_python_loops_30m")
    prompts = service.render_student_prompts("hs_python_loops_30m")

    assert reloaded.student_profiles[1].parameters.confidence == 0.23
    assert "trace table" in prompts[1].prompt
    assert "Python for-loops" in reloaded.title
    assert any("misconception_event" in turn.pedagogical_tags for turn in reloaded.transcript_turns)


def test_transcript_scenario_readiness_test_outputs_preview_and_checks(tmp_path: Path):
    service = TranscriptScenarioService(root=tmp_path)

    result = service.run_readiness_test("uni_hypothesis_testing_30m")

    assert result.passed is True
    assert "Draft transcript" in result.transcript_preview_markdown
    assert len(result.rendered_student_prompts) >= 5
    statuses = {check.check_id: check.status for check in result.checks}
    assert statuses["duration_30_minutes"] == "pass"
    assert statuses["balanced_dialogue_structure"] == "pass"
    assert statuses["misconception_event"] == "pass"
    assert statuses["formative_assessment"] == "pass"


def test_transcript_system_api_list_get_prompts_test_and_save():
    client = TestClient(app)

    listing = client.get("/api/v2/transcript-system/scenarios")
    assert listing.status_code == 200
    list_data = listing.json()
    assert list_data["library_summary"]["scenario_count"] >= 8
    assert "Live" not in list_data["library_summary"]["duration_policy"]

    scenario_id = "college_stoichiometry_30m"
    get_response = client.get(f"/api/v2/transcript-system/scenarios/{scenario_id}")
    assert get_response.status_code == 200
    scenario = get_response.json()
    assert scenario["estimated_duration_minutes"] == 30
    assert scenario["education_level"] == "college"
    assert len(scenario["student_profiles"]) >= 6
    assert len(scenario["transcript_turns"]) == 64
    assert [student["name"] for student in scenario["student_profiles"]] == EXPECTED_STUDENT_NAMES
    assert scenario["transcript_turns"][0]["speaker_name"] == "Mr. Anderson"
    assert len(scenario["transcript_turns"][0]["message"].split()) <= 40
    assert any(turn["speaker_name"] == "Class" for turn in scenario["transcript_turns"])

    prompts = client.get(f"/api/v2/transcript-system/scenarios/{scenario_id}/prompts")
    assert prompts.status_code == 200
    assert "misconception_strength" not in prompts.text.lower()  # prompts show values as prose, not raw field names only
    assert "Special behaviour instructions" in prompts.json()[0]["prompt"]

    original_notes = scenario["editable_notes"]
    try:
        scenario["editable_notes"] = "API save smoke test note; scenario remains editable before benchmark testing."
        save = client.put(f"/api/v2/transcript-system/scenarios/{scenario_id}", json=scenario)
        assert save.status_code == 200
        assert save.json()["saved"] is True

        test_response = client.post(f"/api/v2/transcript-system/scenarios/{scenario_id}/test")
        assert test_response.status_code == 200
        test_data = test_response.json()
        assert test_data["passed"] is True
        assert "fixed/frozen" in " ".join(test_data["next_steps"])
    finally:
        scenario["editable_notes"] = original_notes
        client.put(f"/api/v2/transcript-system/scenarios/{scenario_id}", json=scenario)


def test_transcript_system_api_rejects_mismatched_save_path():
    client = TestClient(app)
    scenario = client.get("/api/v2/transcript-system/scenarios/hs_newton_laws_30m").json()
    scenario["scenario_id"] = "wrong_id"

    response = client.put("/api/v2/transcript-system/scenarios/hs_newton_laws_30m", json=scenario)

    assert response.status_code == 400


def test_transcript_system_selected_scenario_runs_til_evaluation():
    client = TestClient(app)

    response = client.post(
        "/api/v2/transcript-system/scenarios/college_stoichiometry_30m/til-evaluation",
        params={"reviewer_id": "expert_reviewer_selected_scenario_test"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["transcript_id"] == "scenario_college_stoichiometry_30m"
    assert data["scenario"]["scenario_id"] == "college_stoichiometry_30m"
    assert data["benchmark_protocol"]["selected_scenario_id"] == "college_stoichiometry_30m"
    assert data["til_verification"]["overall_status"] == "verified"
    assert len(data["transcript"]["turns"]) == 64
