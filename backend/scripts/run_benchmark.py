"""Run Phase 4 MVP benchmark.

Usage:
  uv run python -m scripts.run_benchmark --conditions baseline,til --repetitions 1
"""

from __future__ import annotations

import argparse
import os
import time

from pathlib import Path

from app.benchmark_loader import GoldenBenchmarkLoader
from app.evaluator_runner import EvaluatorRunner
from app.evidence_verifier import EvidenceVerifier
from app.export_service import ExportService
from app.seed_data import seed_database


def run_benchmark(
    *,
    conditions: list[str],
    repetitions: int,
    transcript_id: str | None = None,
    scenario_id: str | None = None,
    export: bool = True,
    export_root: Path | None = None,
    benchmark_root: Path | None = None,
) -> str:
    loader = GoldenBenchmarkLoader(root=benchmark_root) if benchmark_root else GoldenBenchmarkLoader()
    seed_database(root=loader.root)
    runner = EvaluatorRunner(loader)
    verifier = EvidenceVerifier(loader)
    exporter = ExportService(loader)
    items = loader.list_items()
    if transcript_id:
        items = [item for item in items if item["transcript_id"] == transcript_id]
    if scenario_id:
        items = [item for item in items if item["scenario_id"] == scenario_id]
    if not items:
        raise ValueError("No benchmark items selected")

    experiment_id: str | None = None
    delay_seconds = float(os.getenv("BENCHMARK_EVALUATOR_DELAY_SECONDS") or "0")
    for _ in range(repetitions):
        for item in items:
            for condition in conditions:
                evaluation_id, experiment_id, _ = runner.run(
                    transcript_id=item["transcript_id"],
                    condition=condition,  # type: ignore[arg-type]
                    experiment_id=experiment_id,
                )
                verifier.verify_evaluation(evaluation_id)
                if delay_seconds > 0:
                    time.sleep(delay_seconds)

    assert experiment_id is not None
    print(f"experiment_id={experiment_id}")
    if export:
        if export_root is None:
            export_dir = exporter.export_experiment(experiment_id)
        else:
            export_dir = exporter.export_experiment(experiment_id, export_root=export_root)
        print(f"export_dir={export_dir}")
    return experiment_id


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--conditions", default="baseline,til")
    parser.add_argument("--repetitions", type=int, default=1)
    parser.add_argument("--transcript-id", default=None)
    parser.add_argument("--scenario-id", default=None)
    parser.add_argument("--benchmark-root", type=Path, default=None)
    args = parser.parse_args()
    conditions = [value.strip() for value in args.conditions.split(",") if value.strip()]
    run_benchmark(
        conditions=conditions,
        repetitions=args.repetitions,
        transcript_id=args.transcript_id,
        scenario_id=args.scenario_id,
        benchmark_root=args.benchmark_root,
    )


if __name__ == "__main__":
    main()
