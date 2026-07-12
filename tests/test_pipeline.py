"""Smoke + regression tests for the analytics pipeline.

Builds an in-memory DuckDB from the committed CSVs (no files are touched),
runs every analytical module and asserts the things that once went wrong
stay fixed. Run with:  pytest -q
"""

from pathlib import Path

import duckdb
import pytest

BASE = Path(__file__).parent.parent
TABLES = ["ports", "shipping_routes", "customers",
          "shipments", "shipment_events", "invoices", "fx_rates"]


@pytest.fixture(scope="session")
def con():
    con = duckdb.connect(":memory:")
    con.execute((BASE / "schema" / "01_schema.sql").read_text())
    for t in TABLES:
        con.execute(
            f"INSERT INTO {t} SELECT * FROM "
            f"read_csv_auto('{BASE / 'data' / (t + '.csv')}', header=true)")
    real = BASE / "data" / "real"
    if (real / "port_activity_daily.csv").exists():
        con.execute(
            f"INSERT OR REPLACE INTO port_activity_daily SELECT * FROM "
            f"read_csv_auto('{real / 'port_activity_daily.csv'}', header=true)")
    if (real / "chokepoint_transits_daily.csv").exists():
        con.execute(
            f"INSERT OR REPLACE INTO chokepoint_transits_daily "
            f"SELECT transit_date, chokepoint_code, n_container, n_cargo, "
            f"       n_total, capacity_container FROM "
            f"read_csv_auto('{real / 'chokepoint_transits_daily.csv'}', header=true)")
    door = BASE / "door_to_door"
    if door.exists():
        con.execute((door / "schema.sql").read_text())
        con.execute(
            f"INSERT INTO inland_legs SELECT * FROM "
            f"read_csv_auto('{door / 'inland_legs.csv'}', header=true)")
    return con


def module_files():
    files = sorted((BASE / "analytics").glob("*.sql"))
    door = BASE / "door_to_door"
    if door.exists():
        files += sorted(door.glob("[0-9]*.sql"))
    return files


@pytest.mark.parametrize("sql_file", module_files(), ids=lambda f: f.stem)
def test_module_runs_and_returns_rows(con, sql_file):
    """Every analytical module must execute and produce at least one row."""
    rows = con.execute(sql_file.read_text()).fetchall()
    assert len(rows) > 0, f"{sql_file.name} returned no rows"


def test_quality_suite_has_no_critical_violations(con):
    df = con.execute(
        (BASE / "analytics" / "10_data_quality.sql").read_text()).fetchdf()
    bad = df[(df["severity"] == "critical") & (df["violations"] > 0)]
    assert bad.empty, f"critical data-quality violations:\n{bad}"


def test_structuring_screen_catches_the_whole_cluster(con):
    """Regression: a trailing-only window once flagged just 2 of the 4
    injected structuring invoices (the first members of a cluster saw
    partial counts). Every invoice of the injected cluster must alert."""
    df = con.execute(
        (BASE / "analytics" / "09_aml_screening.sql").read_text()).fetchdf()
    alerts = set(df[df["screen"].str.contains("STRUCTURING")]["invoice_id"])
    injected = {f"INV-2025-9000{k}" for k in range(4)}
    assert injected <= alerts, f"missed structuring invoices: {injected - alerts}"


def test_duplicate_screen_catches_injected_duplicates(con):
    df = con.execute(
        (BASE / "analytics" / "09_aml_screening.sql").read_text()).fetchdf()
    dupes = set(df[df["screen"].str.contains("DUPLICATE")]["invoice_id"])
    injected = {f"INV-2025-9500{k}" for k in range(3)}
    assert injected <= dupes, f"missed duplicate invoices: {injected - dupes}"


def test_report_and_dashboard_agree_on_receivables(con):
    """The aging waterfall (module 07) and the dashboard KPI must be built
    on the same as-of anchor — totals may differ by only rounding."""
    report_total = con.execute("""
        WITH as_of AS (SELECT MAX(issue_date) AS today FROM invoices)
        SELECT SUM(i.amount * fx.rate_to_usd)
        FROM invoices i
        ASOF JOIN fx_rates fx
            ON fx.currency = i.currency AND i.issue_date >= fx.rate_date
        WHERE i.paid_date IS NULL""").fetchone()[0]
    module_total = con.execute(
        (BASE / "analytics" / "07_receivables_aging.sql").read_text()
    ).fetchdf()["outstanding_usd"].sum()
    assert abs(float(report_total) - float(module_total)) < 5, \
        "module 07 and the dashboard disagree on outstanding receivables"
