"""Build the SQLite database the funnel/cohort/LTV analysis runs against.

Usage: python -m src.build_db
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

from src.generator import generate_saas_data

DB_PATH = Path(__file__).resolve().parents[1] / "data" / "saas.db"
SCHEMA_PATH = Path(__file__).resolve().parents[1] / "sql" / "00_schema.sql"
# an event_id column isn't produced by the generator -- SQLite assigns it
# automatically via INTEGER PRIMARY KEY on insert, so events are loaded
# without that column and let the DB fill it in.


def build_db(db_path: Path = DB_PATH, seed: int = 42) -> Path:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    tables = generate_saas_data(seed=seed)

    conn = sqlite3.connect(db_path)
    try:
        conn.executescript(SCHEMA_PATH.read_text())

        tables["users"].to_sql("users", conn, if_exists="append", index=False)
        tables["events"].to_sql("events", conn, if_exists="append", index=False)
        tables["subscriptions"].to_sql("subscriptions", conn, if_exists="append", index=False)
        conn.commit()
    finally:
        conn.close()
    return db_path


if __name__ == "__main__":
    path = build_db()
    print(f"Database built at {path}")
