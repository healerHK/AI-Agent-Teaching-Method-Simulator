"""Check the released thesis inputs and references without provider calls."""
from pathlib import Path
import csv, hashlib, json

def main():
    root = Path(__file__).resolve().parents[2]
    manifest = json.loads((root / "dataset/manifest.json").read_text(encoding="utf-8"))
    catalogue = root / manifest["catalogue"]
    assert hashlib.sha256(catalogue.read_bytes()).hexdigest() == manifest["catalogue_sha256"]
    with catalogue.open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    assert len(rows) == 22
    assert len({r["transcript_id"] for r in rows}) == 22
    assert sum(r["tier"] == "real" for r in rows) == 6
    for row in rows:
        path = root / row["transcript_path"]
        assert hashlib.sha256(path.read_bytes()).hexdigest() == row["transcript_sha256"]
        transcript = json.loads(path.read_text(encoding="utf-8"))
        assert transcript["transcript_id"] == row["transcript_id"]
        assert len(transcript["turns"]) == int(row["turns"])
        ids = [t["turn_id"] for t in transcript["turns"]]
        assert len(ids) == len(set(ids))
        assert all(t["message"].strip() for t in transcript["turns"])
        path = root / row["expected_scores_path"]
        assert hashlib.sha256(path.read_bytes()).hexdigest() == row["expected_scores_sha256"]
        scores = json.loads(path.read_text(encoding="utf-8"))
        assert scores["transcript_id"] == row["transcript_id"]
        assert all(1 <= value <= 5 for value in scores["scores"].values())
    print("Verified 22 transcripts: 6 real and 16 curated; hashes, turn IDs and score references match.")

if __name__ == "__main__":
    main()
