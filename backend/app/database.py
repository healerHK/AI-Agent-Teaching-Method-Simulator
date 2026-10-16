"""SQLite connection and initialization helpers."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from app.config import DATABASE_PATH, ensure_data_dirs
from app.migrations import SCHEMA_SQL


def connect(db_path: Path = DATABASE_PATH) -> sqlite3.Connection:
    ensure_data_dirs()
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(db_path: Path = DATABASE_PATH) -> None:
    ensure_data_dirs()
    with connect(db_path) as conn:
        conn.executescript(SCHEMA_SQL)
        conn.commit()


def table_names(db_path: Path = DATABASE_PATH) -> set[str]:
    with connect(db_path) as conn:
        rows = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        ).fetchall()
    return {row["name"] for row in rows}
