from pathlib import Path

from app.benchmark_loader import GoldenBenchmarkLoader
from app.models import ExpectedMissedOpportunities, ExpectedScores, GroundTruth
from scripts.freeze_transcript_scenarios import DATASET_VERSION, freeze_transcript_scenarios
from scripts.run_benchmark import run_benchmark
from app.export_service import ExportService


def test_freeze_transcript_scenarios_exports_expanded_golden_benchmark(tmp_path: Path):
    manifest = freeze_transcript_scenarios(output_root=tmp_path)

    assert manifest["dataset_version"] == DATASET_VERSION
    assert manifest["scenario_count"] >= 8
    assert manifest["transcript_count"] == manifest["scenario_count"] * 2
    assert (tmp_path / "DATASET_VERSION.json").exists()
    assert (tmp_path / "FREEZE_MANIFEST.json").exists()
    assert (tmp_path / "README.md").exists()

    loader = GoldenBenchmarkLoader(root=tmp_path)
    items = loader.list_items()
    assert len(items) == manifest["transcript_count"]
    assert {item["variant"] for item in items} == {"strong", "weak"}

    first = manifest["exported_scenarios"][0]
    scenario_dir = tmp_path / first["scenario_id"]
    for variant in ["strong", "weak"]:
        variant_dir = scenario_dir / variant
        assert (variant_dir / "transcript.json").exists()
        assert (variant_dir / "ground_truth.json").exists()
        assert (variant_dir / "expected_scores.json").exists()
        assert (variant_dir / "expected_missed_opportunities.json").exists()
        assert (variant_dir / "expert_annotation.csv").exists()
        scores = ExpectedScores.model_validate_json((variant_dir / "expected_scores.json").read_text())
        ground_truth = GroundTruth.model_validate_json((variant_dir / "ground_truth.json").read_text())
        missed = ExpectedMissedOpportunities.model_validate_json(
            (variant_dir / "expected_missed_opportunities.json").read_text()
        )
        assert scores.transcript_id.endswith(f"_{variant}_001")
        assert ground_truth.transcript_id == scores.transcript_id
        if variant == "weak":
            assert missed.missed_opportunities
        else:
            assert missed.missed_opportunities == []


def test_run_benchmark_supports_custom_expanded_benchmark_root(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("EVALUATOR_PROVIDER", "fallback")
    benchmark_root = tmp_path / "benchmark"
    export_root = tmp_path / "exports"
    freeze_transcript_scenarios(
        output_root=benchmark_root,
        scenario_ids=["hs_python_loops_30m"],
    )

    experiment_id = run_benchmark(
        conditions=["baseline", "til"],
        repetitions=1,
        scenario_id="hs_python_loops_30m",
        benchmark_root=benchmark_root,
        export=False,
    )
    export_dir = ExportService(GoldenBenchmarkLoader(root=benchmark_root)).export_experiment(
        experiment_id,
        export_root=export_root,
    )

    assert (export_dir / "evaluation_runs.csv").read_text(encoding="utf-8").count("hs_python_loops_30m") >= 4
    assert "golden_benchmark_expanded" in (export_dir / "reproducibility_manifest.json").read_text(
        encoding="utf-8"
    )
    metrics = (export_dir / "metrics_summary.json").read_text(encoding="utf-8")
    assert '"baseline"' in metrics
    assert '"til"' in metrics
