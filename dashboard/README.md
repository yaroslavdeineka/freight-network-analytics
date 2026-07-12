# Visual dashboard — optional extension

Turns the analytical results into a single **analytics workbench page**:
`outputs/dashboard.html`. One fully self-contained file with zero external
dependencies — all charts are inline SVG, so it works completely offline.
Double-click, it opens in any browser. Languages: English (default),
Ukrainian, Russian — switchable in the top bar.

What's on it:

* a KPI strip — revenue at true historical FX, on-time %, cash stuck in
  receivables;
* monthly volume chart and revenue-by-region / invoice-aging bars;
* a **chokepoint-exposure panel** — the share of the book that sails
  through each strait vs real transit trends (IMF PortWatch);
* a **live port table** — real satellite-measured cargo flow per port
  (IMF PortWatch) with 26-week sparklines and year-over-year trends;
* ranked door-to-door routes and AML alerts;
* **the complete result tables of all 15 analytical modules**, verbatim,
  with a sticky sidebar to jump between them.

## How it runs

`run_pipeline.py` rebuilds the dashboard automatically at the end of every
run. Standalone: `python3 dashboard/build_dashboard.py`.

## How to remove

Delete (or rename) this folder — the pipeline detects its absence and runs
exactly as before. `outputs/dashboard.html` is a generated artifact; delete
it any time.
