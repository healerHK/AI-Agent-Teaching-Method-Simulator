"""Apply defensible human-validation final labels for real-classroom benchmark v0.4.

Reads ``human_validation_master_defensible.csv`` with final-label fields:
final_score, human_decision, evidence_verified, domain_check_required,
domain_check_result, confidence, evidence_turn_ids, adjudication_note.

Dry run:
    uv run python -m scripts.apply_human_validation_v2 \
      --master-csv "D:/Mythesis(Honours)/thesis-project/human_validation/real_classroom_v0_4/human_validation_master_defensible.csv"

Apply:
    uv run python -m scripts.apply_human_validation_v2 \
      --master-csv "D:/Mythesis(Honours)/thesis-project/human_validation/real_classroom_v0_4/human_validation_master_defensible.csv" \
      --apply --reviewer-id human_validator_ty
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import re
import shutil
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.benchmark_loader import GoldenBenchmarkLoader
from app.config import REQUIRED_RUBRIC_CRITERIA

DECISIONS = {"accept", "revise", "reject"}
EVIDENCE = {"yes", "partial", "no", "uncertain"}
DOMAIN_REQUIRED = {"yes", "no"}
DOMAIN_RESULT = {"pass", "fail", "uncertain", "not_required", "pending"}
CONFIDENCE = {"high", "medium-high", "medium", "low"}


def norm(v: Any) -> str:
    return str(v or "").strip()


def lower(v: Any) -> str:
    return norm(v).lower()


def _decode_csv_text(path: Path) -> str:
    raw = path.read_bytes()
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        # Excel on Windows may rewrite edited CSVs as CP1252/Latin-1 with smart quotes.
        text = raw.decode("latin-1")
    sequence_replacements = {
        "â\x80\x98": "‘",
        "â\x80\x99": "’",
        "â\x80\x9c": "“",
        "â\x80\x9d": "”",
        "â\x80\x93": "–",
        "â\x80\x94": "—",
        "â\x80¦": "…",
        "â\x86\x92": "→",
    }
    for bad, good in sequence_replacements.items():
        text = text.replace(bad, good)
    cp1252_controls = {
        "\x91": "‘",
        "\x92": "’",
        "\x93": "“",
        "\x94": "”",
        "\x95": "•",
        "\x96": "–",
        "\x97": "—",
        "\x9d": "”",
    }
    for bad, good in cp1252_controls.items():
        text = text.replace(bad, good)
    return text


def read_rows(path: Path) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(_decode_csv_text(path))))


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def split_ids(value: str) -> list[str]:
    return [x.strip() for x in norm(value).replace(",", ";").split(";") if x.strip()]


def parse_score(value: str) -> int | None:
    try:
        score = int(norm(value))
    except ValueError:
        return None
    return score if 1 <= score <= 5 else None


def variant_dirs(root: Path) -> dict[str, Path]:
    loader = GoldenBenchmarkLoader(root)
    return {item["transcript_id"]: loader.find_variant_dir(item["transcript_id"]) for item in loader.list_items()}


def validate(root: Path, rows: list[dict[str, str]]) -> dict[str, Any]:
    loader = GoldenBenchmarkLoader(root)
    dirs = variant_dirs(root)
    errors: list[str] = []
    warnings: list[str] = []
    complete = 0
    by_tid_criteria: dict[str, set[str]] = defaultdict(set)

    for line_no, row in enumerate(rows, start=2):
        row_type = lower(row.get("row_type"))
        tid = norm(row.get("transcript_id"))
        key = norm(row.get("criterion_or_issue_id"))
        if tid not in dirs:
            errors.append(f"row {line_no}: unknown transcript_id {tid!r}")
            continue
        decision = lower(row.get("human_decision"))
        evidence_verified = lower(row.get("evidence_verified"))
        domain_required = lower(row.get("domain_check_required"))
        domain_result = lower(row.get("domain_check_result"))
        confidence = lower(row.get("confidence"))

        if row_type == "score":
            by_tid_criteria[tid].add(key)
        if decision not in DECISIONS:
            warnings.append(f"row {line_no}: missing human_decision for {tid}/{key}")
            continue
        if evidence_verified not in EVIDENCE:
            errors.append(f"row {line_no}: evidence_verified must be yes/partial/no/uncertain")
        if domain_required not in DOMAIN_REQUIRED:
            errors.append(f"row {line_no}: domain_check_required must be yes/no")
        if domain_result not in DOMAIN_RESULT:
            errors.append(f"row {line_no}: invalid domain_check_result")
        if domain_required == "yes" and domain_result in {"not_required", "pending", ""}:
            warnings.append(f"row {line_no}: domain check required but result still {domain_result or 'blank'} for {tid}/{key}")
        if domain_required == "no" and domain_result not in {"not_required", "pass", "uncertain"}:
            warnings.append(f"row {line_no}: domain_check_result unusual for non-domain row {tid}/{key}")
        if confidence not in CONFIDENCE:
            warnings.append(f"row {line_no}: missing confidence high/medium-high/medium/low for {tid}/{key}")
            continue

        evidence_ids = split_ids(row.get("evidence_turn_ids", ""))
        valid_ids = {turn.turn_id for turn in loader.load_transcript(tid).turns}
        missing_ids = [e for e in evidence_ids if e not in valid_ids]
        if missing_ids:
            errors.append(f"row {line_no}: evidence turn ids not found for {tid}: {missing_ids}")
        if not evidence_ids:
            errors.append(f"row {line_no}: no evidence_turn_ids for {tid}/{key}")

        if row_type == "score":
            by_tid_criteria[tid].add(key)
            if key not in REQUIRED_RUBRIC_CRITERIA:
                errors.append(f"row {line_no}: unknown rubric criterion {key!r}")
            score = parse_score(row.get("final_score", ""))
            if score is None:
                errors.append(f"row {line_no}: final_score must be 1-5 for score row")
        elif row_type == "missed_opportunity":
            if decision != "reject" and not norm(row.get("final_description")):
                errors.append(f"row {line_no}: accepted/revised missed opportunity needs final_description")
            if decision != "reject" and not norm(row.get("final_expected_action")):
                errors.append(f"row {line_no}: accepted/revised missed opportunity needs final_expected_action")
        else:
            errors.append(f"row {line_no}: unknown row_type {row_type!r}")

        complete += 1

    for tid in dirs:
        missing = REQUIRED_RUBRIC_CRITERIA - by_tid_criteria.get(tid, set())
        if missing:
            errors.append(f"{tid}: missing score criteria {sorted(missing)}")

    return {
        "total_rows": len(rows),
        "complete_rows": complete,
        "warnings": warnings,
        "errors": errors,
        "ready_to_apply": complete == len(rows) and not errors and not warnings,
    }


def backup(root: Path, audit_dir: Path) -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    dst = audit_dir / "backups" / f"golden_benchmark_real_v0_before_validation_v2_{stamp}"
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(root, dst)
    return dst


def apply(root: Path, rows: list[dict[str, str]], reviewer_id: str, audit_dir: Path) -> dict[str, Any]:
    check = validate(root, rows)
    if not check["ready_to_apply"]:
        raise SystemExit("Not ready to apply. Fix warnings/errors first.\n" + json.dumps(check, indent=2, ensure_ascii=False))

    dirs = variant_dirs(root)
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[norm(row.get("transcript_id"))].append(row)

    stamp = datetime.now(timezone.utc).isoformat()
    backup_path = backup(root, audit_dir)
    audit: dict[str, Any] = {"reviewer_id": reviewer_id, "applied_at": stamp, "backup": str(backup_path), "transcripts": {}}

    for tid, vdir in dirs.items():
        expected_scores = load_json(vdir / "expected_scores.json")
        expected_missed = load_json(vdir / "expected_missed_opportunities.json")
        ground_truth = load_json(vdir / "ground_truth.json")
        final_labels: list[dict[str, Any]] = []

        missed_by_id = {m["id"]: m for m in expected_missed.get("missed_opportunities", [])}
        scores = dict(expected_scores.get("scores", {}))
        notes = dict(expected_scores.get("notes", {}))

        for row in grouped[tid]:
            row_type = lower(row.get("row_type"))
            key = norm(row.get("criterion_or_issue_id"))
            decision = lower(row.get("human_decision"))
            label = {
                "row_type": row_type,
                "transcript_id": tid,
                "label_id": key,
                "final_score": parse_score(row.get("final_score", "")) if row_type == "score" else None,
                "human_decision": decision,
                "evidence_verified": lower(row.get("evidence_verified")),
                "domain_check_required": lower(row.get("domain_check_required")),
                "domain_check_result": lower(row.get("domain_check_result")),
                "confidence": lower(row.get("confidence")),
                "evidence_turn_ids": split_ids(row.get("evidence_turn_ids", "")),
                "adjudication_note": norm(row.get("adjudication_note")),
            }
            final_labels.append(label)

            if row_type == "score":
                scores[key] = int(label["final_score"])
                if label["adjudication_note"]:
                    notes[key] = label["adjudication_note"]
            elif row_type == "missed_opportunity":
                if decision == "reject":
                    missed_by_id.pop(key, None)
                else:
                    item = missed_by_id.get(key, {"id": key, "criterion": "missed_pedagogical_opportunity"})
                    item["description"] = norm(row.get("final_description"))
                    item["expected_action"] = norm(row.get("final_expected_action"))
                    item["evidence_turn_ids"] = label["evidence_turn_ids"]
                    missed_by_id[key] = item

        expected_scores["scores"] = scores
        expected_scores["notes"] = notes
        expected_missed["missed_opportunities"] = list(missed_by_id.values())
        ground_truth["review_status"] = "human_validated_with_domain_flags"
        base_summary = re.sub(
            r"(?:\s+Human validation v2 applied by .*? on [0-9T:.+\-]+\.)+",
            "",
            ground_truth.get("summary", ""),
        ).strip()
        ground_truth["summary"] = f"{base_summary} Human validation v2 applied by {reviewer_id} on {stamp}."
        issue = "Final labels include human_decision, evidence_verified, domain_check_required, domain_check_result, confidence, evidence_turn_ids, and adjudication_note; this is a human-validated annotation set, not independent multi-expert ground truth."
        if issue not in ground_truth.setdefault("known_issues", []):
            ground_truth["known_issues"].append(issue)

        write_json(vdir / "expected_scores.json", expected_scores)
        write_json(vdir / "expected_missed_opportunities.json", expected_missed)
        write_json(vdir / "ground_truth.json", ground_truth)

        with (vdir / "human_final_labels.csv").open("w", encoding="utf-8", newline="") as f:
            fields = ["row_type", "transcript_id", "label_id", "final_score", "human_decision", "evidence_verified", "domain_check_required", "domain_check_result", "confidence", "evidence_turn_ids", "adjudication_note"]
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            for label in final_labels:
                writer.writerow({**label, "evidence_turn_ids": ";".join(label["evidence_turn_ids"])})

        audit["transcripts"][tid] = {"final_label_count": len(final_labels)}

    audit_dir.mkdir(parents=True, exist_ok=True)
    audit_path = audit_dir / f"human_validation_v2_apply_audit_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json"
    write_json(audit_path, audit)
    audit["audit_path"] = str(audit_path)
    return audit


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--benchmark-root", type=Path, default=Path("data/golden_benchmark_real_v0"))
    parser.add_argument("--master-csv", type=Path, required=True)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--reviewer-id", default="human_validator_ty")
    parser.add_argument("--audit-dir", type=Path, default=Path("D:/Mythesis(Honours)/thesis-project/human_validation/real_classroom_v0_4"))
    args = parser.parse_args()

    rows = read_rows(args.master_csv)
    check = validate(args.benchmark_root, rows)
    print(json.dumps(check, indent=2, ensure_ascii=False))
    if args.apply:
        audit = apply(args.benchmark_root, rows, args.reviewer_id, args.audit_dir)
        print(json.dumps({"applied": True, **audit}, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
