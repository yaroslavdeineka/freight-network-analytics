#!/usr/bin/env python3
"""Fetch REAL, fresh data for the freight analytics pipeline.

Sources (all free, no API keys):
  * IMF PortWatch (portwatch.imf.org) — daily port activity for ~2,000 ports,
    derived from satellite AIS signals; updated weekly by the IMF.
  * IMF PortWatch chokepoints — daily vessel transits through Suez, Bosporus,
    Bab el-Mandeb, Malacca, Hormuz, Gibraltar, Dover, Oresund.
  * ECB reference rates via frankfurter.dev — daily FX fixings (EUR, GBP, CNY).
  * National Bank of Ukraine open API — daily UAH fixing.

Writes CSV caches to data/real/.  Run this script whenever you want fresh
data, then re-run run_pipeline.py — the pipeline works offline from the cache.
Each source fails independently: a dead API costs its own dataset only.

Usage:  python3 fetch_real_data.py
"""

import csv
import json
import time
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

BASE = Path(__file__).parent
REAL_DIR = BASE / "data" / "real"
START = "2024-07-01"                      # matches the synthetic 2-year window
TODAY = date.today().isoformat()

PORTWATCH_URL = ("https://services9.arcgis.com/weJ1QsnbMYJlCHdG/arcgis/rest/"
                 "services/Daily_Ports_Data/FeatureServer/0/query")
CHOKEPOINT_URL = ("https://services9.arcgis.com/weJ1QsnbMYJlCHdG/arcgis/rest/"
                  "services/Daily_Chokepoints_Data/FeatureServer/0/query")
FRANKFURTER_URL = "https://api.frankfurter.dev/v1"
NBU_URL = "https://bank.gov.ua/NBU_Exchange/exchange_site"

# UN/LOCODE -> IMF PortWatch port id (mapping verified against
# PortWatch_ports_database, July 2026)
PORT_MAP = {
    "UAODS": "port843",   # Odesa
    "PLGDN": "port380",   # Gdansk
    "DEHAM": "port446",   # Hamburg
    "NLRTM": "port1114",  # Rotterdam
    "GBFXT": "port343",   # Felixstowe
    "TRMER": "port735",   # Mersin
    "EGALY": "port23",    # Alexandria
    "AEJEA": "port744",   # Jebel Ali
    "INNSA": "port776",   # Mumbai-Jawaharlal Nehru (Nhava Sheva)
    "SGSIN": "port1201",  # Singapore
    "CNSHA": "port1188",  # Shanghai
    "CNSZX": "port1414",  # Yantian — Shenzhen's main container terminal
    "KRPUS": "port1065",  # Busan
    "USNYC": "port815",   # New York
    "USLGB": "port664",   # Los Angeles-Long Beach (combined in PortWatch)
    "BRSSZ": "port1160",  # Santos
}

# Chokepoint code -> IMF PortWatch id (verified against the
# Daily_Chokepoints_Data layer, July 2026). Must match schema/01_schema.sql.
CHOKEPOINT_MAP = {
    "SUEZ":   "chokepoint1",    # Suez Canal
    "BOSPOR": "chokepoint3",    # Bosporus Strait
    "BABMND": "chokepoint4",    # Bab el-Mandeb Strait
    "MALACC": "chokepoint5",    # Malacca Strait
    "HORMUZ": "chokepoint6",    # Strait of Hormuz
    "GIBRAL": "chokepoint8",    # Gibraltar Strait
    "DOVER":  "chokepoint9",    # Dover Strait
    "ORESUN": "chokepoint10",   # Oresund Strait
}


def get_json(url, params=None, raw_suffix="", retries=3):
    if params:
        url += "?" + urllib.parse.urlencode(params) + raw_suffix
    req = urllib.request.Request(
        url, headers={"User-Agent": "freight-sql-portfolio/1.0"})
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=90) as resp:
                return json.load(resp)
        except Exception:                               # noqa: BLE001
            if attempt == retries - 1:
                raise
            time.sleep(5 * (attempt + 1))               # 5s, 10s backoff


def year_chunks(start, end):
    """Split [start, end] into calendar-year chunks (kind to both APIs)."""
    s = date.fromisoformat(start)
    e = date.fromisoformat(end)
    while s <= e:
        chunk_end = min(date(s.year, 12, 31), e)
        yield s.isoformat(), chunk_end.isoformat()
        s = date(s.year + 1, 1, 1)


def esri_date(value):
    """PortWatch returns DateOnly as 'YYYY-MM-DD'; be defensive about epoch ms."""
    if isinstance(value, (int, float)):
        return date.fromtimestamp(value / 1000).isoformat()
    return str(value)[:10]


def fetch_portwatch():
    print(f"IMF PortWatch daily activity, {START} → {TODAY}")
    rows = []
    for code, pid in PORT_MAP.items():
        n_port, offset = 0, 0
        while True:
            data = get_json(PORTWATCH_URL, {
                "where": f"portid='{pid}' AND date>=DATE'{START}'",
                "outFields": ("date,portid,portname,portcalls_container,"
                              "portcalls,import_container,import,"
                              "export_container,export"),
                "orderByFields": "date",
                "resultOffset": offset,
                "resultRecordCount": 1000,
                "f": "json",
            })
            if "error" in data:
                raise RuntimeError(f"PortWatch error for {pid}: {data['error']}")
            feats = data.get("features", [])
            for f in feats:
                a = f["attributes"]
                rows.append([
                    esri_date(a["date"]), code, pid, a.get("portname", ""),
                    a.get("portcalls_container"), a.get("portcalls"),
                    a.get("import_container"), a.get("import"),
                    a.get("export_container"), a.get("export"),
                ])
            n_port += len(feats)
            if len(feats) < 1000:
                break
            offset += 1000
        print(f"  {code} ({pid:<9}) {n_port:>5,} days")

    rows.sort(key=lambda r: (r[0], r[1]))
    out = REAL_DIR / "port_activity_daily.csv"
    with out.open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["activity_date", "port_code", "portwatch_id",
                    "portwatch_name", "portcalls_container", "portcalls_total",
                    "import_container_tons", "import_total_tons",
                    "export_container_tons", "export_total_tons"])
        w.writerows(rows)
    print(f"  wrote {out.relative_to(BASE)} ({len(rows):,} rows)\n")


def fetch_chokepoints():
    print(f"IMF PortWatch chokepoint transits, {START} → {TODAY}")
    rows = []
    for code, pid in CHOKEPOINT_MAP.items():
        n_ck, offset = 0, 0
        while True:
            data = get_json(CHOKEPOINT_URL, {
                "where": f"portid='{pid}' AND date>=DATE'{START}'",
                "outFields": ("date,portid,portname,n_container,"
                              "n_cargo,n_total,capacity_container"),
                "orderByFields": "date",
                "resultOffset": offset,
                "resultRecordCount": 1000,
                "f": "json",
            })
            if "error" in data:
                raise RuntimeError(f"Chokepoint error for {pid}: {data['error']}")
            feats = data.get("features", [])
            for f in feats:
                a = f["attributes"]
                rows.append([
                    esri_date(a["date"]), code, pid, a.get("portname", ""),
                    a.get("n_container"), a.get("n_cargo"),
                    a.get("n_total"), a.get("capacity_container"),
                ])
            n_ck += len(feats)
            if len(feats) < 1000:
                break
            offset += 1000
        print(f"  {code} ({pid:<12}) {n_ck:>5,} days")

    rows.sort(key=lambda r: (r[0], r[1]))
    out = REAL_DIR / "chokepoint_transits_daily.csv"
    with out.open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["transit_date", "chokepoint_code", "portwatch_id",
                    "portwatch_name", "n_container", "n_cargo", "n_total",
                    "capacity_container"])
        w.writerows(rows)
    print(f"  wrote {out.relative_to(BASE)} ({len(rows):,} rows)\n")


def fetch_fx():
    print(f"Real FX fixings, {START} → {TODAY}")
    fixings = {}   # (date, currency) -> rate; dict deduplicates chunk overlaps

    # EUR / GBP / CNY — ECB reference rates via frankfurter.dev
    try:
        for a, b in year_chunks(START, TODAY):
            data = get_json(f"{FRANKFURTER_URL}/{a}..{b}",
                            {"from": "USD", "to": "EUR,GBP,CNY"})
            for d, fixes in data.get("rates", {}).items():
                if d < START:      # frankfurter may echo the prior business day
                    continue
                for cur, units_per_usd in fixes.items():
                    # store as USD per 1 unit of currency (matches fx_rates schema)
                    fixings[(d, cur)] = round(1.0 / units_per_usd, 6)
        print(f"  ECB (frankfurter.dev): EUR/GBP/CNY, {len(fixings):,} fixings")
    except Exception as exc:                            # noqa: BLE001
        print(f"  WARNING: ECB fetch failed ({exc}) — "
              f"pipeline will keep synthetic EUR/GBP/CNY rates")

    # UAH — National Bank of Ukraine
    try:
        n_uah = 0
        for a, b in year_chunks(START, TODAY):
            data = get_json(NBU_URL, {
                "start": a.replace("-", ""), "end": b.replace("-", ""),
                "valcode": "usd", "sort": "exchangedate", "order": "asc",
            }, raw_suffix="&json")
            for rec in data:
                d = "-".join(reversed(rec["exchangedate"].split(".")))
                if d < START:
                    continue
                uah_per_usd = rec.get("rate_per_unit") or rec["rate"]
                fixings[(d, "UAH")] = round(1.0 / uah_per_usd, 6)
                n_uah += 1
        print(f"  NBU (bank.gov.ua): UAH, {n_uah:,} fixings")
    except Exception as exc:                            # noqa: BLE001
        print(f"  WARNING: NBU UAH fetch failed ({exc}) — "
              f"pipeline will keep synthetic UAH rates")

    rows = sorted([d, c, v] for (d, c), v in fixings.items())
    out = REAL_DIR / "fx_rates_real.csv"
    with out.open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["rate_date", "currency", "rate_to_usd"])
        w.writerows(rows)
    print(f"  wrote {out.relative_to(BASE)} ({len(rows):,} rows)\n")


def main():
    REAL_DIR.mkdir(parents=True, exist_ok=True)
    failures = []
    for fetch in (fetch_portwatch, fetch_chokepoints, fetch_fx):
        try:
            fetch()
        except Exception as exc:                        # noqa: BLE001
            failures.append(fetch.__name__)
            print(f"  WARNING: {fetch.__name__} failed ({exc}) — "
                  f"pipeline will use the previous cache for this dataset\n")
    if failures:
        print(f"Done with warnings ({', '.join(failures)} failed). "
              f"Now run:  python3 run_pipeline.py")
    else:
        print("Done. Now run:  python3 run_pipeline.py")


if __name__ == "__main__":
    main()
