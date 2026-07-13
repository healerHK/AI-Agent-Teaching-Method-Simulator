from pathlib import Path

from app.database import init_db, table_names


REQUIRED_TABLES = {
    "scenarios",
    "personas",
    "golden_benchmark_items",
    "sessions",
    "turns",
    "evaluation_runs",
    "feedback_items",
    "evidence_links",
    "verification_results",
    "blinding_mappings",
    "human_annotations",
    "exports",
}


def test_database_schema_initializes_required_tables(tmp_path: Path):
    db_path = tmp_path / "til_research_test.db"

    init_db(db_path)

    assert REQUIRED_TABLES.issubset(table_names(db_path))


def test_database_init_is_idempotent(tmp_path: Path):
    db_path = tmp_path / "til_research_test.db"

    init_db(db_path)
    init_db(db_path)

    assert REQUIRED_TABLES.issubset(table_names(db_path))
