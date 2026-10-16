import json
from pathlib import Path

from app.config import GOLDEN_BENCHMARK_ROOT
from app.models import ReproducibilityManifest


def test_reproducibility_manifest_model_accepts_required_fields():
    manifest = ReproducibilityManifest.model_validate(
        {
            "experiment_id": "exp_20260713_153012_a8f3",
            "dataset_version": "golden_benchmark_v1.0_phase1",
            "transcript_id": "python_loops_weak_001",
            "scenario_id": "python_loops_001",
            "evaluator_condition": "til",
            "prompt_version": "til_evaluator_v1",
            "rubric_version": "rubric_v1.0",
            "openai_model": "configured_model_name",
            "temperature": 0.2,
            "seed": 42,
            "git_commit_hash": "abc123",
            "code_dirty": False,
            "started_at": "2026-07-13T15:30:12Z",
            "completed_at": "2026-07-13T16:10:45Z",
            "raw_response_path": "backend/data/raw_outputs/til/example.json",
        }
    )

    assert manifest.experiment_id.startswith("exp_")
    assert manifest.evaluator_condition == "til"
    assert manifest.rubric_version == "rubric_v1.0"


def test_dataset_version_supports_reproducibility_protocol():
    path = GOLDEN_BENCHMARK_ROOT / "DATASET_VERSION.json"
    data = json.loads(path.read_text(encoding="utf-8"))

    assert data["dataset_version"]
    assert data["rubric_version"] == "rubric_v1.0"
    assert data["scenario_count"] == 1
    assert data["transcript_count"] == 2


def test_reproducibility_protocol_doc_mentions_key_fields():
    doc = Path("../docs/REPRODUCIBILITY_PROTOCOL.md")
    text = doc.read_text(encoding="utf-8")

    for phrase in [
        "experiment ID",
        "dataset version",
        "prompt version",
        "rubric version",
        "OpenAI model",
        "git commit hash",
        "reproducibility_manifest.json",
    ]:
        assert phrase in text
