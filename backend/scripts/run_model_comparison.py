"""Run/record model-comparison benchmark experiments for PixelClass TIL.

Supports two configuration styles:

1. Provider-specific envs such as OPENAI_API_KEY / ANTHROPIC_API_KEY.
2. Repeated generic blocks in `.env`, e.g.

   EVALUATOR_PROVIDER=openai
   EVALUATOR_MODEL=gpt-5.6-sol
   EVALUATOR_API_KEY=...

   EVALUATOR_PROVIDER=claude
   EVALUATOR_MODEL=claude-sonnet-5
   EVALUATOR_API_KEY=...

Keys are never printed. Live providers are smoke-tested before full benchmark runs.
"""

from __future__ import annotations

import argparse
import json
import os
import re
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

from app.benchmark_loader import GoldenBenchmarkLoader
from app.config import REPO_ROOT, THESIS_PROJECT_ROOT
from app.export_service import ExportService
from app.llm_provider import evaluator_provider_config
from scripts.run_benchmark import run_benchmark
from scripts.testing_pack import _safe_live_provider_smoke

DEFAULT_BENCHMARK_ROOT = Path("data/golden_benchmark_expanded")
DEFAULT_OUTPUT_ROOT = THESIS_PROJECT_ROOT / "results" / "model_comparison"


@dataclass(frozen=True)
class ModelCandidate:
    label: str
    provider: str
    model: str
    key_envs: tuple[str, ...] = ()
    api_key: str | None = None
    base_url: str | None = None
    source: str = "default"
    intended_use: str = "benchmark_evaluator"


DEFAULT_CANDIDATES = [
    ModelCandidate(
        label="fallback_deterministic",
        provider="fallback",
        model="deterministic-fallback",
        source="control",
        intended_use="deterministic pipeline validation",
    ),
    ModelCandidate(
        label="openai_gpt4o_mini",
        provider="openai",
        model="gpt-4o-mini",
        key_envs=("OPENAI_API_KEY",),
        intended_use="recommended low-cost OpenAI reference if configured",
    ),
    ModelCandidate(
        label="anthropic_claude_sonnet",
        provider="anthropic",
        model="claude-3-5-sonnet-latest",
        key_envs=("ANTHROPIC_API_KEY", "CLAUDE_API_KEY"),
        intended_use="Claude robustness check if configured",
    ),
    ModelCandidate(
        label="gemini_36_flash",
        provider="gemini",
        model="gemini-3.6-flash",
        key_envs=("GEMINI_API_KEY", "GOOGLE_API_KEY"),
        intended_use="Gemini 3.6 Flash comparison if configured",
    ),
]


def normalize_provider(provider: str) -> str:
    provider = provider.strip().lower()
    return {"claude": "anthropic", "google": "gemini"}.get(provider, provider)


def slug(value: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9]+", "_", value.strip().lower()).strip("_")
    return cleaned or "model"


def _safe_error_message(exc: Exception, limit: int = 1000) -> str:
    """Return provider errors without leaking API keys embedded in request URLs."""

    message = str(exc)
    message = re.sub(r"([?&]key=)[^\s'\"]+", r"\1[REDACTED]", message)
    message = re.sub(r"(Authorization: Bearer\s+)[^\s'\"]+", r"\1[REDACTED]", message, flags=re.IGNORECASE)
    return message[:limit]


@contextmanager
def temporary_env(updates: dict[str, str | None]) -> Iterator[None]:
    old_values = {key: os.environ.get(key) for key in updates}
    try:
        for key, value in updates.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        yield
    finally:
        for key, old in old_values.items():
            if old is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = old


def parse_dotenv_blocks(path: Path = REPO_ROOT / ".env") -> list[ModelCandidate]:
    """Parse repeated generic EVALUATOR_* blocks without exposing key values."""

    if not path.exists():
        return []
    blocks: list[dict[str, str]] = []
    current: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key == "EVALUATOR_PROVIDER" and current.get("provider"):
            blocks.append(current)
            current = {}
        if key == "EVALUATOR_PROVIDER":
            current["provider"] = value
        elif key == "EVALUATOR_MODEL":
            current["model"] = value
        elif key == "EVALUATOR_API_KEY":
            current["api_key"] = value
        elif key == "EVALUATOR_BASE_URL":
            current["base_url"] = value
    if current.get("provider") or current.get("model") or current.get("api_key"):
        blocks.append(current)

    candidates: list[ModelCandidate] = []
    seen: set[tuple[str, str]] = set()
    for index, block in enumerate(blocks, start=1):
        provider = normalize_provider(block.get("provider", ""))
        model = block.get("model", "").strip()
        api_key = block.get("api_key")
        if not provider or not model:
            continue
        key = (provider, model)
        if key in seen:
            continue
        seen.add(key)
        candidates.append(
            ModelCandidate(
                label=f"env_{index}_{slug(provider)}_{slug(model)}",
                provider=provider,
                model=model,
                api_key=api_key,
                base_url=block.get("base_url"),
                source="dotenv_evaluator_block",
                intended_use="user-configured final MVP model comparison",
            )
        )
    return candidates


def provider_specific_key(candidate: ModelCandidate) -> tuple[str | None, str | None]:
    if candidate.provider == "fallback":
        return None, None
    if candidate.api_key:
        return "EVALUATOR_API_KEY[dotenv-block]", candidate.api_key
    for key_name in candidate.key_envs:
        value = os.getenv(key_name)
        if value:
            return key_name, value
    return None, None


def candidate_env_updates(candidate: ModelCandidate, key_value: str | None) -> dict[str, str | None]:
    updates: dict[str, str | None] = {
        "EVALUATOR_PROVIDER": candidate.provider,
        "EVALUATOR_MODEL": candidate.model,
        "BASELINE_EVALUATOR_PROVIDER": candidate.provider,
        "BASELINE_EVALUATOR_MODEL": candidate.model,
        "TIL_EVALUATOR_PROVIDER": candidate.provider,
        "TIL_EVALUATOR_MODEL": candidate.model,
    }
    if candidate.base_url:
        updates["EVALUATOR_BASE_URL"] = candidate.base_url
        updates["BASELINE_EVALUATOR_BASE_URL"] = candidate.base_url
        updates["TIL_EVALUATOR_BASE_URL"] = candidate.base_url
    if candidate.provider != "fallback" and key_value:
        updates["EVALUATOR_API_KEY"] = key_value
        updates["BASELINE_EVALUATOR_API_KEY"] = key_value
        updates["TIL_EVALUATOR_API_KEY"] = key_value
        updates["EVALUATOR_STRICT_PROVIDER"] = "true"
        if candidate.provider == "openai":
            updates["OPENAI_API_KEY"] = key_value
        elif candidate.provider == "anthropic":
            updates["ANTHROPIC_API_KEY"] = key_value
        elif candidate.provider == "gemini":
            updates["GEMINI_API_KEY"] = key_value
            # Model-comparison runs should test the explicitly requested Gemini model.
            # Do not silently switch to another Gemini Flash variant for final metrics.
            updates["GEMINI_FALLBACK_MODELS"] = candidate.model
            updates["EVALUATOR_TIMEOUT_SECONDS"] = "180"
            updates["BASELINE_EVALUATOR_TIMEOUT_SECONDS"] = "180"
            updates["TIL_EVALUATOR_TIMEOUT_SECONDS"] = "180"
            updates["BENCHMARK_EVALUATOR_DELAY_SECONDS"] = "5"
    return updates


def build_candidates(
    *,
    include_default_candidates: bool,
    use_dotenv_blocks: bool,
    include_fallback_control: bool = True,
) -> list[ModelCandidate]:
    candidates: list[ModelCandidate] = [DEFAULT_CANDIDATES[0]] if include_fallback_control else []
    if use_dotenv_blocks:
        candidates.extend(parse_dotenv_blocks())
    if include_default_candidates:
        for candidate in DEFAULT_CANDIDATES[1:]:
            if (candidate.provider, candidate.model) not in {(c.provider, c.model) for c in candidates}:
                candidates.append(candidate)
    return candidates


def _norm_path_string(value: str | Path) -> str:
    return str(value).replace("\\", "/").rstrip("/")


def find_completed_candidate_result(
    candidate: ModelCandidate,
    *,
    output_root: Path,
    benchmark_root: Path,
    repetitions: int,
    transcript_count: int,
    scenario_count: int,
) -> dict[str, Any] | None:
    """Find a compatible completed provider/model row from prior manifests.

    This is a cost-control guard: by default, a successful paid provider run is
    reused and never rerun unless the caller explicitly passes --force-rerun.
    """

    wanted_benchmark = _norm_path_string(benchmark_root)
    manifests = sorted(output_root.glob("*/model_comparison_manifest.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    for manifest_path in manifests:
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except Exception:
            continue
        for row in manifest.get("results", []):
            if row.get("provider") != candidate.provider or row.get("model") != candidate.model:
                continue
            if row.get("status") != "completed":
                continue
            if int(row.get("repetitions") or -1) != repetitions:
                continue
            if int(row.get("selected_transcript_count") or -1) != transcript_count:
                continue
            if int(row.get("selected_scenario_count") or -1) != scenario_count:
                continue
            row_benchmark = _norm_path_string(row.get("benchmark_root") or "")
            if row_benchmark and not (row_benchmark == wanted_benchmark or row_benchmark.endswith(wanted_benchmark)):
                continue
            reused = dict(row)
            reused["reused_completed_provider_result"] = True
            reused["source_manifest_path"] = str(manifest_path)
            reused["source_manifest_run_id"] = manifest.get("run_id")
            reused["secret_redacted"] = True
            return reused
    return None


def run_model_comparison(
    *,
    benchmark_root: Path = DEFAULT_BENCHMARK_ROOT,
    repetitions: int = 3,
    output_root: Path = DEFAULT_OUTPUT_ROOT,
    run_live: bool = False,
    include_labels: set[str] | None = None,
    include_providers: set[str] | None = None,
    include_models: set[str] | None = None,
    include_default_candidates: bool = False,
    use_dotenv_blocks: bool = True,
    include_fallback_control: bool = True,
    reuse_completed: bool = True,
) -> Path:
    output_root.mkdir(parents=True, exist_ok=True)
    run_id = "modelcmp_" + datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    run_dir = output_root / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    loader = GoldenBenchmarkLoader(root=benchmark_root)
    items = loader.list_items()
    results: list[dict[str, Any]] = []
    candidates = build_candidates(
        include_default_candidates=include_default_candidates,
        use_dotenv_blocks=use_dotenv_blocks,
        include_fallback_control=include_fallback_control,
    )

    for candidate in candidates:
        if include_labels and candidate.label not in include_labels:
            continue
        if include_providers and candidate.provider not in include_providers:
            continue
        if include_models and candidate.model not in include_models:
            continue
        key_name, key_value = provider_specific_key(candidate)
        record: dict[str, Any] = {
            "label": candidate.label,
            "provider": candidate.provider,
            "model": candidate.model,
            "source": candidate.source,
            "intended_use": candidate.intended_use,
            "benchmark_root": str(benchmark_root),
            "selected_transcript_count": len(items),
            "selected_scenario_count": len({item["scenario_id"] for item in items}),
            "repetitions": repetitions,
            "conditions": ["baseline", "til"],
            "key_env_present": bool(key_name),
            "key_env_name": key_name,
            "secret_redacted": True,
            "status": "pending",
            "smoke": None,
            "experiment_id": None,
            "export_dir": None,
            "metrics": None,
            "error": None,
        }

        if run_live and reuse_completed and candidate.provider != "fallback":
            reused = find_completed_candidate_result(
                candidate,
                output_root=output_root,
                benchmark_root=benchmark_root,
                repetitions=repetitions,
                transcript_count=len(items),
                scenario_count=len({item["scenario_id"] for item in items}),
            )
            if reused:
                reused.setdefault("label", candidate.label)
                reused["label"] = candidate.label
                reused["status"] = "completed"
                reused["source"] = "reused_completed_manifest"
                reused["reuse_note"] = "Paid provider result was already completed; no provider API call was made for this row."
                results.append(reused)
                continue

        if candidate.provider != "fallback" and not key_value:
            record["status"] = "skipped_no_provider_key"
            results.append(record)
            continue

        with temporary_env(candidate_env_updates(candidate, key_value)):
            safe_config = evaluator_provider_config("til")
            record["resolved_model_label"] = safe_config.model_label
            if candidate.provider != "fallback":
                smoke = _safe_live_provider_smoke("til")
                record["smoke"] = smoke
                if smoke.get("actual_model") and smoke.get("actual_model") != candidate.model:
                    record["actual_model"] = smoke.get("actual_model")
                    record["model_resolution_note"] = f"requested {candidate.model}; actual {smoke.get('actual_model')}"
                if smoke.get("status") != "ok":
                    record["status"] = "blocked_provider_smoke_failed"
                    results.append(record)
                    continue
                if not run_live:
                    record["status"] = "ready_smoke_ok_not_run_without_run_live"
                    results.append(record)
                    continue

            try:
                experiment_id = run_benchmark(
                    conditions=["baseline", "til"],
                    repetitions=repetitions,
                    benchmark_root=benchmark_root,
                    export=False,
                )
                export_dir = ExportService(loader).export_experiment(experiment_id)
                metrics_path = export_dir / "metrics_summary.json"
                record["status"] = "completed"
                record["experiment_id"] = experiment_id
                record["export_dir"] = str(export_dir)
                record["metrics"] = json.loads(metrics_path.read_text(encoding="utf-8"))
            except Exception as exc:
                record["status"] = "failed_run"
                record["error"] = {"type": type(exc).__name__, "message": _safe_error_message(exc)}
        results.append(record)

    summary = {
        "run_id": run_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "benchmark_root": str(benchmark_root),
        "scenario_count": len({item["scenario_id"] for item in items}),
        "transcript_count": len(items),
        "repetitions": repetitions,
        "run_live": run_live,
        "used_dotenv_blocks": use_dotenv_blocks,
        "included_default_candidates": include_default_candidates,
        "include_fallback_control": include_fallback_control,
        "reuse_completed": reuse_completed,
        "provider_filter": sorted(include_providers) if include_providers else None,
        "model_filter": sorted(include_models) if include_models else None,
        "secret_redacted": True,
        "results": results,
    }
    (run_dir / "model_comparison_manifest.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    (run_dir / "MODEL_COMPARISON_README.md").write_text(render_markdown_summary(summary), encoding="utf-8")
    print(
        json.dumps(
            {
                "run_dir": str(run_dir),
                "run_id": run_id,
                "statuses": {r["label"]: r["status"] for r in results},
                "secrets_redacted": True,
            },
            indent=2,
        )
    )
    return run_dir


def render_markdown_summary(summary: dict[str, Any]) -> str:
    lines = [
        "# PixelClass TIL Model Comparison Run",
        "",
        f"Run ID: `{summary['run_id']}`",
        f"Benchmark root: `{summary['benchmark_root']}`",
        f"Scenarios: **{summary['scenario_count']}**",
        f"Transcripts: **{summary['transcript_count']}**",
        f"Repetitions: **{summary['repetitions']}**",
        f"Live providers enabled: **{summary['run_live']}**",
        f"Using dotenv provider blocks: **{summary.get('used_dotenv_blocks')}**",
        "",
        "## Status table",
        "",
        "| Model label | Provider | Model | Status | Experiment | Key/smoke note |",
        "|---|---|---|---|---|---|",
    ]
    for item in summary["results"]:
        smoke = item.get("smoke") or {}
        note = smoke.get("status") or item.get("reuse_note") or item.get("key_env_name") or "n/a"
        if smoke.get("http_status"):
            note += f" HTTP {smoke.get('http_status')} {smoke.get('provider_error_category', '')}"
        experiment = item.get("experiment_id") or "—"
        lines.append(
            f"| `{item['label']}` | {item['provider']} | `{item['model']}` | `{item['status']}` | `{experiment}` | {note} |"
        )

    lines.extend(["", "## Completed result highlights", ""])
    for item in summary["results"]:
        if item.get("status") != "completed" or not item.get("metrics"):
            continue
        conditions = item["metrics"].get("conditions", {})
        lines.append(f"### {item['label']}")
        for condition, values in conditions.items():
            lines.extend(
                [
                    f"- **{condition}** evaluations: {values.get('evaluation_count')}",
                    f"- **{condition}** MAE: {values.get('mean_absolute_error')}",
                    f"- **{condition}** exact agreement: {values.get('exact_agreement_rate')}",
                    f"- **{condition}** evidence validity: {values.get('verified_rate')}",
                ]
            )
        lines.append("")

    lines.extend(
        [
            "## Claim boundary",
            "",
            "Only rows with `status=completed` are empirical benchmark runs. Rows marked `skipped_no_provider_key`, `blocked_provider_smoke_failed`, or `failed_run` are configuration/access/runtime findings, not model-quality results.",
        ]
    )
    return "\n".join(lines) + "\n"


def _parse_csv_arg(value: str | None) -> set[str] | None:
    if not value:
        return None
    parsed = {item.strip() for item in value.split(",") if item.strip()}
    return parsed or None


def _parse_provider_filters(value: str | None) -> set[str] | None:
    parsed = _parse_csv_arg(value)
    if not parsed:
        return None
    aliases = {"claude": "anthropic", "sonnet": "anthropic", "google": "gemini"}
    return {aliases.get(item.lower(), item.lower()) for item in parsed}


def _safe_candidate_rows(candidates: list[ModelCandidate]) -> list[dict[str, Any]]:
    return [
        {
            "label": candidate.label,
            "provider": candidate.provider,
            "model": candidate.model,
            "source": candidate.source,
            "key_configured": bool(provider_specific_key(candidate)[0]),
            "secret_redacted": True,
        }
        for candidate in candidates
    ]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--benchmark-root", type=Path, default=DEFAULT_BENCHMARK_ROOT)
    parser.add_argument("--repetitions", type=int, default=3)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--run-live", action="store_true", help="Actually run non-fallback providers after smoke succeeds.")
    parser.add_argument("--labels", default=None, help="Comma-separated candidate labels to include.")
    parser.add_argument("--provider", "--providers", dest="providers", default=None, help="Comma-separated providers to run, e.g. openai, anthropic, gemini, fallback. Aliases: claude/sonnet -> anthropic.")
    parser.add_argument("--model", "--models", dest="models", default=None, help="Comma-separated exact model IDs to run, e.g. gpt-5.6-sol.")
    parser.add_argument("--no-fallback-control", action="store_true", help="Do not include deterministic fallback control. Use this for provider-only paid runs.")
    parser.add_argument("--force-rerun", action="store_true", help="Opt out of completed-result reuse and rerun the selected provider. This may spend API budget.")
    parser.add_argument("--allow-multi-provider-live", action="store_true", help="Override cost guard and allow --run-live without a provider/model/label filter.")
    parser.add_argument("--list-candidates", action="store_true", help="List resolved candidates and exit without smoke tests or API calls.")
    parser.add_argument("--include-default-candidates", action="store_true")
    parser.add_argument("--no-dotenv-blocks", action="store_true")
    args = parser.parse_args()

    labels = _parse_csv_arg(args.labels)
    providers = _parse_provider_filters(args.providers)
    models = _parse_csv_arg(args.models)
    include_fallback_control = not args.no_fallback_control

    candidates = build_candidates(
        include_default_candidates=args.include_default_candidates,
        use_dotenv_blocks=not args.no_dotenv_blocks,
        include_fallback_control=include_fallback_control,
    )
    if providers:
        candidates = [candidate for candidate in candidates if candidate.provider in providers]
    if models:
        candidates = [candidate for candidate in candidates if candidate.model in models]
    if labels:
        candidates = [candidate for candidate in candidates if candidate.label in labels]

    if args.list_candidates:
        print(json.dumps({"candidates": _safe_candidate_rows(candidates), "secret_redacted": True}, indent=2, ensure_ascii=False))
        return

    if args.run_live and not (labels or providers or models or args.allow_multi_provider_live):
        raise SystemExit(
            "Refusing unfiltered live multi-provider run. Pass --provider/--model/--labels, "
            "or explicitly add --allow-multi-provider-live. This prevents re-running already-completed paid providers."
        )
    if not candidates:
        raise SystemExit("No model candidates matched the selected filters. Use --list-candidates to inspect available labels/providers/models.")

    run_model_comparison(
        benchmark_root=args.benchmark_root,
        repetitions=args.repetitions,
        output_root=args.output_root,
        run_live=args.run_live,
        include_labels=labels,
        include_providers=providers,
        include_models=models,
        include_default_candidates=args.include_default_candidates,
        use_dotenv_blocks=not args.no_dotenv_blocks,
        include_fallback_control=include_fallback_control,
        reuse_completed=not args.force_rerun,
    )


if __name__ == "__main__":
    main()
