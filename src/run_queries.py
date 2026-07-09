"""Run the .sql case-study files against the built database and return each
statement's result as a DataFrame, labelled by its leading comment line.

Usage: python -m src.run_queries
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd

from src.build_db import DB_PATH

SQL_DIR = Path(__file__).resolve().parents[1] / "sql"


def split_statements(sql_text: str) -> list[tuple[str, str]]:
    """Split a .sql file into (label, statement) pairs. The label is the
    first '-- ' comment line immediately preceding a statement."""
    statements = []
    label = None
    buffer: list[str] = []

    def flush():
        stmt = "\n".join(buffer).strip()
        if stmt:
            statements.append((label or "Untitled query", stmt))

    for line in sql_text.splitlines():
        stripped = line.strip()
        if not stripped and not buffer:
            continue
        is_new_label = stripped.startswith("--") and not buffer and label is None
        if stripped.startswith("-- Q") or is_new_label:
            if buffer:
                flush()
                buffer = []
            label = stripped.lstrip("- ").strip()
            continue
        if stripped.startswith("--"):
            continue
        buffer.append(line)
        if stripped.endswith(";"):
            flush()
            buffer = []
            label = None
    if buffer:
        flush()
    return statements


def run_sql_file(conn: sqlite3.Connection, path: Path) -> list[tuple[str, pd.DataFrame]]:
    results = []
    for label, stmt in split_statements(path.read_text()):
        df = pd.read_sql(stmt, conn)
        results.append((label, df))
    return results


def run_all(db_path: Path = DB_PATH) -> dict[str, list[tuple[str, pd.DataFrame]]]:
    conn = sqlite3.connect(db_path)
    try:
        results = {}
        for sql_file in sorted(SQL_DIR.glob("[0-9]*.sql")):
            if sql_file.name.startswith("00_"):
                continue  # schema, not a query file
            results[sql_file.stem] = run_sql_file(conn, sql_file)
        return results
    finally:
        conn.close()


if __name__ == "__main__":
    for file_stem, queries in run_all().items():
        print(f"\n=== {file_stem} ===")
        for label, df in queries:
            print(f"\n-- {label}")
            print(df.head(15).to_string(index=False))
