"""Phase 4 MVP export service."""

from __future__ import annotations

import csv
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from app.benchmark_loader import GoldenBenchmarkLoader
from app.config import EXPORT_ROOT, METRICS_VERSION, RUBRIC_VERSION, VERIFIER_VERSION
from app.database import connect
from app.evaluator_runner import git_commit_hash
from app.metrics import MetricsService


class ExportService:
    def __init__(self, loader: GoldenBenchmarkLoader | None = None) -> None:
        self.loader = loader or GoldenBenchmarkLoader()
        self.metrics = MetricsService(self.loader)

    def export_experiment(self, experiment_id: str, export_root: Path = EXPORT_ROOT) -> Path:
        export_dir = export_root / experiment_id
        charts_dir = export_dir / "charts"
        charts_dir.mkdir(parents=True, exist_ok=True)

        with connect() as conn:
            evaluations = conn.execute(
                "SELECT * FROM evaluation_runs WHERE experiment_id = ? ORDER BY evaluation_id",
                (experiment_id,),
            ).fetchall()
            evaluation_ids = [row["evaluation_id"] for row in evaluations]
            feedback = _select_in(conn, "feedback_items", "evaluation_id", evaluation_ids)
            verification = _select_in(conn, "verification_results", "evaluation_id", evaluation_ids)
            annotations = _select_in(conn, "human_annotations", "evaluation_id", evaluation_ids)
            blinding = _select_in(conn, "blinding_mappings", "evaluation_id", evaluation_ids)

        _write_csv(export_dir / "evaluation_runs.csv", evaluations)
        _write_csv(export_dir / "feedback_items.csv", feedback)
        _write_csv(export_dir / "evidence_verification.csv", verification)
        _write_csv(export_dir / "human_annotations.csv", annotations)
        _write_csv(export_dir / "blinded_mapping_revealed.csv", blinding)

        metrics = self.metrics.compute_experiment_metrics(experiment_id)
        (export_dir / "metrics_summary.json").write_text(
            json.dumps(metrics, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        self._write_charts(charts_dir, metrics)
        manifest = self._manifest(experiment_id, evaluations)
        (export_dir / "reproducibility_manifest.json").write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        (export_dir / "readable_report.md").write_text(
            self._readable_report(experiment_id, metrics, manifest), encoding="utf-8"
        )
        with connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO exports
                (export_id, experiment_id, export_path, reproducibility_manifest_path, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    f"export_{experiment_id}",
                    experiment_id,
                    str(export_dir),
                    str(export_dir / "reproducibility_manifest.json"),
                    datetime.now(timezone.utc).isoformat(),
                ),
            )
            conn.commit()
        return export_dir

    def _manifest(self, experiment_id: str, evaluations) -> dict:
        dataset = self.loader.dataset_version()
        return {
            "experiment_id": experiment_id,
            "dataset_version": dataset.dataset_version,
            "rubric_version": RUBRIC_VERSION,
            "verifier_version": VERIFIER_VERSION,
            "metrics_version": METRICS_VERSION,
            "prompt_versions": sorted({row["prompt_version"] for row in evaluations}),
            "models": sorted({row["model_name"] for row in evaluations}),
            "temperature_values": sorted({row["temperature"] for row in evaluations}),
            "git_commit_hash": git_commit_hash(),
            "code_dirty": _code_dirty(),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

    def _write_charts(self, charts_dir: Path, metrics: dict) -> None:
        conditions = metrics.get("conditions", {})
        mae_values = {
            condition: values.get("mean_absolute_error") or 0 for condition, values in conditions.items()
        }
        missing_values = {
            condition: values.get("missing_evidence_rate") or 0 for condition, values in conditions.items()
        }
        (charts_dir / "score_mae.svg").write_text(_bar_chart_svg("Mean absolute error", mae_values), encoding="utf-8")
        (charts_dir / "missing_evidence_rate.svg").write_text(_bar_chart_svg("Missing evidence rate", missing_values), encoding="utf-8")

    def _readable_report(self, experiment_id: str, metrics: dict, manifest: dict) -> str:
        lines = [
            f"# Experiment Report: {experiment_id}",
            "",
            "## Reproducibility",
            "",
            f"- Dataset: `{manifest['dataset_version']}`",
            f"- Rubric: `{manifest['rubric_version']}`",
            f"- Git commit: `{manifest['git_commit_hash']}`",
            f"- Code dirty: `{manifest['code_dirty']}`",
            "",
            "## Metrics",
            "",
        ]
        for condition, values in metrics.get("conditions", {}).items():
            lines.extend(
                [
                    f"### {condition}",
                    "",
                    f"- Evaluations: {values['evaluation_count']}",
                    f"- Feedback items: {values['feedback_count']}",
                    f"- Mean absolute error: {values['mean_absolute_error']}",
                    f"- Verified rate: {values['verified_rate']}",
                    f"- Missing evidence rate: {values['missing_evidence_rate']}",
                    "",
                ]
            )
        return "\n".join(lines)


def _select_in(conn, table: str, column: str, values: list[str]):
    if not values:
        return []
    placeholders = ",".join("?" for _ in values)
    return conn.execute(f"SELECT * FROM {table} WHERE {column} IN ({placeholders})", values).fetchall()


def _write_csv(path: Path, rows: Iterable) -> None:
    rows = list(rows)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        for row in rows:
            writer.writerow(dict(row))


def _code_dirty() -> bool:
    try:
        output = subprocess.check_output(["git", "status", "--porcelain"], cwd=Path(__file__).resolve().parents[2])
        return bool(output.decode().strip())
    except Exception:
        return True


def _bar_chart_svg(title: str, values: dict[str, float]) -> str:
    width = 520
    height = 220
    max_value = max(values.values(), default=1) or 1
    bars = []
    x = 70
    for label, value in values.items():
        bar_height = int((value / max_value) * 120) if max_value else 0
        y = 170 - bar_height
        bars.append(f'<rect x="{x}" y="{y}" width="90" height="{bar_height}" fill="#5a7cff" stroke="#18212f" stroke-width="3"/>')
        bars.append(f'<text x="{x}" y="195" font-size="14">{label}</text>')
        bars.append(f'<text x="{x}" y="{y - 8}" font-size="12">{value}</text>')
        x += 150
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  <rect width="100%" height="100%" fill="#fff8e8"/>
  <text x="24" y="32" font-size="20" font-family="Arial" font-weight="700">{title}</text>
  <line x1="50" y1="170" x2="470" y2="170" stroke="#18212f" stroke-width="3"/>
  {''.join(bars)}
</svg>'''
