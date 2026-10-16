"""Load Phase 1 golden benchmark files into SQLite."""

from __future__ import annotations

import json
from pathlib import Path

from app.config import GOLDEN_BENCHMARK_ROOT
from app.database import connect, init_db
from app.models import BenchmarkTranscript, GroundTruth, Scenario


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def iter_benchmark_variants(root: Path = GOLDEN_BENCHMARK_ROOT):
    for scenario_dir in sorted(p for p in root.iterdir() if p.is_dir()):
        scenario_path = scenario_dir / "scenario.json"
        if not scenario_path.exists():
            continue
        for variant in ["strong", "weak"]:
            variant_dir = scenario_dir / variant
            transcript_path = variant_dir / "transcript.json"
            if transcript_path.exists():
                yield scenario_path, variant_dir, transcript_path


def seed_database(root: Path = GOLDEN_BENCHMARK_ROOT) -> None:
    init_db()
    with connect() as conn:
        for scenario_path, variant_dir, transcript_path in iter_benchmark_variants(root):
            scenario = Scenario.model_validate(load_json(scenario_path))
            transcript = BenchmarkTranscript.model_validate(load_json(transcript_path))
            ground_truth_path = variant_dir / "ground_truth.json"
            ground_truth = GroundTruth.model_validate(load_json(ground_truth_path))

            if ground_truth.transcript_id != transcript.transcript_id:
                raise ValueError(f"Ground truth mismatch for {transcript_path}")

            conn.execute(
                """
                INSERT OR REPLACE INTO scenarios
                (scenario_id, title, domain, education_level, learning_objective, source_path)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    scenario.scenario_id,
                    scenario.title,
                    scenario.domain,
                    scenario.education_level,
                    scenario.learning_objective,
                    str(scenario_path),
                ),
            )
            conn.execute(
                """
                INSERT OR REPLACE INTO golden_benchmark_items
                (transcript_id, scenario_id, variant, domain, education_level, transcript_path,
                 ground_truth_path, expected_scores_path, expected_missed_opportunities_path,
                 expert_annotation_path)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    transcript.transcript_id,
                    transcript.scenario_id,
                    transcript.variant,
                    transcript.domain,
                    transcript.education_level,
                    str(transcript_path),
                    str(ground_truth_path),
                    str(variant_dir / "expected_scores.json"),
                    str(variant_dir / "expected_missed_opportunities.json"),
                    str(variant_dir / "expert_annotation.csv"),
                ),
            )
            for index, turn in enumerate(transcript.turns, start=1):
                conn.execute(
                    """
                    INSERT OR REPLACE INTO turns
                    (turn_key, turn_id, transcript_id, session_id, speaker_role, speaker_name, message, turn_index)
                    VALUES (?, ?, ?, NULL, ?, ?, ?, ?)
                    """,
                    (
                        f"{transcript.transcript_id}:{turn.turn_id}",
                        turn.turn_id,
                        transcript.transcript_id,
                        turn.speaker_role,
                        turn.speaker_name,
                        turn.message,
                        index,
                    ),
                )
        conn.commit()


if __name__ == "__main__":
    seed_database()
    print("Seeded PixelClass TIL Phase 1 database.")
