import csv
import json
from pathlib import Path

from app.config import GOLDEN_BENCHMARK_ROOT, REQUIRED_RUBRIC_CRITERIA
from app.models import (
    BenchmarkTranscript,
    DatasetVersion,
    ExpectedMissedOpportunities,
    ExpectedScores,
    GroundTruth,
    Scenario,
)


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def variant_dirs():
    scenario_dir = GOLDEN_BENCHMARK_ROOT / "python_loops"
    return [scenario_dir / "strong", scenario_dir / "weak"]


def test_dataset_version_file_is_valid():
    path = GOLDEN_BENCHMARK_ROOT / "DATASET_VERSION.json"
    data = DatasetVersion.model_validate(load_json(path))

    assert data.dataset_version == "golden_benchmark_v1.0_phase1"
    assert data.scenario_count == 1
    assert data.transcript_count == 2
    assert data.rubric_version == "rubric_v1.0"


def test_python_loops_scenario_is_valid():
    scenario = Scenario.model_validate(load_json(GOLDEN_BENCHMARK_ROOT / "python_loops" / "scenario.json"))

    assert scenario.scenario_id == "python_loops_001"
    assert scenario.domain == "computer_science"
    assert scenario.common_misconceptions


def test_golden_benchmark_variants_have_required_files():
    required = {
        "transcript.json",
        "ground_truth.json",
        "expected_scores.json",
        "expected_missed_opportunities.json",
        "expert_annotation.csv",
    }
    for variant_dir in variant_dirs():
        assert variant_dir.exists(), variant_dir
        assert required.issubset({p.name for p in variant_dir.iterdir()})


def test_transcripts_ground_truth_scores_and_missed_opportunities_align():
    for variant_dir in variant_dirs():
        transcript = BenchmarkTranscript.model_validate(load_json(variant_dir / "transcript.json"))
        ground_truth = GroundTruth.model_validate(load_json(variant_dir / "ground_truth.json"))
        scores = ExpectedScores.model_validate(load_json(variant_dir / "expected_scores.json"))
        missed = ExpectedMissedOpportunities.model_validate(
            load_json(variant_dir / "expected_missed_opportunities.json")
        )
        turn_ids = set(transcript.turn_map())

        assert transcript.scenario_id == "python_loops_001"
        assert ground_truth.transcript_id == transcript.transcript_id
        assert scores.transcript_id == transcript.transcript_id
        assert missed.transcript_id == transcript.transcript_id
        assert set(scores.scores) == REQUIRED_RUBRIC_CRITERIA

        for opportunity in missed.missed_opportunities:
            assert set(opportunity.evidence_turn_ids).issubset(turn_ids)


def test_expert_annotation_csv_has_required_columns_and_valid_scores():
    required_columns = {
        "transcript_id",
        "reviewer_id",
        "criterion",
        "human_score",
        "issue_id",
        "evidence_turn_ids",
        "accepted_ground_truth",
        "comment",
        "timestamp",
    }
    for variant_dir in variant_dirs():
        with (variant_dir / "expert_annotation.csv").open(newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        assert rows
        assert required_columns.issubset(rows[0])
        for row in rows:
            assert row["criterion"] in REQUIRED_RUBRIC_CRITERIA
            assert 1 <= int(row["human_score"]) <= 5
