"""SQLite schema for PixelClass TIL Phase 1."""

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS scenarios (
    scenario_id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    domain TEXT NOT NULL,
    education_level TEXT NOT NULL,
    learning_objective TEXT NOT NULL,
    source_path TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS personas (
    persona_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    role TEXT NOT NULL,
    description TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS golden_benchmark_items (
    transcript_id TEXT PRIMARY KEY,
    scenario_id TEXT NOT NULL,
    variant TEXT NOT NULL CHECK (variant IN ('strong', 'weak')),
    domain TEXT NOT NULL,
    education_level TEXT NOT NULL,
    transcript_path TEXT NOT NULL,
    ground_truth_path TEXT NOT NULL,
    expected_scores_path TEXT NOT NULL,
    expected_missed_opportunities_path TEXT NOT NULL,
    expert_annotation_path TEXT NOT NULL,
    FOREIGN KEY (scenario_id) REFERENCES scenarios(scenario_id)
);

CREATE TABLE IF NOT EXISTS sessions (
    session_id TEXT PRIMARY KEY,
    scenario_id TEXT NOT NULL,
    mode TEXT NOT NULL,
    created_at TEXT NOT NULL,
    completed_at TEXT,
    FOREIGN KEY (scenario_id) REFERENCES scenarios(scenario_id)
);

CREATE TABLE IF NOT EXISTS turns (
    turn_key TEXT PRIMARY KEY,
    turn_id TEXT NOT NULL,
    transcript_id TEXT,
    session_id TEXT,
    speaker_role TEXT NOT NULL,
    speaker_name TEXT NOT NULL,
    message TEXT NOT NULL,
    turn_index INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS evaluation_runs (
    evaluation_id TEXT PRIMARY KEY,
    experiment_id TEXT NOT NULL,
    transcript_id TEXT NOT NULL,
    scenario_id TEXT NOT NULL,
    evaluator_condition TEXT NOT NULL CHECK (evaluator_condition IN ('baseline', 'til')),
    model_name TEXT NOT NULL,
    prompt_version TEXT NOT NULL,
    rubric_version TEXT NOT NULL,
    temperature REAL NOT NULL,
    seed INTEGER,
    started_at TEXT NOT NULL,
    completed_at TEXT,
    latency_ms INTEGER,
    input_tokens INTEGER,
    output_tokens INTEGER,
    estimated_cost REAL,
    raw_response_path TEXT,
    status TEXT NOT NULL,
    error_message TEXT,
    FOREIGN KEY (transcript_id) REFERENCES golden_benchmark_items(transcript_id)
);

CREATE TABLE IF NOT EXISTS feedback_items (
    feedback_item_id TEXT PRIMARY KEY,
    evaluation_id TEXT NOT NULL,
    criterion TEXT NOT NULL,
    claim TEXT NOT NULL,
    score INTEGER CHECK (score BETWEEN 1 AND 5),
    suggested_action TEXT,
    confidence REAL,
    verification_status TEXT,
    FOREIGN KEY (evaluation_id) REFERENCES evaluation_runs(evaluation_id)
);

CREATE TABLE IF NOT EXISTS evidence_links (
    evidence_link_id TEXT PRIMARY KEY,
    feedback_item_id TEXT NOT NULL,
    turn_id TEXT NOT NULL,
    evidence_quote TEXT NOT NULL,
    FOREIGN KEY (feedback_item_id) REFERENCES feedback_items(feedback_item_id)
);

CREATE TABLE IF NOT EXISTS verification_results (
    verification_id TEXT PRIMARY KEY,
    evaluation_id TEXT NOT NULL,
    verifier_version TEXT NOT NULL,
    status TEXT NOT NULL,
    details_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (evaluation_id) REFERENCES evaluation_runs(evaluation_id)
);

CREATE TABLE IF NOT EXISTS blinding_mappings (
    mapping_id TEXT PRIMARY KEY,
    transcript_id TEXT NOT NULL,
    reviewer_id TEXT NOT NULL,
    display_label TEXT NOT NULL CHECK (display_label IN ('Evaluation A', 'Evaluation B')),
    actual_condition TEXT NOT NULL CHECK (actual_condition IN ('baseline', 'til')),
    evaluation_id TEXT NOT NULL,
    revealed INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY (transcript_id) REFERENCES golden_benchmark_items(transcript_id),
    FOREIGN KEY (evaluation_id) REFERENCES evaluation_runs(evaluation_id)
);

CREATE TABLE IF NOT EXISTS human_annotations (
    annotation_id TEXT PRIMARY KEY,
    reviewer_id TEXT NOT NULL,
    evaluation_id TEXT NOT NULL,
    feedback_item_id TEXT,
    blinded_label TEXT NOT NULL,
    criterion TEXT NOT NULL,
    ai_score INTEGER,
    human_score INTEGER CHECK (human_score BETWEEN 1 AND 5),
    accept INTEGER NOT NULL,
    fabricated_evidence INTEGER NOT NULL,
    unsupported_inference INTEGER NOT NULL,
    pedagogical_disagreement INTEGER NOT NULL,
    missed_issue INTEGER NOT NULL,
    usefulness INTEGER CHECK (usefulness BETWEEN 1 AND 5),
    review_time_seconds INTEGER,
    comment TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (evaluation_id) REFERENCES evaluation_runs(evaluation_id),
    FOREIGN KEY (feedback_item_id) REFERENCES feedback_items(feedback_item_id)
);

CREATE TABLE IF NOT EXISTS exports (
    export_id TEXT PRIMARY KEY,
    experiment_id TEXT NOT NULL,
    export_path TEXT NOT NULL,
    reproducibility_manifest_path TEXT NOT NULL,
    created_at TEXT NOT NULL
);
"""
