"""Correctness tests for the .sql case-study files, run against a small
temporary database built from a fixed seed."""

import sqlite3
from pathlib import Path

import pandas as pd
import pytest

from src.build_db import build_db
from src.run_queries import run_all, split_statements

SQL_DIR = Path(__file__).resolve().parents[1] / "sql"


@pytest.fixture(scope="module")
def db_path(tmp_path_factory):
    tmp_dir = tmp_path_factory.mktemp("db")
    return build_db(db_path=tmp_dir / "test.db", seed=7)


def test_split_statements_labels_every_query():
    for filename in ["01_funnel_conversion.sql", "02_cohort_retention.sql",
                     "03_ltv_and_recommendation.sql"]:
        statements = split_statements((SQL_DIR / filename).read_text())
        assert len(statements) > 0
        for label, _ in statements:
            assert label != "Untitled query"


def test_funnel_counts_are_monotonically_decreasing(db_path):
    conn = sqlite3.connect(db_path)
    stmt = split_statements((SQL_DIR / "01_funnel_conversion.sql").read_text())[0][1]
    df = pd.read_sql(stmt, conn)
    conn.close()
    row = df.iloc[0]
    assert row["signups"] >= row["activated"] >= row["subscribed"]


def test_funnel_by_channel_rates_in_valid_range(db_path):
    conn = sqlite3.connect(db_path)
    stmt = split_statements((SQL_DIR / "01_funnel_conversion.sql").read_text())[1][1]
    df = pd.read_sql(stmt, conn)
    conn.close()
    for col in ["activation_rate_pct", "subscribe_given_activated_pct", "overall_conversion_pct"]:
        assert (df[col] >= 0).all()
        assert (df[col] <= 100).all()
    assert (df["subscribed"] <= df["activated"]).all()
    assert (df["activated"] <= df["signups"]).all()


def test_cohort_retention_percentages_in_valid_range(db_path):
    conn = sqlite3.connect(db_path)
    stmt = split_statements((SQL_DIR / "02_cohort_retention.sql").read_text())[0][1]
    df = pd.read_sql(stmt, conn)
    conn.close()
    assert (df["retention_pct"] >= 0).all()
    assert (df["retention_pct"] <= 100).all()
    assert (df["retained"] <= df["cohort_size_observable"]).all()


def test_retention_is_non_increasing_within_a_cohort(db_path):
    """A subscription that has churned stays churned -- retention at
    month_offset+1 can never exceed retention at month_offset within the
    same cohort."""
    conn = sqlite3.connect(db_path)
    stmt = split_statements((SQL_DIR / "02_cohort_retention.sql").read_text())[0][1]
    df = pd.read_sql(stmt, conn)
    conn.close()
    for _, group in df.groupby("cohort_month"):
        group = group.sort_values("month_offset")
        assert (group["retention_pct"].diff().dropna() <= 1e-9).all()


def test_ltv_to_cac_ratio_positive_and_referral_beats_paid_ads(db_path):
    conn = sqlite3.connect(db_path)
    stmt = split_statements((SQL_DIR / "03_ltv_and_recommendation.sql").read_text())[0][1]
    df = pd.read_sql(stmt, conn)
    conn.close()
    assert (df["ltv_to_cac_ratio"] > 0).all()
    ratios = df.set_index("acquisition_channel")["ltv_to_cac_ratio"]
    assert ratios["Referral"] > ratios["Paid Ads"]


def test_run_all_executes_every_query_file(db_path):
    results = run_all(db_path=db_path)
    assert set(results.keys()) == {
        "01_funnel_conversion", "02_cohort_retention", "03_ltv_and_recommendation",
    }
    for queries in results.values():
        assert len(queries) > 0
        for _, df in queries:
            assert not df.empty
