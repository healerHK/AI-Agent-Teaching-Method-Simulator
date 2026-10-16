"""Configuration helpers for PixelClass TIL Phase 1."""

from __future__ import annotations

import os
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND_ROOT.parent


def load_local_env(path: Path = REPO_ROOT / ".env") -> None:
    """Load local .env values without requiring python-dotenv.

    Existing environment variables win, so CI/test envs can override local secrets.
    """

    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


load_local_env()

DATA_ROOT = BACKEND_ROOT / "data"
GOLDEN_BENCHMARK_ROOT = DATA_ROOT / "golden_benchmark"
DATABASE_PATH = DATA_ROOT / "til_research.db"
THESIS_PROJECT_ROOT = Path(os.getenv("THESIS_PROJECT_ROOT", str(REPO_ROOT / "research_outputs")))
EXPORT_ROOT = Path(os.getenv("EXPORT_ROOT", str(THESIS_PROJECT_ROOT / "results")))

DATASET_VERSION_FILE = GOLDEN_BENCHMARK_ROOT / "DATASET_VERSION.json"
RUBRIC_VERSION = "rubric_v1.0"
VERIFIER_VERSION = "evidence_verifier_v1"
METRICS_VERSION = "metrics_v1"

SUPPORTED_LLM_PROVIDERS = {"fallback", "openai", "anthropic", "gemini", "openai_compatible"}

REQUIRED_RUBRIC_CRITERIA = {
    "pck_conceptual_accuracy",
    "scaffolding",
    "formative_assessment",
    "cognitive_questioning",
    "missed_pedagogical_opportunity",
}


def ensure_data_dirs() -> None:
    """Create runtime data directories used by Phase 1 and later phases."""
    for path in [
        DATA_ROOT,
        GOLDEN_BENCHMARK_ROOT,
        DATA_ROOT / "raw_outputs",
        DATA_ROOT / "exports",
        DATA_ROOT / "charts",
    ]:
        path.mkdir(parents=True, exist_ok=True)
