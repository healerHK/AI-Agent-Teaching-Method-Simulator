# Thesis benchmark

The catalogue lists the 22 frozen transcripts analysed in the Honours thesis:
six observed classroom transcripts and eight curated scenarios, each with a strong
and a weak teaching variant. Paths, source-page links, turn counts and SHA-256
hashes are recorded in catalogue.csv and manifest.json.

Real-classroom transcript files use anonymised speaker labels. Their strong/
directory is a loader compatibility convention; it does not rate the teacher.
The source-page links document provenance. Classroom audio, video and intermediate
source documents are not part of this repository.

Each transcript is accompanied by expected_scores.json, discrete issue labels,
ground_truth.json and annotation records. The five stored score keys comprise
four core pedagogical criteria and a compatibility score named
missed_pedagogical_opportunity. Discrete missed-opportunity labels are separate.
The real-tier final labels reflect joint author-supervisor review.

The two Python-loop seed transcripts under backend/data/golden_benchmark support
the demo and tests. They are not part of the 22-transcript thesis catalogue.

Run the integrity check from backend/:

    python -m scripts.verify_thesis_dataset
