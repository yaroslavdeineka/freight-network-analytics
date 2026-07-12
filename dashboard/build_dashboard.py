import json
import re
from datetime import datetime
from pathlib import Path

import duckdb

BASE = Path(__file__).parent.parent
DB = BASE / "freight.duckdb"
OUT = BASE / "outputs" / "dashboard.html"


# ─── data extraction ─────────────────────────────────────────────────────────

def q(con, sql, one=False):
    cur = con.execute(sql)
    return cur.fetchone() if one else cur.fetchall()


def collect(con):
    d = {"generated": datetime.now().strftime("%Y-%m-%d %H:%M")}

    fresh = q(con, "SELECT MAX(activity_date) FROM port_activity_daily", one=True)[0]
    d["fresh"] = str(fresh) if fresh else None

    names = dict(q(con, "SELECT port_code, port_name FROM ports"))

    d["kpi"] = dict(zip(
        ["shipments", "customers", "on_time_pct", "avg_transit"],
        q(con, """
            SELECT COUNT(*),
                   -- active = shipped in the last 180 days of the data
                   COUNT(DISTINCT customer_id) FILTER (
                       WHERE booked_date > (SELECT MAX(booked_date) FROM shipments) - 180),
                   ROUND(100.0 * AVG(CASE WHEN ata IS NOT NULL THEN
                       CASE WHEN ata <= eta + INTERVAL 2 DAY THEN 1 ELSE 0 END END), 1),
                   ROUND(AVG(CASE WHEN ata IS NOT NULL
                       THEN date_diff('day', atd, ata) END), 1)
            FROM shipments""", one=True)))
    d["kpi"]["revenue_usd"], = q(con, """
        SELECT ROUND(SUM(i.amount * fx.rate_to_usd), 0)
        FROM invoices i ASOF JOIN fx_rates fx
          ON fx.currency = i.currency AND i.issue_date >= fx.rate_date""", one=True)
    # as-of anchor = newest invoice date IN THE DATA (same as module 07),
    # so the dashboard and the markdown report always show identical aging
    d["kpi"]["outstanding_usd"], d["kpi"]["overdue90_usd"] = q(con, """
        WITH as_of AS (SELECT MAX(issue_date) AS today FROM invoices)
        SELECT ROUND(SUM(i.amount * fx.rate_to_usd), 0),
               ROUND(SUM(CASE WHEN i.due_date < a.today - 90
                              THEN i.amount * fx.rate_to_usd END), 0)
        FROM invoices i ASOF JOIN fx_rates fx
          ON fx.currency = i.currency AND i.issue_date >= fx.rate_date
        CROSS JOIN as_of a
        WHERE i.paid_date IS NULL""", one=True)

    d["monthly"] = [
        {"m": r[0], "shipments": r[1]}
        for r in q(con, """
            SELECT strftime(date_trunc('month', booked_date), '%Y-%m'), COUNT(*)
            FROM shipments GROUP BY 1 ORDER BY 1""")]

    d["regions"] = [
        {"region": r[0], "usd": float(r[1])}
        for r in q(con, """
            SELECT p.region, ROUND(SUM(i.amount * fx.rate_to_usd), 0)
            FROM invoices i
            ASOF JOIN fx_rates fx
              ON fx.currency = i.currency AND i.issue_date >= fx.rate_date
            JOIN shipments s ON s.shipment_id = i.shipment_id
            JOIN ports p ON p.port_code = s.origin_port
            GROUP BY 1 ORDER BY 2 DESC""")]

    d["ports"] = [
        {"code": r[0], "name": r[1], "country": r[2], "region": r[3],
         "cbm180": float(r[4] or 0), "kt_day": r[5], "yoy": r[6]}
        for r in q(con, """
            WITH anchor AS (SELECT MAX(activity_date) AS d_max FROM port_activity_daily),
            book AS (
                SELECT port_code, SUM(cbm) AS cbm FROM (
                    SELECT origin_port AS port_code, SUM(volume_cbm) AS cbm FROM shipments
                    WHERE booked_date > (SELECT MAX(booked_date) FROM shipments) - 180 GROUP BY 1
                    UNION ALL
                    SELECT dest_port, SUM(volume_cbm) FROM shipments
                    WHERE booked_date > (SELECT MAX(booked_date) FROM shipments) - 180 GROUP BY 1
                ) GROUP BY 1),
            act AS (
                SELECT pa.port_code,
                    ROUND(SUM(pa.import_total_tons + pa.export_total_tons)
                        FILTER (WHERE pa.activity_date > a.d_max - 90) / 90.0 / 1000, 1) AS kt_day,
                    ROUND(100.0 * (
                        SUM(pa.import_total_tons + pa.export_total_tons)
                            FILTER (WHERE pa.activity_date > a.d_max - 90)
                      - SUM(pa.import_total_tons + pa.export_total_tons)
                            FILTER (WHERE pa.activity_date > a.d_max - 455
                                      AND pa.activity_date <= a.d_max - 365))
                      / NULLIF(SUM(pa.import_total_tons + pa.export_total_tons)
                            FILTER (WHERE pa.activity_date > a.d_max - 455
                                      AND pa.activity_date <= a.d_max - 365), 0), 1) AS yoy
                FROM port_activity_daily pa CROSS JOIN anchor a GROUP BY 1)
            SELECT p.port_code, p.port_name, p.country, p.region,
                   b.cbm, a.kt_day, a.yoy
            FROM ports p LEFT JOIN book b USING (port_code)
            LEFT JOIN act a USING (port_code)
            ORDER BY a.kt_day DESC NULLS LAST""")]

    d["spark"] = {}
    for code, wk, tons in q(con, """
        WITH anchor AS (SELECT MAX(activity_date) AS d_max FROM port_activity_daily)
        SELECT pa.port_code, date_trunc('week', pa.activity_date) AS wk,
               SUM(pa.import_total_tons + pa.export_total_tons)
        FROM port_activity_daily pa CROSS JOIN anchor a
        WHERE pa.activity_date > a.d_max - 182
        GROUP BY 1, 2 ORDER BY 1, 2"""):
        d["spark"].setdefault(code, []).append(float(tons or 0))

    d["aging"] = [
        {"bucket": r[0], "usd": float(r[1])}
        for r in q(con, """
            WITH as_of AS (SELECT MAX(issue_date) AS today FROM invoices)
            SELECT CASE
                WHEN i.due_date >= a.today THEN 'Not yet due'
                WHEN i.due_date >= a.today - 30 THEN '1–30 days'
                WHEN i.due_date >= a.today - 60 THEN '31–60 days'
                WHEN i.due_date >= a.today - 90 THEN '61–90 days'
                ELSE '90+ days' END AS bucket,
                ROUND(SUM(i.amount * fx.rate_to_usd), 0)
            FROM invoices i ASOF JOIN fx_rates fx
              ON fx.currency = i.currency AND i.issue_date >= fx.rate_date
            CROSS JOIN as_of a
            WHERE i.paid_date IS NULL
            GROUP BY 1
            ORDER BY CASE bucket WHEN 'Not yet due' THEN 0 WHEN '1–30 days' THEN 1
                WHEN '31–60 days' THEN 2 WHEN '61–90 days' THEN 3 ELSE 4 END""")]

    # chokepoint exposure (module 13's logic, compact form for the overview)
    d["choke"] = [
        {"name": r[0], "share": float(r[1]), "yoy": r[2]}
        for r in q(con, """
            WITH anchor AS (SELECT MAX(transit_date) AS d_max
                            FROM chokepoint_transits_daily),
            book AS (
                SELECT s.origin_port, s.dest_port,
                       SUM(s.volume_cbm) AS cbm
                FROM shipments s
                WHERE s.booked_date > (SELECT MAX(booked_date) FROM shipments) - 180
                GROUP BY 1, 2),
            total AS (SELECT SUM(cbm) AS cbm_total FROM book),
            exposure AS (
                SELECT lc.chokepoint_code, SUM(b.cbm) AS cbm
                FROM book b
                JOIN lane_chokepoints lc USING (origin_port, dest_port)
                GROUP BY 1),
            trend AS (
                SELECT t.chokepoint_code,
                       SUM(t.n_container) FILTER (
                           WHERE t.transit_date > a.d_max - 90)  AS cur,
                       SUM(t.n_container) FILTER (
                           WHERE t.transit_date >  a.d_max - 455
                             AND t.transit_date <= a.d_max - 365) AS prev
                FROM chokepoint_transits_daily t CROSS JOIN anchor a
                GROUP BY 1)
            SELECT c.chokepoint_name,
                   ROUND(100.0 * e.cbm / tt.cbm_total, 1),
                   ROUND(100.0 * (t.cur - t.prev) / NULLIF(t.prev, 0), 1)
            FROM exposure e
            JOIN chokepoints c USING (chokepoint_code)
            LEFT JOIN trend t  USING (chokepoint_code)
            CROSS JOIN total tt
            ORDER BY e.cbm DESC""")]

    # door-to-door routes for the overview block (human port names)
    d["routes13"] = []
    sql13 = BASE / "door_to_door" / "14_door_to_door_routing.sql"
    try:
        if sql13.exists():
            def humanise(s):
                for code, nm in names.items():
                    s = s.replace(code, nm)
                return s
            d["routes13"] = [
                {"request": humanise(str(r[0])), "rank": r[1],
                 "route": humanise(str(r[2])), "mode": r[4],
                 "days": r[5], "usd": float(r[6])}
                for r in con.execute(sql13.read_text()).fetchall()]
    except Exception as exc:                            # noqa: BLE001
        print(f"  WARNING: door-to-door block skipped ({exc})")

    d["aml"] = []
    sql09 = BASE / "analytics" / "09_aml_screening.sql"
    try:
        if sql09.exists():
            # module 09 columns: screen, customer_name, invoice_id,
            # issue_date, currency, amount, evidence_count, evidence_usd
            d["aml"] = [
                {"screen": str(r[0]), "customer": str(r[1]),
                 "invoice": str(r[2]), "amount": float(r[5])}
                for r in con.execute(sql09.read_text()).fetchall()]
    except Exception as exc:                            # noqa: BLE001
        print(f"  WARNING: AML block skipped ({exc})")

    # top-10 busiest lanes (for the overview chart)
    d["lanes"] = [
        {"l": f"{names.get(r[0], r[0])} → {names.get(r[1], r[1])}", "n": r[2]}
        for r in q(con, """
            SELECT origin_port, dest_port, COUNT(*) AS n
            FROM shipments GROUP BY 1, 2 ORDER BY n DESC LIMIT 10""")]

    # monthly on-time % (for the overview chart)
    d["ontime"] = [
        {"m": r[0], "pct": float(r[1])}
        for r in q(con, """
            SELECT strftime(date_trunc('month', booked_date), '%Y-%m'),
                   ROUND(100.0 * AVG(CASE WHEN ata IS NOT NULL THEN
                       CASE WHEN ata <= eta + INTERVAL 2 DAY THEN 1 ELSE 0 END END), 1)
            FROM shipments GROUP BY 1 ORDER BY 1""")]

    # ── ALL module result tables, verbatim ──
    d["modules"] = []
    files = sorted((BASE / "analytics").glob("*.sql"))
    dd = BASE / "door_to_door"
    if dd.exists():
        files += sorted(dd.glob("[0-9]*.sql"))
    for fp in files:
        sql = fp.read_text()
        m = re.search(r"^--\s*(\d+[a-z]?)\s*·\s*(.*?)\s*$", sql, re.M)
        num = m.group(1) if m else fp.stem[:2]
        title = m.group(2) if m else fp.stem

        def cell(v):
            if v is None:
                return ""
            if isinstance(v, float):
                return f"{v:,.2f}".rstrip("0").rstrip(".")
            if isinstance(v, int):
                return f"{v:,}"
            s = str(v)
            if any(c in s for c in names):          # 'CNSHA → NLRTM' → names
                for code, nm in names.items():
                    s = s.replace(code, nm)
            return s
        try:
            cur = con.execute(sql)
            cols = [c[0] for c in cur.description]
            rows = [[cell(v) for v in r] for r in cur.fetchall()[:200]]
        except Exception as exc:                        # noqa: BLE001
            cols, rows = ["error"], [[str(exc)]]
        d["modules"].append({
            "num": num, "title": title, "cols": cols, "rows": rows,
            "src": f"{fp.parent.name}/{fp.name}"})

    # ── data-driven plain-language facts ──
    f = {}
    peak = max(d["monthly"], key=lambda r: r["shipments"])
    f["peakM"], f["peakN"] = peak["m"], peak["shipments"]
    tot = sum(r["usd"] for r in d["regions"]) or 1
    f["topRegion"] = d["regions"][0]["region"]
    f["topRegionPct"] = round(100 * d["regions"][0]["usd"] / tot)
    live = [p for p in d["ports"] if p["kt_day"] and p["yoy"] is not None]
    if live:
        up = max(live, key=lambda p: p["yoy"])
        dn = min(live, key=lambda p: p["yoy"])
        f["upPort"], f["upPct"] = up["name"], up["yoy"]
        f["dnPort"], f["dnPct"] = dn["name"], dn["yoy"]
    f["zeroPorts"] = [p["name"] for p in d["ports"] if p["kt_day"] == 0]
    if d["kpi"]["outstanding_usd"]:
        f["overduePct"] = round(100 * (d["kpi"]["overdue90_usd"] or 0)
                                / d["kpi"]["outstanding_usd"])
    d["facts"] = f
    return d


# ─── HTML template: full-width analytics workbench, zero dependencies ───────

TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Freight Network Analytics</title>
<style>
  :root {
    /* validated reference palette (dataviz skill): warm paper surfaces,
       one accent hue for series, reserved status colors for state */
    --page:#f9f9f7; --panel:#fcfcfb; --ink:#141413; --ink2:#52514e;
    --muted:#898781; --hair:#e7e6df; --grid:#e1e0d9; --track:#f0efec;
    --accent:#2a78d6; --accent-deep:#1c5cab; --accent-soft:#9ec5f4;
    --pos:#006300; --posbg:#e6f3e6; --neg:#d03b3b; --negbg:#fbeaea;
    --warn:#8a6100; --warnbg:#fdf3dc; --nabg:#f0efec;
    --topbar:#141413; --topink:#fcfcfb; --topmut:#a5a49c;
  }
  * { box-sizing:border-box; margin:0; }
  html { scroll-behavior:smooth; }
  body { background:var(--page); color:var(--ink);
         font:14px/1.5 -apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;
         -webkit-font-smoothing:antialiased; }

  .top { position:sticky; top:0; z-index:20; background:var(--topbar);
         color:var(--topink); display:flex; align-items:center;
         gap:16px; padding:11px 22px; }
  .top .name { font-weight:750; font-size:14.5px; white-space:nowrap;
               letter-spacing:-.01em; }
  .top .name::before { content:'⚓ '; font-size:13px; }
  .top .meta { color:var(--topmut); font-size:12px; flex:1;
               overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
  .langs { display:flex; gap:2px; }
  .langs a { color:var(--topmut); text-decoration:none; cursor:pointer;
             font-size:12px; font-weight:650; padding:3px 9px; border-radius:6px; }
  .langs a:hover { color:var(--topink); }
  .langs a.on { color:var(--topink); background:rgba(255,255,255,.14); }

  .shell { display:flex; align-items:flex-start; }
  nav { width:216px; flex-shrink:0; position:sticky; top:46px;
        max-height:calc(100vh - 46px); overflow-y:auto; padding:16px 10px 30px; }
  nav a { display:block; padding:4px 10px; border-radius:7px; color:var(--ink2);
          text-decoration:none; font-size:12px; line-height:1.45; margin-bottom:1px; }
  nav a:hover { background:#efeee9; color:var(--ink); }
  nav .nh { font-size:10.5px; letter-spacing:.09em; text-transform:uppercase;
            color:var(--muted); padding:14px 10px 5px; font-weight:650; }
  @media (max-width:940px){ nav { display:none; } }

  main { flex:1; min-width:0; padding:20px 22px 70px; }
  .row { display:grid; gap:16px; margin-bottom:16px; }
  .r2 { grid-template-columns:1.5fr 1fr; }
  .r3 { grid-template-columns:1fr 1fr; }
  @media (max-width:1100px){ .r2,.r3 { grid-template-columns:1fr; } }

  .panel { background:var(--panel); border:1px solid rgba(20,20,19,.08);
           border-radius:12px; padding:16px 18px; min-width:0;
           box-shadow:0 1px 2px rgba(20,20,19,.04); }
  .pt { font-size:13px; font-weight:700; margin-bottom:12px;
        letter-spacing:-.005em; }
  .pt small { color:var(--muted); font-weight:400; margin-left:6px; }

  .kpis { display:grid; grid-template-columns:repeat(auto-fit,minmax(150px,1fr));
          gap:0; padding:0; overflow:hidden; }
  .kpi { padding:14px 18px 13px; border-right:1px solid var(--hair);
         position:relative; }
  .kpi::before { content:''; position:absolute; left:18px; top:14px;
                 width:20px; height:3px; border-radius:2px; background:var(--accent);
                 opacity:.85; }
  .kpi:last-child { border-right:none; }
  .kpi .l { color:var(--muted); font-size:10.5px; font-weight:650;
            letter-spacing:.07em; text-transform:uppercase; margin-top:9px; }
  .kpi .v { font-size:25px; font-weight:750; letter-spacing:-.02em;
            margin-top:3px; }
  .kpi .n { color:var(--muted); font-size:11.5px; margin-top:2px; }

  .note { font-size:12.5px; color:var(--muted); margin-top:10px; }
  .note b { color:var(--ink); }

  table { width:100%; border-collapse:collapse; font-size:12.5px;
          font-variant-numeric:tabular-nums; }
  th { text-align:left; font-weight:650; color:var(--muted); font-size:10.5px;
       letter-spacing:.05em; text-transform:uppercase;
       padding:7px 8px; border-bottom:1px solid var(--grid); white-space:nowrap;
       position:sticky; top:0; background:var(--panel); }
  td { padding:5.5px 8px; border-bottom:1px solid var(--hair); white-space:nowrap; }
  tbody tr:last-child td { border-bottom:none; }
  tbody tr:hover td { background:#f4f3ee; }
  td.num, th.num { text-align:right; }
  .scroll { overflow:auto; max-height:430px; border:1px solid var(--hair);
            border-radius:10px; }
  .scroll table { font-size:12px; }
  .scroll td, .scroll th { padding:4.5px 8px; }

  .pill { display:inline-block; border-radius:999px; padding:1.5px 9px;
          font-size:11px; font-weight:650; font-variant-numeric:tabular-nums; }
  .up { color:var(--pos); background:var(--posbg); }
  .dn { color:var(--neg); background:var(--negbg); }
  .fl { color:var(--warn); background:var(--warnbg); }
  .na { color:var(--muted); background:var(--nabg); font-weight:450; }
  .rgn td { background:#f4f3ee; font-size:10.5px; letter-spacing:.09em;
            text-transform:uppercase; color:var(--muted); font-weight:650;
            border-bottom:none; }

  .bars .brow { display:flex; align-items:center; gap:12px; margin-bottom:8px; }
  .bars .lbl { width:130px; flex-shrink:0; font-size:12.5px; color:var(--ink2); }
  .bars .track { flex:1; background:var(--track); border-radius:999px; }
  .bars .bar { height:12px; background:var(--accent); border-radius:999px; }
  .bars .bar.warn { background:var(--neg); }
  .bars .val { width:140px; text-align:right; font-size:12px; color:var(--ink2);
               font-variant-numeric:tabular-nums; white-space:nowrap; }
  .bars.wide .lbl { width:200px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
  .bars .bar.pos { background:#0ca30c; }
  .bars .bar.neg { background:var(--neg); }

  .itin { margin-bottom:14px; }
  .itin h4 { font-size:13px; margin-bottom:6px; }
  .itin .opt { display:flex; justify-content:space-between; gap:10px; padding:7px 11px;
    border-radius:9px; font-size:12.5px; margin-bottom:5px; background:#f4f3ee; }
  .itin .opt.best { background:var(--posbg); box-shadow:inset 3px 0 0 #0ca30c; }
  .itin .opt .m { color:var(--muted); white-space:nowrap;
                  font-variant-numeric:tabular-nums; }
  .itin .opt.best .m { color:var(--pos); font-weight:650; }

  .flag { display:flex; justify-content:space-between; gap:10px; padding:8px 11px;
          background:var(--negbg); border-radius:9px; margin-bottom:6px;
          font-size:12.5px; box-shadow:inset 3px 0 0 var(--neg); }
  .flag b { color:var(--neg); }

  .mh { display:flex; align-items:baseline; gap:10px; margin:30px 0 10px; }
  .mh .n { font-size:11.5px; font-weight:700; color:var(--panel);
           background:var(--ink); border-radius:7px; padding:2.5px 8px;
           font-variant-numeric:tabular-nums; }
  .mh h2 { font-size:15px; font-weight:700; letter-spacing:-.01em; }
  .mh .src { color:var(--muted); font-size:11.5px; margin-left:auto; }
  .sect { font-size:18px; font-weight:800; margin:34px 0 4px;
          letter-spacing:-.015em; }
  .sectd { color:var(--muted); font-size:13px; margin-bottom:16px; }
</style>
</head>
<body>

<div class="top">
  <div class="name">Freight Network Analytics</div>
  <div class="meta" id="topMeta"></div>
  <div class="langs" id="lang">
    <a data-l="en" class="on">EN</a><a data-l="uk">УКР</a><a data-l="ru">РУС</a>
  </div>
</div>

<div class="shell">
<nav id="nav"></nav>
<main>

<div class="row"><div class="panel kpis" id="kpis" style="padding:0"></div></div>

<div class="row r2" id="ovTrendRow">
  <div class="panel"><div class="pt" id="pTrend"></div><div id="trend"></div>
    <div class="note" id="noteTrend"></div>
    <div class="pt" id="pOntime" style="margin-top:16px"></div><div id="ontime"></div></div>
  <div class="panel"><div class="pt" id="pRegions"></div>
    <div class="bars" id="regionBars"></div><div class="note" id="noteRegion"></div>
    <div class="pt" id="pAging" style="margin-top:16px"></div>
    <div class="bars" id="agingBars"></div><div class="note" id="noteAging"></div></div>
</div>

<div class="row r2" id="ovCharts">
  <div class="panel"><div class="pt" id="pYoy"></div><div class="bars wide" id="yoyBars"></div></div>
  <div class="panel"><div class="pt" id="pLanes"></div><div class="bars wide" id="laneBars"></div></div>
</div>

<div class="row" id="ovChoke">
  <div class="panel"><div class="pt" id="pChoke"></div>
    <div class="bars wide" id="chokeBars"></div>
    <div class="note" id="noteChoke"></div></div>
</div>

<div class="row" id="ovPorts">
  <div class="panel"><div class="pt" id="pPorts"></div>
    <table id="portsTbl"><thead></thead><tbody></tbody></table>
    <div class="note" id="notePorts"></div><div class="note" id="noteZero"></div></div>
</div>

<div class="row r3">
  <div class="panel" id="routesPanel"><div class="pt" id="pRoutes"></div><div id="routes"></div></div>
  <div class="panel"><div class="pt" id="pAml"></div><div id="aml"></div></div>
</div>

<div class="sect" id="modsTitle"></div>
<div class="sectd" id="modsDesc"></div>
<div id="modules"></div>

</main>
</div>

<script>
const D = __DATA__;
const fmt = n => n==null ? '—' : new Intl.NumberFormat('en-US').format(Math.round(n));
const usd = n => n==null ? '—' : '$' + (n>=1e6 ? (n/1e6).toFixed(2)+'M' : fmt(n));
const F = D.facts;

/* ── translations (English is ALWAYS the default on load) ───────────────── */
const I18N = {
en: {
  meta:"Data through {d} · satellite feed: IMF PortWatch · FX: ECB / NBU · generated {g} · book of business is synthetic, port activity and FX are real",
  metaNone:"Synthetic data only — run fetch_real_data.py for the live feed",
  navOverview:"Overview", navModules:"Query results",
  kRev:"Revenue", kRevN:"FX-true, all invoices",
  kShp:"Shipments", kShpN:"two years",
  kCus:"Customers", kCusN:"active, last 180 days",
  kOnt:"On time", kOntN:"± 2 days of ETA",
  kOut:"Unpaid", kOutN:"{x} is 90+ days late",
  kTra:"Avg transit", kTraN:"port to port", dUnit:"d",
  pTrend:"Shipments per month",
  pRegions:"Revenue by region", pAging:"Unpaid invoices by age",
  pPorts:"Ports — live satellite view (last 90 days vs a year ago; sparkline = 26 weeks)",
  pRoutes:"Door-to-door routes — ranked", pAml:"AML alerts",
  pYoy:"Port cargo, year over year — satellite data",
  pLanes:"Top-10 busiest lanes, shipments",
  pChoke:"Chokepoint exposure — our cargo vs real strait transits",
  noteChoke:"Share of the last-180-day book that sails through each strait · badge = real container transits, 90 days vs a year ago (IMF PortWatch).",
  pOntime:"On-time arrivals by month, %",
  noteTrend:"Peak month: <b>{m}</b> — {n} shipments.",
  noteRegion:"<b>{r}</b> ≈ {p}% of all revenue.",
  noteAging:"<b>{p}%</b> of unpaid money is already 90+ days late.",
  notePorts:"Fastest riser: <b>{up}</b> (+{upp}%) · steepest fall: <b>{dn}</b> ({dnp}%).",
  noteZero:"<b>{z}</b>: zero container traffic right now.",
  portsH:["Port","Country","Cargo/day","vs last yr","26 weeks","Our volume, 180d"],
  kt:"kt", noTraffic:"no traffic", noData:"no data",
  pick:"best", noAlerts:"Nothing caught this run.",
  modsTitle:"All query results",
  modsDesc:"Complete output of every analytical module, exactly as produced by the SQL pipeline. Scroll inside a table if it is long; the header stays put.",
  rows:"rows", src:"source",
  regions:{Europe:"Europe",Asia:"Asia",MEA:"Middle East & Africa",Americas:"Americas"},
  buckets:{"Not yet due":"Not yet due","1–30 days":"1–30 days","31–60 days":"31–60 days","61–90 days":"61–90 days","90+ days":"90+ days"},
  modes:{truck:"truck",rail:"rail"},
  screens:{"A · STRUCTURING":"Structuring","B · DUPLICATE BILLING":"Duplicate billing"},
  mods:{}
},
uk: {
  meta:"Дані до {d} · супутниковий фід: IMF PortWatch · курси: ЄЦБ / НБУ · згенеровано {g} · книга бізнесу синтетична, активність портів і курси — реальні",
  metaNone:"Лише синтетичні дані — запустіть fetch_real_data.py",
  navOverview:"Огляд", navModules:"Результати запитів",
  kRev:"Дохід", kRevN:"за курсом дня, всі інвойси",
  kShp:"Відправлення", kShpN:"два роки",
  kCus:"Клієнти", kCusN:"активні за 180 днів",
  kOnt:"Вчасно", kOntN:"± 2 дні від ETA",
  kOut:"Не сплачено", kOutN:"{x} — прострочення 90+ днів",
  kTra:"Сер. транзит", kTraN:"порт – порт", dUnit:"дн",
  pTrend:"Відправлення за місяцями",
  pRegions:"Дохід за регіонами", pAging:"Несплачені інвойси за віком",
  pPorts:"Порти — супутникові дані (останні 90 днів проти року тому; лінія = 26 тижнів)",
  pRoutes:"Маршрути до дверей — ранжовані", pAml:"AML-сигнали",
  pYoy:"Вантаж портів, рік до року — супутник",
  pLanes:"Топ-10 найзавантаженіших лейнів, відправлення",
  pChoke:"Експозиція на протоки — наш вантаж проти реальних транзитів",
  noteChoke:"Частка книги за 180 днів, що йде через протоку · бейдж = реальні контейнерні транзити, 90 днів проти року тому (IMF PortWatch).",
  pOntime:"Вчасні прибуття за місяцями, %",
  noteTrend:"Піковий місяць: <b>{m}</b> — {n} відправлень.",
  noteRegion:"<b>{r}</b> ≈ {p}% усього доходу.",
  noteAging:"<b>{p}%</b> несплачених грошей — прострочення 90+ днів.",
  notePorts:"Найшвидше зростає <b>{up}</b> (+{upp}%) · найглибше падає <b>{dn}</b> ({dnp}%).",
  noteZero:"<b>{z}</b>: контейнерного трафіку зараз немає.",
  portsH:["Порт","Країна","Вантаж/добу","до мин. року","26 тижнів","Наш обсяг, 180дн"],
  kt:"кт", noTraffic:"немає трафіку", noData:"немає даних",
  pick:"кращий", noAlerts:"Цього разу нічого не спіймано.",
  modsTitle:"Усі результати запитів",
  modsDesc:"Повний вивід кожного аналітичного модуля — точно так, як його видав SQL-конвеєр. Довгі таблиці прокручуються всередині; шапка лишається на місці.",
  rows:"рядків", src:"джерело",
  regions:{Europe:"Європа",Asia:"Азія",MEA:"Бл. Схід і Африка",Americas:"Америки"},
  buckets:{"Not yet due":"Строк не настав","1–30 days":"1–30 днів","31–60 days":"31–60 днів","61–90 days":"61–90 днів","90+ days":"90+ днів"},
  modes:{truck:"вантажівка",rail:"залізниця"},
  screens:{"A · STRUCTURING":"Дроблення сум","B · DUPLICATE BILLING":"Дубльовані рахунки"},
  chokes:{"Suez Canal":"Суецький канал","Bosporus Strait":"Босфор","Bab el-Mandeb Strait":"Баб-ель-Мандеб","Malacca Strait":"Малаккська протока","Strait of Hormuz":"Ормузька протока","Gibraltar Strait":"Гібралтар","Dover Strait":"Дуврська протока","Oresund Strait":"Ересунн"},
  cols:{month:"місяць",shipments:"відправлення",mom_change:"зміна м/м",mom_growth_pct:"ріст м/м, %",total_cbm:"обсяг, CBM",cumulative_cbm:"накопич. CBM",shipments_3mo_avg:"середнє 3 міс",active_customers:"активні клієнти",on_time_pct:"вчасно, %",avg_transit_days:"сер. транзит, дн",routing:"маршрут",legs:"плечі",modes:"режими",transit_days:"днів у дорозі",cost_per_cbm_usd:"ціна за CBM, $",cost_rank:"ранг за ціною",speed_rank:"ранг за швидкістю",stage:"етап",location:"порт",observations:"спостереження",median_days:"медіана, дн",p90_days:"p90, дн",worst_case_days:"найгірше, дн",p90_to_median_ratio:"p90/медіана",segment:"сегмент",customers:"клієнти",revenue_usd:"дохід, $",revenue_share_pct:"частка доходу, %",class_a_customers:"клас A",class_b_customers:"клас B",class_c_customers:"клас C",cohort:"когорта",size:"розмір",q0:"кв. 0",q1_pct:"кв. 1, %",q2_pct:"кв. 2, %",q3_pct:"кв. 3, %",q4_pct:"кв. 4, %",q5_pct:"кв. 5, %",q6_pct:"кв. 6, %",region:"регіон",quarter:"квартал",invoices:"інвойси",avg_invoice_usd:"сер. інвойс, $",currencies_billed:"валют",aging_bucket:"кошик прострочення",outstanding_usd:"не сплачено, $",share_pct:"частка, %",customers_affected:"клієнтів",shipment_id:"відправлення",lane:"лейн",actual_days:"факт, дн",lane_avg_days:"середнє лейну, дн",z_score:"z-оцінка",days_late_vs_eta:"запізнення до ETA, дн",severity:"важливість",screen:"перевірка",customer_name:"клієнт",invoice_id:"інвойс",issue_date:"дата виставлення",amount:"сума",evidence_count:"епізодів",evidence_amount:"сума епізодів",check_name:"перевірка",violations:"порушень",port_name:"порт",data_through:"дані до",days_observed:"днів спостережень",ctr_calls_per_day:"конт. заходи/добу",ctr_calls_yoy_pct:"заходи р/р, %",cargo_kt_per_day:"вантаж, кт/добу",cargo_yoy_pct:"вантаж р/р, %",shipments_180d:"відправлення 180дн",cbm_180d:"CBM 180дн",share_of_book_pct:"частка книги, %",real_calls_yoy_pct:"реальні заходи р/р, %",real_world_signal:"сигнал",request:"запит",rank:"ранг",route:"маршрут",gateway:"порт-шлюз",inland_mode:"наземний режим",total_days:"всього днів",usd_per_cbm:"$ за CBM",real_data_buffer_d:"буфер за даними, дн",score:"бал",yoy_growth_pct:"ріст р/р, %",customer:"клієнт",paid:"сплачено",avg_days_late:"сер. запізнення, дн",paid_late_pct:"сплачено пізно, %",overdue_90d_usd:"прострочено 90+, $",dso_days:"DSO, дн",lane_median_days:"медіана лейну, дн",robust_z:"робастний z",classic_z:"класичний z",currency:"валюта",evidence_usd:"сума епізодів, $",chokepoint:"протока",lanes:"лейни",transits_per_day:"транзитів/добу",transits_yoy_pct:"транзити р/р, %"},
  mods:{"01":"Ключові показники","02":"Пошук маршрутів (граф)","03":"Вузькі місця транзиту","04":"Сегментація клієнтів","05":"Когортне утримання","06":"Дохід у USD (FX)","07":"Старіння дебіторки","07b":"Платіжна дисципліна і DSO","08":"Аномалії транзиту","09":"AML-скринінг","10":"Якість даних","11":"Реальна активність портів","12":"Експозиція мережі","13":"Експозиція на протоки","14":"Маршрути до дверей"}
},
ru: {
  meta:"Данные по {d} · спутниковый фид: IMF PortWatch · курсы: ЕЦБ / НБУ · сгенерировано {g} · книга бизнеса синтетическая, активность портов и курсы — реальные",
  metaNone:"Только синтетические данные — запустите fetch_real_data.py",
  navOverview:"Обзор", navModules:"Результаты запросов",
  kRev:"Выручка", kRevN:"по курсу дня, все инвойсы",
  kShp:"Отправки", kShpN:"два года",
  kCus:"Клиенты", kCusN:"активные за 180 дней",
  kOnt:"Вовремя", kOntN:"± 2 дня от ETA",
  kOut:"Не оплачено", kOutN:"{x} — просрочка 90+ дней",
  kTra:"Ср. транзит", kTraN:"порт – порт", dUnit:"дн",
  pTrend:"Отправки по месяцам",
  pRegions:"Выручка по регионам", pAging:"Неоплаченные инвойсы по возрасту",
  pPorts:"Порты — спутниковые данные (последние 90 дней против года назад; линия = 26 недель)",
  pRoutes:"Маршруты до двери — ранжированные", pAml:"AML-сигналы",
  pYoy:"Груз портов, год к году — спутник",
  pLanes:"Топ-10 самых загруженных лейнов, отправки",
  pChoke:"Экспозиция на проливы — наш груз против реальных транзитов",
  noteChoke:"Доля книги за 180 дней, идущая через пролив · бейдж = реальные контейнерные транзиты, 90 дней против года назад (IMF PortWatch).",
  pOntime:"Прибытия вовремя по месяцам, %",
  noteTrend:"Пиковый месяц: <b>{m}</b> — {n} отправок.",
  noteRegion:"<b>{r}</b> ≈ {p}% всей выручки.",
  noteAging:"<b>{p}%</b> неоплаченных денег — просрочка 90+ дней.",
  notePorts:"Быстрее всех растёт <b>{up}</b> (+{upp}%) · глубже всех падает <b>{dn}</b> ({dnp}%).",
  noteZero:"<b>{z}</b>: контейнерного трафика сейчас нет.",
  portsH:["Порт","Страна","Груз/сутки","к прош. году","26 недель","Наш объём, 180дн"],
  kt:"кт", noTraffic:"нет трафика", noData:"нет данных",
  pick:"лучший", noAlerts:"В этот раз ничего не поймано.",
  modsTitle:"Все результаты запросов",
  modsDesc:"Полный вывод каждого аналитического модуля — ровно так, как его выдал SQL-конвейер. Длинные таблицы прокручиваются внутри; шапка остаётся на месте.",
  rows:"строк", src:"источник",
  regions:{Europe:"Европа",Asia:"Азия",MEA:"Бл. Восток и Африка",Americas:"Америки"},
  buckets:{"Not yet due":"Срок не наступил","1–30 days":"1–30 дней","31–60 days":"31–60 дней","61–90 days":"61–90 дней","90+ days":"90+ дней"},
  modes:{truck:"фура",rail:"ж/д"},
  screens:{"A · STRUCTURING":"Дробление сумм","B · DUPLICATE BILLING":"Дубли счетов"},
  chokes:{"Suez Canal":"Суэцкий канал","Bosporus Strait":"Босфор","Bab el-Mandeb Strait":"Баб-эль-Мандеб","Malacca Strait":"Малаккский пролив","Strait of Hormuz":"Ормузский пролив","Gibraltar Strait":"Гибралтар","Dover Strait":"Дуврский пролив","Oresund Strait":"Эресунн"},
  cols:{month:"месяц",shipments:"отправки",mom_change:"изм. м/м",mom_growth_pct:"рост м/м, %",total_cbm:"объём, CBM",cumulative_cbm:"накопл. CBM",shipments_3mo_avg:"среднее 3 мес",active_customers:"активные клиенты",on_time_pct:"вовремя, %",avg_transit_days:"ср. транзит, дн",routing:"маршрут",legs:"плечи",modes:"режимы",transit_days:"дней в пути",cost_per_cbm_usd:"цена за CBM, $",cost_rank:"ранг по цене",speed_rank:"ранг по скорости",stage:"этап",location:"порт",observations:"наблюдения",median_days:"медиана, дн",p90_days:"p90, дн",worst_case_days:"худшее, дн",p90_to_median_ratio:"p90/медиана",segment:"сегмент",customers:"клиенты",revenue_usd:"выручка, $",revenue_share_pct:"доля выручки, %",class_a_customers:"класс A",class_b_customers:"класс B",class_c_customers:"класс C",cohort:"когорта",size:"размер",q0:"кв. 0",q1_pct:"кв. 1, %",q2_pct:"кв. 2, %",q3_pct:"кв. 3, %",q4_pct:"кв. 4, %",q5_pct:"кв. 5, %",q6_pct:"кв. 6, %",region:"регион",quarter:"квартал",invoices:"инвойсы",avg_invoice_usd:"ср. инвойс, $",currencies_billed:"валют",aging_bucket:"корзина просрочки",outstanding_usd:"не оплачено, $",share_pct:"доля, %",customers_affected:"клиентов",shipment_id:"отправка",lane:"лейн",actual_days:"факт, дн",lane_avg_days:"среднее лейна, дн",z_score:"z-оценка",days_late_vs_eta:"опоздание к ETA, дн",severity:"важность",screen:"проверка",customer_name:"клиент",invoice_id:"инвойс",issue_date:"дата выставления",amount:"сумма",evidence_count:"эпизодов",evidence_amount:"сумма эпизодов",check_name:"проверка",violations:"нарушений",port_name:"порт",data_through:"данные по",days_observed:"дней наблюдений",ctr_calls_per_day:"конт. заходы/сутки",ctr_calls_yoy_pct:"заходы г/г, %",cargo_kt_per_day:"груз, кт/сутки",cargo_yoy_pct:"груз г/г, %",shipments_180d:"отправки 180дн",cbm_180d:"CBM 180дн",share_of_book_pct:"доля книги, %",real_calls_yoy_pct:"реальные заходы г/г, %",real_world_signal:"сигнал",request:"запрос",rank:"ранг",route:"маршрут",gateway:"порт-шлюз",inland_mode:"наземный режим",total_days:"всего дней",usd_per_cbm:"$ за CBM",real_data_buffer_d:"буфер по данным, дн",score:"балл",yoy_growth_pct:"рост г/г, %",customer:"клиент",paid:"оплачено",avg_days_late:"ср. опоздание, дн",paid_late_pct:"оплачено с опозданием, %",overdue_90d_usd:"просрочено 90+, $",dso_days:"DSO, дн",lane_median_days:"медиана лейна, дн",robust_z:"робастный z",classic_z:"классический z",currency:"валюта",evidence_usd:"сумма эпизодов, $",chokepoint:"пролив",lanes:"лейны",transits_per_day:"транзитов/сутки",transits_yoy_pct:"транзиты г/г, %"},
  mods:{"01":"Ключевые показатели","02":"Поиск маршрутов (граф)","03":"Узкие места транзита","04":"Сегментация клиентов","05":"Когортное удержание","06":"Выручка в USD (FX)","07":"Старение дебиторки","07b":"Платёжная дисциплина и DSO","08":"Аномалии транзита","09":"AML-скрининг","10":"Качество данных","11":"Реальная активность портов","12":"Экспозиция сети","13":"Экспозиция на проливы","14":"Маршруты до двери"}
}};
let LANG = 'en';                                 /* ALWAYS starts in English */
const T = k => I18N[LANG][k] ?? I18N.en[k] ?? k;
const M = (map, key) => (I18N[LANG][map] || {})[key] ?? key;
const S = (k, vars) => Object.entries(vars).reduce(
  (s,[kk,v]) => s.replaceAll('{'+kk+'}', v), T(k));
const modTitle = m => LANG==='en' ? m.title : ((I18N[LANG].mods||{})[m.num] || m.title);

function renderTop() {
  document.documentElement.lang = LANG;
  topMeta.textContent = D.fresh
    ? S('meta',{d:D.fresh, g:D.generated}) : T('metaNone');
}

function renderNav() {
  nav.innerHTML =
    `<div class="nh">${T('navOverview')}</div>
     <a href="#kpis">${T('kRev')} · KPI</a>
     <a href="#ovTrendRow">${T('pTrend')}</a>
     <a href="#ovChoke">${T('pChoke').split('—')[0]}</a>
     <a href="#ovPorts">${T('pPorts').split('(')[0]}</a>
     <a href="#routesPanel">${T('pRoutes')}</a>
     <div class="nh">${T('navModules')}</div>` +
    D.modules.map(m =>
      `<a href="#m${m.num}">${m.num} · ${modTitle(m)}</a>`).join('');
}

function renderKPIs() {
  const K = D.kpi, items = [
    [T('kRev'), usd(K.revenue_usd), T('kRevN')],
    [T('kShp'), fmt(K.shipments), T('kShpN')],
    [T('kCus'), fmt(K.customers), T('kCusN')],
    [T('kOnt'), K.on_time_pct+'%', T('kOntN')],
    [T('kOut'), usd(K.outstanding_usd), S('kOutN',{x:usd(K.overdue90_usd)})],
    [T('kTra'), K.avg_transit+' '+T('dUnit'), T('kTraN')],
  ];
  kpis.innerHTML = items.map(k =>
    `<div class="kpi"><div class="l">${k[0]}</div><div class="v">${k[1]}</div>
     <div class="n">${k[2]}</div></div>`).join('');
}

/* bar with a 4px rounded data-end, anchored flat on the baseline */
function barPath(x, y, w, h, r) {
  r = Math.min(r, w/2, h);
  return `M${(x).toFixed(1)},${(y+h).toFixed(1)} v${(-(h-r)).toFixed(1)} ` +
         `q0,${(-r).toFixed(1)} ${r.toFixed(1)},${(-r).toFixed(1)} ` +
         `h${(w-2*r).toFixed(1)} q${r.toFixed(1)},0 ${r.toFixed(1)},${r.toFixed(1)} ` +
         `v${(h-r).toFixed(1)} z`;
}
function renderTrend() {
  const W=740, H=170, padB=24, padT=18, n=D.monthly.length;
  const max = Math.max(...D.monthly.map(r=>r.shipments));
  const gap = W/n, bw = gap*0.6;
  let s = `<svg viewBox="0 0 ${W} ${H}" style="width:100%">`;
  s += `<line x1="0" y1="${H-padB}" x2="${W}" y2="${H-padB}" stroke="#c3c2b7"/>`;
  D.monthly.forEach((r,i) => {
    const h = (H-padB-padT)*r.shipments/max, x = i*gap+(gap-bw)/2, y = H-padB-h;
    const peak = r.shipments===max;
    s += `<path d="${barPath(x, y, bw, h, 4)}"
      fill="${peak?'#256abf':'#9ec5f4'}">
      <title>${r.m}: ${fmt(r.shipments)}</title></path>`;
    if (peak) s += `<text x="${(x+bw/2).toFixed(1)}" y="${(y-6).toFixed(1)}"
      text-anchor="middle" font-size="11" font-weight="650"
      fill="#1c5cab">${fmt(r.shipments)}</text>`;
    if (i%3===0) {
      const [yy,mm]=r.m.split('-');
      s += `<text x="${(x+bw/2).toFixed(1)}" y="${H-8}" text-anchor="middle"
        font-size="10" fill="#898781">${mm}.${yy.slice(2)}</text>`;
    }
  });
  trend.innerHTML = s + '</svg>';
  noteTrend.innerHTML = S('noteTrend',{m:F.peakM, n:fmt(F.peakN)});
}

function barRows(el, rows, warnIdx) {
  const mx = Math.max(...rows.map(r=>r.v), 1);
  el.innerHTML = rows.map((r,i) =>
    `<div class="brow"><div class="lbl">${r.l}</div>
     <div class="track"><div class="bar${i===warnIdx?' warn':''}"
       style="width:${Math.max(2,100*r.v/mx)}%"></div></div>
     <div class="val">${usd(r.v)}${r.x?' · '+r.x:''}</div></div>`).join('');
}
function renderBars() {
  const tot = D.regions.reduce((a,r)=>a+r.usd,0)||1;
  barRows(regionBars, D.regions.map(r =>
    ({l:M('regions',r.region), v:r.usd, x:Math.round(100*r.usd/tot)+'%'})), -1);
  barRows(agingBars, D.aging.map(r =>
    ({l:M('buckets',r.bucket), v:r.usd})), D.aging.findIndex(r=>r.bucket==='90+ days'));
  noteRegion.innerHTML = S('noteRegion',{r:M('regions',F.topRegion), p:F.topRegionPct});
  noteAging.innerHTML = F.overduePct!=null ? S('noteAging',{p:F.overduePct}) : '';
}

function spark(vals) {
  if (!vals || vals.length < 3) return '';
  const W=140, H=22, mn=Math.min(...vals), mx=Math.max(...vals);
  const pts = vals.map((v,i) =>
    (i/(vals.length-1)*W).toFixed(1)+','+
    (mx===mn?H/2:H-2-((v-mn)/(mx-mn))*(H-4)).toFixed(1)).join(' ');
  return `<svg viewBox="0 0 ${W} ${H}" width="${W}" height="${H}">
    <polyline points="${pts}" fill="none" stroke="#2a78d6" stroke-width="1.5"
      stroke-linejoin="round" stroke-linecap="round"/></svg>`;
}
function renderPorts() {
  document.querySelector('#portsTbl thead').innerHTML = '<tr>' +
    T('portsH').map((h,i)=>`<th${i===2||i===3||i===5?' class="num"':''}>${h}</th>`).join('')+'</tr>';
  const order=['Europe','Asia','MEA','Americas'];
  let rows='';
  order.forEach(reg => {
    const ps = D.ports.filter(p=>p.region===reg);
    if (!ps.length) return;
    rows += `<tr class="rgn"><td colspan="6">${M('regions',reg)}</td></tr>`;
    ps.forEach(p => {
      let t;
      if (p.kt_day==null) t = `<span class="pill na">${T('noData')}</span>`;
      else if (p.kt_day===0) t = `<span class="pill na">${T('noTraffic')}</span>`;
      else if (p.yoy==null) t = `<span class="pill na">—</span>`;
      else t = `<span class="pill ${p.yoy>=3?'up':(p.yoy<=-3?'dn':'fl')}">${p.yoy>0?'+':''}${p.yoy}%</span>`;
      rows += `<tr><td><b>${p.name}</b></td><td>${p.country}</td>
        <td class="num">${p.kt_day==null?'—':fmt(p.kt_day)+' '+T('kt')}</td>
        <td class="num">${t}</td><td>${spark(D.spark[p.code])}</td>
        <td class="num">${fmt(p.cbm180)} cbm</td></tr>`;
    });
  });
  document.querySelector('#portsTbl tbody').innerHTML = rows;
  notePorts.innerHTML = F.upPort!=null
    ? S('notePorts',{up:F.upPort,upp:F.upPct,dn:F.dnPort,dnp:F.dnPct}) : '';
  noteZero.innerHTML = F.zeroPorts.length ? S('noteZero',{z:F.zeroPorts.join(', ')}) : '';
}

function renderRoutes() {
  if (!D.routes13.length) { routesPanel.style.display = 'none'; return; }
  routesPanel.style.display = '';
  routesPanel.innerHTML = `<div class="pt">${T('pRoutes')}</div>`;
  const groups = {};
  D.routes13.forEach(r => (groups[r.request]=groups[r.request]||[]).push(r));
  routesPanel.innerHTML += Object.entries(groups).map(([req,rs]) =>
    `<div class="itin"><h4>${req}</h4>` + rs.map(r =>
      `<div class="opt${r.rank===1?' best':''}">
        <span>${r.rank}. ${r.route} <span style="color:var(--muted)">· ${M('modes',r.mode)}</span></span>
        <span class="m">${r.days} ${T('dUnit')} · $${r.usd}/cbm${r.rank===1?' · '+T('pick'):''}</span>
      </div>`).join('') + '</div>').join('');
}

function renderAML() {
  aml.innerHTML = D.aml.length ? D.aml.map(a =>
    `<div class="flag"><span><b>${M('screens',a.screen)}</b> — ${a.customer}
      <span style="color:var(--muted)">${a.invoice}</span></span>
      <b>$${fmt(a.amount)}</b></div>`).join('')
    : `<div class="note">${T('noAlerts')}</div>`;
}

const colT = c => LANG==='en' ? c : ((I18N[LANG].cols||{})[c] || c);

function renderYoy() {
  pYoy.textContent = T('pYoy');
  const ps = D.ports.filter(p=>p.yoy!=null && p.kt_day).sort((a,b)=>b.yoy-a.yoy);
  const mx = Math.max(...ps.map(p=>Math.abs(p.yoy)), 1);
  yoyBars.innerHTML = ps.map(p =>
    `<div class="brow"><div class="lbl">${p.name}</div>
     <div class="track"><div class="bar ${p.yoy>=0?'pos':'neg'}"
       style="width:${Math.max(2,100*Math.abs(p.yoy)/mx)}%"></div></div>
     <div class="val">${p.yoy>0?'+':''}${p.yoy}%</div></div>`).join('');
}

function renderLanes() {
  pLanes.textContent = T('pLanes');
  const mx = Math.max(...D.lanes.map(l=>l.n), 1);
  laneBars.innerHTML = D.lanes.map(l =>
    `<div class="brow"><div class="lbl">${l.l}</div>
     <div class="track"><div class="bar" style="width:${Math.max(2,100*l.n/mx)}%"></div></div>
     <div class="val">${fmt(l.n)}</div></div>`).join('');
}

function renderChoke() {
  const box = document.getElementById('ovChoke');
  if (!D.choke || !D.choke.length) { box.style.display = 'none'; return; }
  pChoke.textContent = T('pChoke');
  noteChoke.innerHTML = T('noteChoke');
  const mx = Math.max(...D.choke.map(c=>c.share), 1);
  chokeBars.innerHTML = D.choke.map(c => {
    const pill = c.yoy==null
      ? `<span class="pill na">${T('noData')}</span>`
      : `<span class="pill ${c.yoy<=-8?'dn':(c.yoy>=8?'up':'fl')}">${c.yoy>0?'+':''}${c.yoy}%</span>`;
    return `<div class="brow"><div class="lbl">${M('chokes',c.name)}</div>
     <div class="track"><div class="bar" style="width:${Math.max(2,100*c.share/mx)}%"></div></div>
     <div class="val">${c.share}% · ${pill}</div></div>`;
  }).join('');
}

function renderOntime() {
  pOntime.textContent = T('pOntime');
  const W=740, H=120, padB=18, padT=12, n=D.ontime.length;
  const vals = D.ontime.map(r=>r.pct), mn = Math.min(...vals)-4, mxv = 100;
  const X = i => i/(n-1)*(W-30)+4, Y = v => padT+(H-padB-padT)*(1-(v-mn)/(mxv-mn));
  let s = `<svg viewBox="0 0 ${W} ${H}" style="width:100%">`;
  s += `<line x1="0" y1="${H-padB}" x2="${W-26}" y2="${H-padB}" stroke="#e1e0d9"/>`;
  s += `<polyline points="${D.ontime.map((r,i)=>X(i).toFixed(1)+','+Y(r.pct).toFixed(1)).join(' ')}"
        fill="none" stroke="#2a78d6" stroke-width="2"
        stroke-linejoin="round" stroke-linecap="round"/>`;
  D.ontime.forEach((r,i) => {
    s += `<circle cx="${X(i).toFixed(1)}" cy="${Y(r.pct).toFixed(1)}" r="8"
      fill="transparent"><title>${r.m}: ${r.pct}%</title></circle>`;
    if (i%4===0) { const [yy,mm]=r.m.split('-');
      s += `<text x="${X(i).toFixed(1)}" y="${H-5}" text-anchor="middle"
        font-size="10" fill="#898781">${mm}.${yy.slice(2)}</text>`; }
  });
  const last = D.ontime[n-1];
  s += `<text x="${(X(n-1)+4).toFixed(1)}" y="${(Y(last.pct)+4).toFixed(1)}"
    font-size="11" font-weight="650" fill="#1c5cab">${last.pct}%</text>`;
  ontime.innerHTML = s + '</svg>';
}

function renderModules() {
  modsTitle.textContent = T('modsTitle');
  modsDesc.textContent = T('modsDesc');
  modules.innerHTML = D.modules.map(m => {
    const head = '<tr>'+m.cols.map(c=>`<th>${colT(c)}</th>`).join('')+'</tr>';
    const body = m.rows.map(r =>
      '<tr>'+r.map(v=>`<td${/^-?[\d,.]+%?$/.test(v)?' class="num"':''}>${v}</td>`).join('')+'</tr>').join('');
    const big = m.rows.length > 12;
    return `<div class="mh" id="m${m.num}"><span class="n">${m.num}</span>
        <h2>${modTitle(m)}</h2>
        <span class="src">${m.rows.length} ${T('rows')} · ${m.src}</span></div>
      <div class="panel" style="padding:${big?'0':'6px 8px'}">
        ${big?'<div class="scroll">':''}<table><thead>${head}</thead>
        <tbody>${body}</tbody></table>${big?'</div>':''}</div>`;
  }).join('');
}

function renderAll() {
  renderTop(); renderNav(); renderKPIs(); renderTrend(); renderBars();
  renderYoy(); renderLanes(); renderChoke(); renderOntime();
  renderPorts(); renderRoutes(); renderAML(); renderModules();
}
function setLang(l) {
  LANG = l;
  document.querySelectorAll('#lang a').forEach(a =>
    a.classList.toggle('on', a.dataset.l===l));
  pTrend.textContent=T('pTrend'); pRegions.textContent=T('pRegions');
  pAging.textContent=T('pAging'); pPorts.textContent=T('pPorts');
  pAml.textContent=T('pAml');
  renderAll();
}
document.querySelectorAll('#lang a').forEach(a =>
  a.addEventListener('click', () => setLang(a.dataset.l)));

setLang('en');   /* first paint: English */
</script>
</body></html>
"""


def main():
    if not DB.exists():
        raise SystemExit("freight.duckdb not found — run run_pipeline.py first")
    con = duckdb.connect(str(DB), read_only=True)
    data = collect(con)
    con.close()
    OUT.parent.mkdir(exist_ok=True)
    html = (TEMPLATE
            .replace("__DATA__", json.dumps(data, default=str))
            .replace("__GENERATED__", data["generated"]))
    OUT.write_text(html)
    print(f"Dashboard written to {OUT.relative_to(BASE)} "
          f"({len(html)//1024} KB) — double-click to open in a browser")


if __name__ == "__main__":
    main()
