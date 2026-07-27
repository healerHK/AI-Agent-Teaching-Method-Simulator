from app.seed_data import seed_database
from app.database import connect


def test_seed_database_loads_phase1_golden_benchmark_idempotently():
    seed_database()
    seed_database()

    with connect() as conn:
        golden_scenarios = conn.execute(
            "SELECT COUNT(*) AS n FROM scenarios WHERE scenario_id = 'python_loops_001'"
        ).fetchone()["n"]
        items = conn.execute("SELECT COUNT(*) AS n FROM golden_benchmark_items").fetchone()["n"]
        turns = conn.execute(
            "SELECT COUNT(*) AS n FROM turns WHERE transcript_id IS NOT NULL"
        ).fetchone()["n"]

    assert golden_scenarios == 1
    assert items == 2
    assert turns == 18
