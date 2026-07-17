"""Golden benchmark loading helpers for Phase 3."""

from __future__ import annotations

import json
from pathlib import Path

from app.config import GOLDEN_BENCHMARK_ROOT
from app.models import (
    BenchmarkTranscript,
    DatasetVersion,
    ExpectedMissedOpportunities,
    ExpectedScores,
    GroundTruth,
    Scenario,
)


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


class GoldenBenchmarkLoader:
    def __init__(self, root: Path = GOLDEN_BENCHMARK_ROOT) -> None:
        self.root = root

    def dataset_version(self) -> DatasetVersion:
        return DatasetVersion.model_validate(load_json(self.root / "DATASET_VERSION.json"))

    def list_items(self) -> list[dict[str, str]]:
        items: list[dict[str, str]] = []
        for scenario_dir in sorted(path for path in self.root.iterdir() if path.is_dir()):
            scenario_path = scenario_dir / "scenario.json"
            if not scenario_path.exists():
                continue
            scenario = Scenario.model_validate(load_json(scenario_path))
            for variant in ["strong", "weak"]:
                transcript_path = scenario_dir / variant / "transcript.json"
                if not transcript_path.exists():
                    continue
                transcript = BenchmarkTranscript.model_validate(load_json(transcript_path))
                items.append(
                    {
                        "transcript_id": transcript.transcript_id,
                        "scenario_id": transcript.scenario_id,
                        "scenario_title": scenario.title,
                        "variant": transcript.variant,
                        "domain": transcript.domain,
                        "education_level": transcript.education_level,
                    }
                )
        return items

    def find_variant_dir(self, transcript_id: str) -> Path:
        for scenario_dir in sorted(path for path in self.root.iterdir() if path.is_dir()):
            for variant in ["strong", "weak"]:
                variant_dir = scenario_dir / variant
                transcript_path = variant_dir / "transcript.json"
                if not transcript_path.exists():
                    continue
                transcript = BenchmarkTranscript.model_validate(load_json(transcript_path))
                if transcript.transcript_id == transcript_id:
                    return variant_dir
        raise FileNotFoundError(f"Unknown transcript_id: {transcript_id}")

    def load_transcript(self, transcript_id: str) -> BenchmarkTranscript:
        variant_dir = self.find_variant_dir(transcript_id)
        return BenchmarkTranscript.model_validate(load_json(variant_dir / "transcript.json"))

    def load_ground_truth(self, transcript_id: str) -> GroundTruth:
        variant_dir = self.find_variant_dir(transcript_id)
        return GroundTruth.model_validate(load_json(variant_dir / "ground_truth.json"))

    def load_expected_scores(self, transcript_id: str) -> ExpectedScores:
        variant_dir = self.find_variant_dir(transcript_id)
        return ExpectedScores.model_validate(load_json(variant_dir / "expected_scores.json"))

    def load_expected_missed_opportunities(self, transcript_id: str) -> ExpectedMissedOpportunities:
        variant_dir = self.find_variant_dir(transcript_id)
        return ExpectedMissedOpportunities.model_validate(
            load_json(variant_dir / "expected_missed_opportunities.json")
        )
