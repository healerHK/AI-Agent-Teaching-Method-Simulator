from pathlib import Path

from app.export_service import ExportService
from scripts.run_benchmark import run_benchmark


def test_phase4_benchmark_runner_exports_results(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("EVALUATOR_PROVIDER", "fallback")
    experiment_id = run_benchmark(
        conditions=["baseline", "til"],
        repetitions=1,
        transcript_id="python_loops_weak_001",
        export=False,
    )

    export_dir = ExportService().export_experiment(experiment_id, export_root=tmp_path)

    assert (export_dir / "evaluation_runs.csv").exists()
    assert (export_dir / "feedback_items.csv").exists()
    assert (export_dir / "metrics_summary.json").exists()
    assert (export_dir / "reproducibility_manifest.json").exists()
    assert (export_dir / "charts" / "score_mae.svg").exists()
