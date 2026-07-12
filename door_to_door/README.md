# Door-to-door routing — optional extension

Ranks the best multimodal routes from an origin port to an inland city
(e.g. Shanghai → Poltava: via Odesa vs via Gdansk), combining:

* the sea/rail network graph (`shipping_routes`, recursive CTE pathfinding),
* inland truck/rail legs from `inland_legs.csv` (**editable tariff estimates**,
  not live market rates),
* a war-risk surcharge per gateway port (edit `port_risk` in the SQL),
* a congestion buffer computed from **real IMF PortWatch data** — rankings
  re-shuffle automatically after each `fetch_real_data.py` run.

## How to use

* Ask new questions: add rows to `route_requests` in `schema.sql`
  (`('CNSHA', 'Lviv')` …) and re-run `run_pipeline.py` (module 14 in the
  report).
* Add destinations: a row in `cities` + legs in `inland_legs.csv`.
* Tune the trade-off: `usd_per_cbm_day` in `14_door_to_door_routing.sql`
  (higher = speed matters more than cost).

## How to remove

Delete (or rename) this folder. Nothing else references it — the main
pipeline detects its absence and runs exactly as before.
