import re
import sys
from pathlib import Path

import duckdb

BASE = Path(__file__).parent
DB_PATH = BASE / "freight.duckdb"
TABLES = ["ports", "shipping_routes", "customers",
          "shipments", "shipment_events", "invoices", "fx_rates"]


def build_database(con):
    schema_sql = (BASE / "schema" / "01_schema.sql").read_text()
    con.execute(schema_sql)
    for t in TABLES:
        con.execute(
            f"INSERT INTO {t} SELECT * FROM read_csv_auto('{BASE / 'data' / (t + '.csv')}', header=true)"
        )
        n = con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        print(f"  loaded {t:<18} {n:>7,} rows")


def load_real_data(con):
    """Load cached REAL data (refreshed by fetch_real_data.py) if present."""
    real = BASE / "data" / "real"

    pa = real / "port_activity_daily.csv"
    if pa.exists():
        con.execute(
            f"INSERT OR REPLACE INTO port_activity_daily "
            f"SELECT * FROM read_csv_auto('{pa}', header=true)"
        )
        n, dmax = con.execute(
            "SELECT COUNT(*), MAX(activity_date) FROM port_activity_daily"
        ).fetchone()
        print(f"  loaded port_activity   {n:>7,} rows  (REAL, IMF PortWatch, through {dmax})")
    else:
        print("  port_activity_daily: no cache — run fetch_real_data.py for live IMF PortWatch data")

    ck = real / "chokepoint_transits_daily.csv"
    if ck.exists():
        con.execute(
            f"INSERT OR REPLACE INTO chokepoint_transits_daily "
            f"SELECT transit_date, chokepoint_code, n_container, n_cargo, "
            f"       n_total, capacity_container "
            f"FROM read_csv_auto('{ck}', header=true)"
        )
        n, dmax = con.execute(
            "SELECT COUNT(*), MAX(transit_date) FROM chokepoint_transits_daily"
        ).fetchone()
        print(f"  loaded chokepoints     {n:>7,} rows  (REAL, IMF PortWatch, through {dmax})")
    else:
        print("  chokepoint_transits_daily: no cache — run fetch_real_data.py "
              "for live strait-transit data")

    fx = real / "fx_rates_real.csv"
    if fx.exists():
        con.execute(
            f"CREATE TEMP TABLE fx_real AS "
            f"SELECT * FROM read_csv_auto('{fx}', header=true)"
        )
        con.execute(
            "DELETE FROM fx_rates WHERE currency IN (SELECT DISTINCT currency FROM fx_real) "
            "AND rate_date >= (SELECT MIN(rate_date) FROM fx_real)"
        )
        con.execute(
            "INSERT OR REPLACE INTO fx_rates "
            "SELECT rate_date, currency, rate_to_usd FROM fx_real"
        )
        n, d0, d1, curs = con.execute(
            "SELECT COUNT(*), MIN(rate_date), MAX(rate_date), "
            "STRING_AGG(DISTINCT currency, ', ' ORDER BY currency) FROM fx_real"
        ).fetchone()
        print(f"  loaded fx_rates        {n:>7,} rows  (REAL: {curs}, {d0} → {d1})")
        if str(d0) > "2024-07-01":
            print(f"  NOTE: real FX cache starts {d0}; earlier dates still use "
                  f"synthetic rates — run fetch_real_data.py for full history")
    else:
        print("  fx_rates: using synthetic rates — run fetch_real_data.py for real ECB/NBU fixings")


# ── OPTIONAL EXTENSION: door-to-door routing ────────────────────────────────
# Everything lives in door_to_door/ (schema.sql, inland_legs.csv, 14_*.sql).
# Delete or rename that folder to switch the feature off — nothing below
# breaks without it.
DOOR_DIR = BASE / "door_to_door"


def load_door_to_door(con):
    if not DOOR_DIR.exists():
        return
    con.execute((DOOR_DIR / "schema.sql").read_text())
    con.execute(
        f"INSERT INTO inland_legs "
        f"SELECT * FROM read_csv_auto('{DOOR_DIR / 'inland_legs.csv'}', header=true)"
    )
    legs, reqs = con.execute(
        "SELECT (SELECT COUNT(*) FROM inland_legs), (SELECT COUNT(*) FROM route_requests)"
    ).fetchone()
    print(f"  loaded door_to_door    {legs:>7,} inland legs, {reqs} route requests  (optional extension)")
# ── end of optional extension ───────────────────────────────────────────────


# ── OPTIONAL EXTENSION: visual dashboard ────────────────────────────────────
# Lives in dashboard/ (build_dashboard.py). Delete or rename the folder to
# switch it off — nothing below breaks without it.
DASH_DIR = BASE / "dashboard"


def build_dashboard():
    script = DASH_DIR / "build_dashboard.py"
    if not script.exists():
        return
    import subprocess, sys
    r = subprocess.run([sys.executable, str(script)],
                       capture_output=True, text=True)
    print(r.stdout.strip() if r.returncode == 0 else
          f"  dashboard build failed (non-fatal):\n{r.stderr.strip()}")
# ── end of optional extension ───────────────────────────────────────────────


def title_from(sql_text, fallback):
    m = re.search(r"^--\s*(\d+[a-z]?\s*·.*)$", sql_text, re.MULTILINE)
    return m.group(1).strip() if m else fallback


def quality_gate(df):
    """Fail the pipeline on critical data-quality violations (module 10)."""
    bad = df[(df["severity"] == "critical") & (df["violations"] > 0)]
    if len(bad):
        print("\n  ✗ QUALITY GATE FAILED — critical violations:")
        for _, r in bad.iterrows():
            print(f"      {r['check_name']}: {r['violations']}")
    return len(bad) == 0


def run_analytics(con):
    from datetime import datetime
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    fresh = con.execute(
        "SELECT MAX(activity_date) FROM port_activity_daily").fetchone()[0]
    fresh = f"real data through **{fresh}**" if fresh else \
        "no real-data cache — run `fetch_real_data.py`"
    report = ["# Freight Network Analytics — Query Results\n",
              f"*Generated {stamp} · {fresh}*\n"]
    # legend: port codes → names, so tables read easily for non-specialists
    report.append("<details><summary><b>Port codes used in this report</b></summary>\n")
    report.append("| Code | Port | Country |\n|---|---|---|")
    for c, n, co in con.execute(
            "SELECT port_code, port_name, country FROM ports ORDER BY port_name").fetchall():
        report.append(f"| `{c}` | {n} | {co} |")
    report.append("\n</details>\n")
    files = sorted((BASE / "analytics").glob("*.sql"))
    if DOOR_DIR.exists():                      # optional extension (see above)
        files += sorted(DOOR_DIR.glob("[0-9]*.sql"))
    quality_ok = True
    for f in files:
        sql = f.read_text()
        title = title_from(sql, f.stem)
        print(f"\n{'=' * 74}\n {title}\n{'=' * 74}")
        df = con.execute(sql).fetchdf()
        # plain objects + None: tabulate/pandas then render every missing
        # value as '—' instead of a mix of nan / <NA> / None
        df = df.astype(object).where(df.notna(), None)
        print(df.to_string(index=False, max_rows=40, na_rep="—"))
        if "data_quality" in f.stem:
            quality_ok = quality_gate(df)
        report.append(f"\n## {title}\n")
        report.append(f"*Source: `{f.parent.name}/{f.name}`*\n")
        report.append(df.to_markdown(index=False, intfmt=",", missingval="—"))
        report.append("")

    out = BASE / "outputs"
    out.mkdir(exist_ok=True)
    (out / "analytics_report.md").write_text("\n".join(report))
    print(f"\nReport written to outputs/analytics_report.md")
    return quality_ok


def main():
    if DB_PATH.exists():
        DB_PATH.unlink()
    con = duckdb.connect(str(DB_PATH))
    print("Building database…")
    build_database(con)
    load_real_data(con)
    load_door_to_door(con)
    quality_ok = run_analytics(con)
    con.close()
    build_dashboard()
    if not quality_ok:
        # artifacts are still written for debugging, but the run is a failure —
        # this is what gates the weekly CI refresh on bad data
        sys.exit(1)


if __name__ == "__main__":
    main()
