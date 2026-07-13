"""Configuration helpers for PixelClass TIL Phase 1."""

from __future__ import annotations

import os
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND_ROOT.parent
DATA_ROOT = BACKEND_ROOT / "data"
GOLDEN_BENCHMARK_ROOT = DATA_ROOT / "golden_benchmark"
DATABASE_PATH = DATA_ROOT / "til_research.db"
EXPORT_ROOT = Path(os.getenv("EXPORT_ROOT", r"D:/Mythesis(Honours)/MVP_Outputs"))

DATASET_VERSION_FILE = GOLDEN_BENCHMARK_ROOT / "DATASET_VERSION.json"
RUBRIC_VERSION = "rubric_v1.0"
VERIFIER_VERSION = "evidence_verifier_v1"
METRICS_VERSION = "metrics_v1"

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
