"""Merge independently-run model-comparison manifests without calling any provider API.

Use this after running providers separately, e.g. OpenAI once, Sonnet once,
Gemini once. The merger keeps one best row per provider/model and prefers
completed rows over blocked/failed/partial rows so a successful GPT result is
preserved instead of rerun.

Usage:
  uv run python -m scripts.merge_model_comparison_manifests
  uv run python -m scripts.merge_model_comparison_manifests --output-name final_mvp_v1_combined
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.config import THESIS_PROJECT_ROOT

MODEL_CMP_ROOT = THESIS_PROJECT_ROOT / "results" / "model_comparison"
STATUS_RANK = {
    "completed": 4,
    "failed_live_run": 3,
    "failed_run": 3,
    "ready_smoke_ok_not_run_without_run_live": 2,
    "blocked_provider_smoke_failed": 1,
    "skipped_no_provider_key": 0,
}


def _load_manifest(path: Path) -> dict[str, Any] | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        data["_manifest_path"] = str(path)
        return data
    except Exception:
        return None


def _row_sort_key(row: dict[str, Any]) -> tuple[int, str]:
    status_score = STATUS_RANK.get(str(row.get("status", "")), -1)
    # Prefer preserved completed rows when present, then later manifest timestamps.
    preserved = "1" if row.get("source") == "preserved_completed_experiment" else "0"
    return status_score, preserved


def merge_manifests(
    manifest_paths: list[Path] | None = None,
    output_name: str | None = None,
    include_default_skipped: bool = False,
) -> Path:
    if manifest_paths is None:
        manifest_paths = sorted(MODEL_CMP_ROOT.glob("*/model_comparison_manifest.json"))
    manifests = []
    for path in manifest_paths:
        manifest = _load_manifest(path)
        if not manifest:
            continue
        run_id = str(manifest.get("run_id", ""))
        if manifest.get("no_provider_api_called") and "combined" in run_id:
            # Do not recursively merge an aggregate manifest back into itself.
            continue
        manifests.append(manifest)

    best: dict[tuple[str, str], dict[str, Any]] = {}
    diagnostics: list[dict[str, Any]] = []
    for manifest in manifests:
        for row in manifest.get("results", []):
            row = dict(row)
            if row.get("status") == "skipped_no_provider_key" and not row.get("key_env_present"):
                continue
            if (
                not include_default_skipped
                and row.get("source") == "default"
                and row.get("status") == "skipped_no_provider_key"
            ):
                continue
            row["source_manifest_run_id"] = manifest.get("run_id")
            row["source_manifest_path"] = manifest.get("_manifest_path")
            key = (str(row.get("provider")), str(row.get("model")))
            diagnostics.append({
                "provider": key[0],
                "model": key[1],
                "status": row.get("status"),
                "experiment_id": row.get("experiment_id"),
                "source_manifest_run_id": manifest.get("run_id"),
            })
            old = best.get(key)
            if old is None or _row_sort_key(row) > _row_sort_key(old):
                best[key] = row

    now = datetime.now(timezone.utc)
    run_id = output_name or "combined_model_comparison_" + now.strftime("%Y%m%d_%H%M%S")
    out_dir = MODEL_CMP_ROOT / run_id
    out_dir.mkdir(parents=True, exist_ok=True)
    rows = sorted(best.values(), key=lambda r: (str(r.get("provider")), str(r.get("model"))))
    summary = {
        "run_id": run_id,
        "created_at": now.isoformat(),
        "merged_manifest_count": len(manifests),
        "source_manifests": [m.get("_manifest_path") for m in manifests],
        "secret_redacted": True,
        "no_provider_api_called": True,
        "include_default_skipped": include_default_skipped,
        "selection_policy": "one best row per provider/model; prefer completed over ready/blocked/failed/skipped; prefer preserved completed experiments on ties",
        "diagnostics": diagnostics,
        "results": rows,
    }
    (out_dir / "model_comparison_manifest.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    (out_dir / "MODEL_COMPARISON_README.md").write_text(_render_markdown(summary), encoding="utf-8")
    print(json.dumps({"created": str(out_dir), "rows": len(rows), "no_provider_api_called": True, "secret_redacted": True}, indent=2))
    return out_dir


def _render_markdown(summary: dict[str, Any]) -> str:
    lines = [
        "# Combined Model Comparison Manifest",
        "",
        f"Run ID: `{summary['run_id']}`",
        f"Merged manifests: **{summary['merged_manifest_count']}**",
        "No provider API called: **true**",
        "",
        "## Selected results",
        "",
        "| Provider | Model | Status | Experiment | Source manifest |",
        "|---|---|---|---|---|",
    ]
    for row in summary["results"]:
        lines.append(
            "| "
            + " | ".join(
                [
                    str(row.get("provider")),
                    f"`{row.get('actual_model') or row.get('model')}`",
                    f"`{row.get('status')}`",
                    f"`{row.get('experiment_id') or '—'}`",
                    f"`{row.get('source_manifest_run_id')}`",
                ]
            )
            + " |"
        )
    lines.extend([
        "",
        "## Cost-control rule",
        "",
        "Use this combined manifest in final reports. Do not rerun a completed provider row unless the user explicitly requests a fresh run.",
    ])
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-name", default=None)
    parser.add_argument("--include-default-skipped", action="store_true", help="Include legacy skipped default candidates such as gpt-4o-mini if present.")
    parser.add_argument("manifests", nargs="*", type=Path, help="Optional explicit manifest paths. Defaults to all model_comparison manifests.")
    args = parser.parse_args()
    merge_manifests(manifest_paths=args.manifests or None, output_name=args.output_name, include_default_skipped=args.include_default_skipped)


if __name__ == "__main__":
    main()
