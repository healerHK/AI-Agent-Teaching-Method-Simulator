"""Tonight testing pack for PixelClass TIL.

Runs a safe provider status check, optional live provider smoke, and a compact
baseline-vs-TIL benchmark/export that can be used for supervisor/demo testing.

Usage:
  uv run python -m scripts.testing_pack
  uv run python -m scripts.testing_pack --live-provider-smoke
"""

from __future__ import annotations

import argparse
import json
from typing import Any

import httpx

from app.llm_provider import LLMProviderClient, evaluator_provider_config, evaluator_provider_status
from scripts.run_benchmark import run_benchmark


def _safe_live_provider_smoke(condition: str) -> dict[str, Any]:
    """Probe the configured provider with a tiny JSON prompt without exposing secrets."""

    config = evaluator_provider_config(condition)
    result: dict[str, Any] = {
        "condition": condition,
        "provider": config.provider,
        "requested_model": config.model,
        "api_key_configured": bool(config.api_key),
    }
    if config.provider == "fallback":
        result.update({"status": "skipped", "reason": "fallback_provider"})
        return result

    try:
        payload = LLMProviderClient(config).complete_json(
            system_prompt="Return strict JSON only. Use no external facts.",
            user_prompt='Return exactly {"ok": true, "message": "provider_ready"}.',
        )
        result.update(
            {
                "status": "ok",
                "actual_model": config.model,
                "response_keys": sorted(payload.keys()),
            }
        )
    except httpx.HTTPStatusError as exc:
        response = exc.response
        category = "unavailable"
        if response is not None:
            try:
                body = response.json()
                category = str(body.get("error", {}).get("status") or body.get("error", {}).get("code") or category)
            except Exception:
                category = "unavailable"
            status_code = response.status_code
        else:
            status_code = "unknown"
        result.update(
            {
                "status": "failed_provider_http",
                "http_status": status_code,
                "provider_error_category": category,
                "fallback_available": True,
            }
        )
    except Exception as exc:  # keep tonight testing script safe if provider output is malformed
        result.update(
            {
                "status": "failed_provider_client",
                "error_type": type(exc).__name__,
                "fallback_available": True,
            }
        )
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--transcript-id", default="python_loops_weak_001")
    parser.add_argument("--repetitions", type=int, default=1)
    parser.add_argument("--live-provider-smoke", action="store_true")
    args = parser.parse_args()

    print("== PixelClass TIL tonight testing pack ==")
    provider_status = {
        "conditions": [
            evaluator_provider_status("baseline"),
            evaluator_provider_status("til"),
        ],
        "secrets_redacted": True,
    }
    print("provider_status=" + json.dumps(provider_status, indent=2))

    if args.live_provider_smoke:
        print("live_provider_smoke=" + json.dumps(_safe_live_provider_smoke("til"), indent=2))

    experiment_id = run_benchmark(
        conditions=["baseline", "til"],
        repetitions=args.repetitions,
        transcript_id=args.transcript_id,
        export=True,
    )
    print("testing_pack_status=complete")
    print(f"testing_pack_experiment_id={experiment_id}")


if __name__ == "__main__":
    main()
