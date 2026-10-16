"""Compute and export metrics for an existing experiment."""

from __future__ import annotations

import argparse
import json

from app.export_service import ExportService
from app.metrics import MetricsService


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("experiment_id")
    parser.add_argument("--export", action="store_true")
    args = parser.parse_args()

    metrics = MetricsService().compute_experiment_metrics(args.experiment_id)
    print(json.dumps(metrics, indent=2))
    if args.export:
        export_dir = ExportService().export_experiment(args.experiment_id)
        print(f"export_dir={export_dir}")


if __name__ == "__main__":
    main()
