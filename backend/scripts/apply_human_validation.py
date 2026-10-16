"""Apply human validation decisions to the real-classroom benchmark.

This script reads a validation CSV generated under
``thesis-project/human_validation/real_classroom_v0_4/human_validation_master.csv``
and either summarises completion status or applies validated score / missed-
opportunity decisions to the benchmark artifacts.

Dry run / summary only:
    uv run python -m scripts.apply_human_validation \
      --master-csv "D:/Mythesis(Honours)/thesis-project/human_validation/real_classroom_v0_4/human_validation_master.csv"

Apply after the CSV is filled:
    uv run python -m scripts.apply_human_validation \
      --master-csv "D:/Mythesis(Honours)/thesis-project/human_validation/real_classroom_v0_4/human_validation_master.csv" \
      --apply --reviewer-id human_validator_01 --review-status expert_reviewed
"""

from __future__ import annotations

import argparse
import csv
import json
import shutil
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.benchmark_loader import GoldenBenchmarkLoader
from app.config import REQUIRED_RUBRIC_CRITERIA

VALID_SCORE_DECISIONS = {"accept", "revise", "reject"}
VALID_MISSED_DECISIONS = {"accept", "revise", "reject"}
VALID_REVIEW_STATUSES = {
    "draft",
    "researcher_annotated",
    "expert_reviewed",
    "adjudicated",
    "human_validated_with_domain_flags",
}


@dataclass
class ValidationSummary:
    total_rows: int
    score_rows: int
    missed_rows: int
    new_missed_rows: int
    complete_score_rows: int
    complete_missed_rows: int
    complete_new_missed_rows: int
    errors: list[str]
    warnings: list[str]

    @property
    def complete(self) -> bool:
        return not self.errors and self.complete_score_rows == self.score_rows and self.complete_missed_rows == self.missed_rows


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, data: dict[str, Any]) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _norm(value: Any) -> str:
    return str(value or "").strip()


def _norm_decision(value: Any) -> str:
    return _norm(value).lower()


def _parse_score(value: Any) -> int | None:
    text = _norm(value)
    if not text:
        return None
    try:
        score = int(text)
    except ValueError:
        return None
    if 1 <= score <= 5:
        return score
    return None


def _split_ids(value: Any) -> list[str]:
    text = _norm(value)
    if not text:
        return []
    return [part.strip() for part in text.replace(",", ";").split(";") if part.strip()]


def _read_master_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _variant_dirs_by_transcript(root: Path) -> dict[str, Path]:
    loader = GoldenBenchmarkLoader(root)
    mapping: dict[str, Path] = {}
    for item in loader.list_items():
        mapping[item["transcript_id"]] = loader.find_variant_dir(item["transcript_id"])
    return mapping


def _validate_evidence_ids(root: Path, tid: str, ids: list[str], errors: list[str]) -> None:
    if not ids:
        return
    loader = GoldenBenchmarkLoader(root)
    transcript = loader.load_transcript(tid)
    valid_ids = {turn.turn_id for turn in transcript.turns}
    for evidence_id in ids:
        if evidence_id not in valid_ids:
            errors.append(f"{tid}: evidence id not found: {evidence_id}")


def summarise(root: Path, master_csv: Path) -> ValidationSummary:
    rows = _read_master_csv(master_csv)
    errors: list[str] = []
    warnings: list[str] = []
    variant_dirs = _variant_dirs_by_transcript(root)

    score_rows = missed_rows = new_missed_rows = 0
    complete_score_rows = complete_missed_rows = complete_new_missed_rows = 0
    seen_score_keys: set[tuple[str, str]] = set()
    seen_missed_keys: set[tuple[str, str]] = set()
    per_transcript_score_criteria: dict[str, set[str]] = defaultdict(set)

    for i, row in enumerate(rows, start=2):
        row_type = _norm_decision(row.get("row_type"))
        tid = _norm(row.get("transcript_id"))
        key = _norm(row.get("criterion_or_issue_id"))
        if not tid:
            errors.append(f"row {i}: missing transcript_id")
            continue
        if tid not in variant_dirs:
            errors.append(f"row {i}: unknown transcript_id {tid!r}")
            continue
        if row_type == "score":
            score_rows += 1
            if key not in REQUIRED_RUBRIC_CRITERIA:
                errors.append(f"row {i}: unknown score criterion {key!r}")
            pair = (tid, key)
            if pair in seen_score_keys:
                errors.append(f"row {i}: duplicate score row for {tid}/{key}")
            seen_score_keys.add(pair)
            per_transcript_score_criteria[tid].add(key)
            decision = _norm_decision(row.get("score_decision"))
            validator_score = _parse_score(row.get("validator_score"))
            if decision not in VALID_SCORE_DECISIONS:
                warnings.append(f"row {i}: score decision missing/incomplete for {tid}/{key}")
                continue
            if decision in {"revise", "reject"} and validator_score is None:
                errors.append(f"row {i}: {decision} score row requires validator_score 1-5 for {tid}/{key}")
                continue
            if validator_score is not None and not _norm(row.get("validator_comment")) and decision != "accept":
                warnings.append(f"row {i}: revised/rejected score has no validator_comment for {tid}/{key}")
            _validate_evidence_ids(root, tid, _split_ids(row.get("evidence_turn_ids")), errors)
            complete_score_rows += 1
        elif row_type == "missed_opportunity":
            missed_rows += 1
            pair = (tid, key)
            if pair in seen_missed_keys:
                errors.append(f"row {i}: duplicate missed-opportunity row for {tid}/{key}")
            seen_missed_keys.add(pair)
            decision = _norm_decision(row.get("missed_decision"))
            if decision not in VALID_MISSED_DECISIONS:
                warnings.append(f"row {i}: missed decision missing/incomplete for {tid}/{key}")
                continue
            if decision == "revise" and not (_norm(row.get("revised_description")) or _norm(row.get("revised_expected_action"))):
                warnings.append(f"row {i}: revise missed row has no revised text for {tid}/{key}")
            _validate_evidence_ids(root, tid, _split_ids(row.get("evidence_turn_ids")), errors)
            complete_missed_rows += 1
        elif row_type == "new_missed_opportunity":
            new_missed_rows += 1
            if not key:
                errors.append(f"row {i}: new missed opportunity needs criterion_or_issue_id")
            if not _norm(row.get("revised_description")):
                errors.append(f"row {i}: new missed opportunity needs revised_description")
            if not _norm(row.get("revised_expected_action")):
                errors.append(f"row {i}: new missed opportunity needs revised_expected_action")
            evidence_ids = _split_ids(row.get("evidence_turn_ids"))
            if not evidence_ids:
                errors.append(f"row {i}: new missed opportunity needs evidence_turn_ids")
            _validate_evidence_ids(root, tid, evidence_ids, errors)
            if not errors:
                complete_new_missed_rows += 1
        else:
            errors.append(f"row {i}: unknown row_type {row_type!r}")

    for tid in variant_dirs:
        missing = REQUIRED_RUBRIC_CRITERIA - per_transcript_score_criteria.get(tid, set())
        if missing:
            errors.append(f"{tid}: missing score criteria in master CSV: {sorted(missing)}")

    return ValidationSummary(
        total_rows=len(rows),
        score_rows=score_rows,
        missed_rows=missed_rows,
        new_missed_rows=new_missed_rows,
        complete_score_rows=complete_score_rows,
        complete_missed_rows=complete_missed_rows,
        complete_new_missed_rows=complete_new_missed_rows,
        errors=errors,
        warnings=warnings,
    )


def _backup_benchmark(root: Path, output_dir: Path) -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    backup = output_dir / "backups" / f"golden_benchmark_real_v0_before_human_validation_{stamp}"
    backup.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(root, backup)
    return backup


def apply_validation(root: Path, master_csv: Path, reviewer_id: str, review_status: str, audit_dir: Path) -> dict[str, Any]:
    if review_status not in VALID_REVIEW_STATUSES:
        raise SystemExit(f"Invalid --review-status {review_status!r}. Expected one of {sorted(VALID_REVIEW_STATUSES)}")

    summary = summarise(root, master_csv)
    if summary.errors:
        raise SystemExit("Cannot apply validation while errors remain:\n" + "\n".join(summary.errors[:30]))
    if summary.complete_score_rows != summary.score_rows or summary.complete_missed_rows != summary.missed_rows:
        raise SystemExit("Cannot apply validation until all score and missed-opportunity rows have decisions.")

    rows = _read_master_csv(master_csv)
    variant_dirs = _variant_dirs_by_transcript(root)
    stamp = datetime.now(timezone.utc).isoformat()
    backup = _backup_benchmark(root, audit_dir)
    applied: dict[str, Any] = {"backup": str(backup), "transcripts": {}}

    rows_by_tid: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        rows_by_tid[_norm(row.get("transcript_id"))].append(row)

    for tid, vdir in variant_dirs.items():
        transcript_rows = rows_by_tid.get(tid, [])
        expected_scores = _load_json(vdir / "expected_scores.json")
        missed = _load_json(vdir / "expected_missed_opportunities.json")
        ground_truth = _load_json(vdir / "ground_truth.json")

        score_changes = []
        missed_changes = []
        final_scores = dict(expected_scores["scores"])
        final_notes = dict(expected_scores.get("notes", {}))
        final_missed_by_id = {item["id"]: item for item in missed.get("missed_opportunities", [])}

        for row in transcript_rows:
            row_type = _norm_decision(row.get("row_type"))
            key = _norm(row.get("criterion_or_issue_id"))
            if row_type == "score":
                decision = _norm_decision(row.get("score_decision"))
                validator_score = _parse_score(row.get("validator_score"))
                old_score = final_scores.get(key)
                new_score = validator_score if validator_score is not None else old_score
                final_scores[key] = int(new_score)
                comment = _norm(row.get("validator_comment"))
                if comment:
                    final_notes[key] = comment
                score_changes.append({"criterion": key, "decision": decision, "old_score": old_score, "new_score": new_score, "comment": comment})
            elif row_type == "missed_opportunity":
                decision = _norm_decision(row.get("missed_decision"))
                item = final_missed_by_id.get(key)
                if not item:
                    continue
                if decision == "reject":
                    final_missed_by_id.pop(key, None)
                    missed_changes.append({"id": key, "decision": decision})
                else:
                    if decision == "revise":
                        desc = _norm(row.get("revised_description"))
                        action = _norm(row.get("revised_expected_action"))
                        if desc:
                            item["description"] = desc
                        if action:
                            item["expected_action"] = action
                    missed_changes.append({"id": key, "decision": decision, "comment": _norm(row.get("validator_comment"))})
            elif row_type == "new_missed_opportunity":
                final_missed_by_id[key] = {
                    "id": key,
                    "criterion": "missed_pedagogical_opportunity",
                    "description": _norm(row.get("revised_description")),
                    "evidence_turn_ids": _split_ids(row.get("evidence_turn_ids")),
                    "expected_action": _norm(row.get("revised_expected_action")),
                }
                missed_changes.append({"id": key, "decision": "new"})

        expected_scores["scores"] = final_scores
        expected_scores["notes"] = final_notes
        missed["missed_opportunities"] = list(final_missed_by_id.values())
        ground_truth["review_status"] = review_status
        ground_truth["summary"] = f"{ground_truth.get('summary', '').rstrip()} Human validation applied by {reviewer_id} on {stamp}."
        issue = f"Human validation applied by {reviewer_id} on {stamp}; not independent multi-expert adjudication unless separately documented."
        if issue not in ground_truth.setdefault("known_issues", []):
            ground_truth["known_issues"].append(issue)

        _write_json(vdir / "expected_scores.json", expected_scores)
        _write_json(vdir / "expected_missed_opportunities.json", missed)
        _write_json(vdir / "ground_truth.json", ground_truth)

        with (vdir / "expert_annotation.csv").open("w", encoding="utf-8", newline="") as handle:
            fields = [
                "transcript_id",
                "reviewer_id",
                "criterion",
                "human_score",
                "issue_id",
                "evidence_turn_ids",
                "accepted_ground_truth",
                "comment",
                "timestamp",
            ]
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            for criterion in sorted(final_scores):
                source = next((r for r in transcript_rows if _norm_decision(r.get("row_type")) == "score" and _norm(r.get("criterion_or_issue_id")) == criterion), {})
                writer.writerow({
                    "transcript_id": tid,
                    "reviewer_id": reviewer_id,
                    "criterion": criterion,
                    "human_score": final_scores[criterion],
                    "issue_id": _norm(source.get("score_decision")) or "validated",
                    "evidence_turn_ids": _norm(source.get("evidence_turn_ids")),
                    "accepted_ground_truth": str((_norm_decision(source.get("score_decision")) or "accept") == "accept").lower(),
                    "comment": final_notes.get(criterion, ""),
                    "timestamp": stamp,
                })

        applied["transcripts"][tid] = {"score_changes": score_changes, "missed_changes": missed_changes}

    audit_dir.mkdir(parents=True, exist_ok=True)
    audit_path = audit_dir / f"human_validation_apply_audit_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json"
    _write_json(audit_path, applied)
    applied["audit_path"] = str(audit_path)
    return applied


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--benchmark-root", default="data/golden_benchmark_real_v0", type=Path)
    parser.add_argument("--master-csv", required=True, type=Path)
    parser.add_argument("--apply", action="store_true", help="Apply completed validation decisions to benchmark files.")
    parser.add_argument("--reviewer-id", default="human_validator_01")
    parser.add_argument("--review-status", default="expert_reviewed", choices=sorted(VALID_REVIEW_STATUSES))
    parser.add_argument("--audit-dir", default=Path("D:/Mythesis(Honours)/thesis-project/human_validation/real_classroom_v0_4"), type=Path)
    args = parser.parse_args()

    root = args.benchmark_root.resolve()
    master_csv = args.master_csv.resolve()
    summary = summarise(root, master_csv)
    print(json.dumps({
        "benchmark_root": str(root),
        "master_csv": str(master_csv),
        "total_rows": summary.total_rows,
        "score_rows": summary.score_rows,
        "missed_rows": summary.missed_rows,
        "new_missed_rows": summary.new_missed_rows,
        "complete_score_rows": summary.complete_score_rows,
        "complete_missed_rows": summary.complete_missed_rows,
        "complete_new_missed_rows": summary.complete_new_missed_rows,
        "warnings": summary.warnings[:50],
        "errors": summary.errors[:50],
        "ready_to_apply": summary.complete,
    }, indent=2, ensure_ascii=False))

    if args.apply:
        applied = apply_validation(root, master_csv, args.reviewer_id, args.review_status, args.audit_dir)
        print(json.dumps({"applied": True, **applied}, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
