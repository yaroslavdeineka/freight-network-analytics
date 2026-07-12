from pathlib import Path

import numpy as np
import pandas as pd

RNG = np.random.default_rng(7)
DATA_DIR = Path(__file__).parent.parent / "data"

SIM_START = pd.Timestamp("2024-07-01")
SIM_END = pd.Timestamp("2026-06-30")

# ---------------------------------------------------------------------------
# 1. Ports — real UN/LOCODEs across four regions
# ---------------------------------------------------------------------------
PORTS = [
    # code, name, country, region, lat, lon
    ("UAODS", "Odesa",        "Ukraine",        "Europe",   46.48, 30.73),
    ("PLGDN", "Gdansk",       "Poland",         "Europe",   54.40, 18.66),
    ("DEHAM", "Hamburg",      "Germany",        "Europe",   53.54, 9.98),
    ("NLRTM", "Rotterdam",    "Netherlands",    "Europe",   51.95, 4.14),
    ("GBFXT", "Felixstowe",   "United Kingdom", "Europe",   51.95, 1.31),
    ("TRMER", "Mersin",       "Turkey",         "MEA",      36.79, 34.64),
    ("EGALY", "Alexandria",   "Egypt",          "MEA",      31.19, 29.87),
    ("AEJEA", "Jebel Ali",    "UAE",            "MEA",      24.98, 55.06),
    ("INNSA", "Nhava Sheva",  "India",          "Asia",     18.95, 72.95),
    ("SGSIN", "Singapore",    "Singapore",      "Asia",     1.26,  103.84),
    ("CNSHA", "Shanghai",     "China",          "Asia",     31.22, 121.49),
    ("CNSZX", "Shenzhen",     "China",          "Asia",     22.54, 114.06),
    ("KRPUS", "Busan",        "South Korea",    "Asia",     35.10, 129.04),
    ("USNYC", "New York",     "United States",  "Americas", 40.67, -74.04),
    ("USLGB", "Long Beach",   "United States",  "Americas", 33.75, -118.19),
    ("BRSSZ", "Santos",       "Brazil",         "Americas", -23.95, -46.33),
]

# ---------------------------------------------------------------------------
# 2. Route graph — directed edges; both directions generated for sea lanes
# ---------------------------------------------------------------------------
# (origin, dest, mode, transit_days, cost_per_cbm)
BASE_ROUTES = [
    ("UAODS", "TRMER", "sea",  3, 22.0),
    ("UAODS", "EGALY", "sea",  5, 28.0),
    ("UAODS", "PLGDN", "rail", 4, 41.0),   # overland corridor
    ("PLGDN", "DEHAM", "sea",  2, 12.0),
    ("DEHAM", "NLRTM", "sea",  2, 10.0),
    ("NLRTM", "GBFXT", "sea",  1, 9.0),
    ("TRMER", "EGALY", "sea",  2, 14.0),
    ("TRMER", "NLRTM", "sea",  8, 34.0),
    ("TRMER", "AEJEA", "sea",  9, 38.0),
    ("EGALY", "AEJEA", "sea",  7, 30.0),
    ("EGALY", "NLRTM", "sea",  7, 31.0),
    ("EGALY", "SGSIN", "sea", 12, 44.0),
    ("AEJEA", "INNSA", "sea",  3, 16.0),
    ("AEJEA", "SGSIN", "sea",  7, 26.0),
    ("INNSA", "SGSIN", "sea",  5, 21.0),
    ("SGSIN", "CNSHA", "sea",  5, 19.0),
    ("SGSIN", "CNSZX", "sea",  3, 14.0),
    ("SGSIN", "KRPUS", "sea",  6, 23.0),
    ("CNSZX", "CNSHA", "sea",  2, 8.0),
    ("CNSHA", "KRPUS", "sea",  2, 9.0),
    ("CNSHA", "USLGB", "sea", 14, 52.0),
    ("KRPUS", "USLGB", "sea", 11, 47.0),
    ("NLRTM", "USNYC", "sea", 10, 40.0),
    ("GBFXT", "USNYC", "sea",  9, 39.0),
    ("NLRTM", "CNSHA", "sea", 28, 68.0),
    ("NLRTM", "SGSIN", "sea", 16, 55.0),
    ("SGSIN", "DEHAM", "sea", 17, 56.0),   # Asia-North Europe direct call
    ("EGALY", "CNSHA", "sea", 16, 50.0),   # Med-Far East service
    ("AEJEA", "NLRTM", "sea", 13, 46.0),   # Gulf-North Europe service
    ("NLRTM", "PLGDN", "sea",  3, 13.0),   # North Europe feeder
    ("USNYC", "USLGB", "rail", 5, 33.0),
    ("USNYC", "BRSSZ", "sea", 12, 45.0),
]

CURRENCY_BY_REGION = {
    "Europe": ["EUR", "USD", "GBP"],
    "MEA": ["USD", "EUR"],
    "Asia": ["USD", "CNY"],
    "Americas": ["USD"],
}

INDUSTRIES = [
    "Automotive parts", "Consumer electronics", "Agricultural produce",
    "Furniture", "Textiles & apparel", "Industrial machinery",
    "Pharmaceuticals", "Building materials", "Food & beverage", "Chemicals",
]

FIRST = ["Nova", "Baltic", "Trident", "Vector", "Atlas", "Meridian", "Polar",
         "Crown", "Delta", "Orion", "Vista", "Summit", "Anchor", "Falcon",
         "Global", "Prime", "United", "Eastern", "Coastal", "Central"]
SECOND = ["Trading", "Industries", "Logistics", "Imports", "Exports",
          "Manufacturing", "Distribution", "Commodities", "Group", "Supply"]
SUFFIX = ["Ltd", "GmbH", "LLC", "S.A.", "OÜ", "Sp. z o.o.", "PLC", "LLP"]


def make_ports():
    return pd.DataFrame(PORTS, columns=[
        "port_code", "port_name", "country", "region", "latitude", "longitude"
    ])


def make_routes():
    rows, rid = [], 1
    for o, d, mode, days, cost in BASE_ROUTES:
        rows.append((rid, o, d, mode, days, cost)); rid += 1
        rows.append((rid, d, o, mode, days, round(cost * 1.05, 2))); rid += 1
    return pd.DataFrame(rows, columns=[
        "route_id", "origin_port", "dest_port", "mode", "transit_days", "cost_per_cbm"
    ])


# The first N_ANCHORS customer ids are the "anchor" accounts: onboarded early,
# large credit limits, and ~55% of shipment volume (see make_shipments_...).
# Onboarding them early matters for realism: bookings are only generated
# inside each customer's lifetime, so a late-onboarded anchor would compress
# its whole history into a few months and create absurd volume spikes.
N_ANCHORS = 12


def make_customers(n=80):
    rows = []
    for i in range(1, n + 1):
        name = f"{RNG.choice(FIRST)} {RNG.choice(SECOND)} {RNG.choice(SUFFIX)}"
        if i <= N_ANCHORS:
            onboard = SIM_START + pd.Timedelta(days=int(RNG.integers(0, 60)))
            credit = 250_000
        else:
            onboard = SIM_START + pd.Timedelta(days=int(RNG.integers(0, 640)))
            tier = RNG.random()
            credit = 100_000 if tier > 0.6 else 30_000
        rows.append({
            "customer_id": i,
            "customer_name": name,
            "country": RNG.choice(["Ukraine", "Poland", "Germany", "Netherlands",
                                    "United Kingdom", "Turkey", "UAE", "China",
                                    "United States", "Egypt"]),
            "industry": RNG.choice(INDUSTRIES),
            "onboarded_date": onboard.date(),
            "credit_limit_usd": credit,
        })
    return pd.DataFrame(rows)


# Popular trade lanes with sensible transshipment hubs
LANES = [
    # (origin, dest, via or None, weight)
    ("CNSHA", "NLRTM", "SGSIN", 14),
    ("CNSZX", "DEHAM", "SGSIN", 10),
    ("CNSHA", "GBFXT", "NLRTM", 7),
    ("UAODS", "CNSHA", "EGALY", 6),
    ("UAODS", "NLRTM", "TRMER", 8),
    ("UAODS", "DEHAM", "PLGDN", 9),
    ("TRMER", "DEHAM", "NLRTM", 6),
    ("INNSA", "NLRTM", "AEJEA", 8),
    ("CNSHA", "USLGB", None, 10),
    ("NLRTM", "USNYC", None, 8),
    ("SGSIN", "USLGB", "CNSHA", 4),
    ("EGALY", "PLGDN", "NLRTM", 4),
    ("AEJEA", "UAODS", "TRMER", 3),
    ("KRPUS", "NLRTM", "SGSIN", 5),
]


def seasonal_weight(date):
    m = date.month
    if m in (9, 10, 11):     # peak season
        return 1.55
    if m == 12:
        return 1.2
    if m in (1, 2):          # CNY slowdown
        return 0.65
    return 1.0


def make_shipments_and_events(customers, routes, n_target=5200):
    route_lookup = {(r.origin_port, r.dest_port): r for r in routes.itertuples()}
    lanes, weights = zip(*[((o, d, v), w) for o, d, v, w in LANES])
    weights = np.array(weights, dtype=float); weights /= weights.sum()

    # Pareto assignment: the anchors take ~55% of volume
    cust_ids = customers["customer_id"].to_numpy()
    cust_prob = np.where(cust_ids <= N_ANCHORS,
                         0.55 / N_ANCHORS, 0.45 / (len(cust_ids) - N_ANCHORS))

    all_days = pd.date_range(SIM_START, SIM_END - pd.Timedelta(days=20), freq="D")
    day_w = np.array([seasonal_weight(d) for d in all_days], dtype=float)

    onboard_by_cust = {c.customer_id: pd.Timestamp(c.onboarded_date)
                       for c in customers.itertuples()}
    # Churn: ~18% of non-anchor customers stop booking 6–14 months after
    # onboarding. This is what gives module 05 a real retention curve and
    # module 04 genuine Dormant / At-Risk segments — without it every cohort
    # retains at ~100% and both modules have nothing to say.
    churn_by_cust = {}
    for cid, ob in onboard_by_cust.items():
        if cid > N_ANCHORS and RNG.random() < 0.18:
            churn_by_cust[cid] = ob + pd.Timedelta(days=int(RNG.integers(180, 420)))

    shipments, events = [], []
    eid = 1
    i = 0
    while i < n_target:
        cust = int(RNG.choice(cust_ids, p=cust_prob))
        # bookings live inside the customer's lifetime: [onboarding, churn].
        # Sampling within the window (instead of re-basing invalid dates onto
        # the onboarding month) keeps the monthly series free of artificial
        # spikes while preserving seasonality.
        start = max(onboard_by_cust[cust] + pd.Timedelta(days=2), SIM_START)
        end = min(churn_by_cust.get(cust, SIM_END), all_days[-1])
        lo = all_days.searchsorted(start)
        hi = all_days.searchsorted(end, side="right")
        if hi - lo < 5:                    # onboarded too late / churned early
            continue                       # resample another customer
        w = day_w[lo:hi] / day_w[lo:hi].sum()
        booked = pd.Timestamp(RNG.choice(all_days[lo:hi], p=w))
        i += 1

        origin, dest, via = lanes[RNG.choice(len(lanes), p=weights)]
        legs = [(origin, via), (via, dest)] if via else [(origin, dest)]
        plan_days = sum(route_lookup[l].transit_days for l in legs)

        service = "LCL" if RNG.random() < 0.72 else "FCL"
        volume = round(float(RNG.uniform(1.5, 14.0)), 2) if service == "LCL" \
            else round(float(RNG.uniform(28.0, 66.0)), 2)
        weight = round(volume * float(RNG.uniform(180, 420)), 1)

        cost_per_cbm = sum(route_lookup[l].cost_per_cbm for l in legs)
        margin = float(RNG.uniform(1.28, 1.55))
        base_amount = volume * cost_per_cbm * margin
        origin_region = [p for p in PORTS if p[0] == origin][0][3]
        currency = RNG.choice(CURRENCY_BY_REGION[origin_region])
        fx_approx = {"USD": 1.0, "EUR": 1.07, "GBP": 1.26, "CNY": 0.138, "UAH": 0.024}
        amount = round(base_amount / fx_approx[currency], 2)

        etd = booked + pd.Timedelta(days=int(RNG.integers(3, 9)))
        eta = etd + pd.Timedelta(days=plan_days)

        # actuals: departure slip + transit noise + congestion episode
        atd = etd + pd.Timedelta(days=int(max(0, RNG.normal(0.6, 1.1))))
        transit_noise = RNG.normal(0.5, 1.6)
        congestion = 0
        # Rotterdam congestion: Oct 1 - Nov 20, 2025 hits anything routed via NLRTM
        via_ports = [via] if via else []
        if ("NLRTM" in via_ports or dest == "NLRTM") and \
           pd.Timestamp("2025-10-01") <= eta <= pd.Timestamp("2025-11-20"):
            congestion = int(RNG.integers(6, 16))
        actual_days = max(1, plan_days + int(round(transit_noise)) + congestion)
        ata = atd + pd.Timedelta(days=actual_days)

        if atd > SIM_END:                       # not even departed yet
            status, ata_out = ("BOOKED", None)
        elif ata > SIM_END:
            status, ata_out = ("IN_TRANSIT", None)
        else:
            status, ata_out = ("DELIVERED", ata.date())

        sid = f"SHP-{booked.year}-{i:05d}"
        shipments.append({
            "shipment_id": sid, "customer_id": cust,
            "origin_port": origin, "dest_port": dest,
            "service": service, "volume_cbm": volume, "weight_kg": weight,
            "booked_date": booked.date(), "etd": etd.date(), "eta": eta.date(),
            "atd": atd.date() if atd <= SIM_END else None,
            "ata": ata_out, "status": status,
            "freight_amount": amount, "currency": currency,
        })

        # ---- event stream along the actual journey ----
        def add(ev, t, loc):
            nonlocal eid
            events.append({"event_id": eid, "shipment_id": sid,
                           "event_type": ev, "event_time": t, "location": loc})
            eid += 1

        t = booked + pd.Timedelta(hours=int(RNG.integers(8, 18)))
        add("BOOKED", t, "ONLINE")
        t = pd.Timestamp(atd) - pd.Timedelta(days=2, hours=int(RNG.integers(0, 10)))
        if t <= SIM_END:
            add("CARGO_RECEIVED", t, origin)
        t = pd.Timestamp(atd) - pd.Timedelta(hours=int(RNG.integers(6, 20)))
        if t <= SIM_END:
            add("LOADED", t, origin)
        t = pd.Timestamp(atd) + pd.Timedelta(hours=int(RNG.integers(2, 12)))
        if t <= SIM_END:
            add("DEPARTED", t, origin)

        if via and pd.Timestamp(atd) <= SIM_END:
            leg1 = route_lookup[(origin, via)].transit_days
            t_in = pd.Timestamp(atd) + pd.Timedelta(days=leg1, hours=int(RNG.integers(0, 12)))
            dwell_days = float(RNG.gamma(2.0, 0.9))
            if via == "NLRTM" and congestion:
                dwell_days += congestion * 0.6
            t_out = t_in + pd.Timedelta(days=dwell_days)
            if t_in <= SIM_END:
                add("TRANSSHIPMENT_IN", t_in, via)
            if t_out <= SIM_END:
                add("TRANSSHIPMENT_OUT", t_out, via)

        if ata_out is not None:
            t = pd.Timestamp(ata)
            add("ARRIVED", t, dest)
            t2 = t + pd.Timedelta(days=float(RNG.gamma(1.8, 0.8)))
            if t2 <= SIM_END:
                add("CUSTOMS_CLEARED", t2, dest)
                t3 = t2 + pd.Timedelta(days=float(RNG.gamma(1.5, 0.7)))
                if t3 <= SIM_END:
                    add("DELIVERED", t3, dest)

    return pd.DataFrame(shipments), pd.DataFrame(events)


def make_invoices(shipments, customers):
    """One invoice per shipment + injected AML patterns."""
    # per-customer payment discipline
    profile = {}
    for c in customers["customer_id"]:
        r = RNG.random()
        profile[c] = "prompt" if r < 0.55 else ("slow" if r < 0.88 else "delinquent")

    rows = []
    inv_no = 1
    for s in shipments.itertuples():
        issue = pd.Timestamp(s.booked_date) + pd.Timedelta(days=int(RNG.integers(1, 5)))
        terms = int(RNG.choice([14, 30, 45], p=[0.3, 0.55, 0.15]))
        due = issue + pd.Timedelta(days=terms)
        p = profile[s.customer_id]
        if p == "prompt":
            lag = int(RNG.normal(-2, 4))
        elif p == "slow":
            lag = int(RNG.normal(12, 9))
        else:
            lag = int(RNG.normal(35, 20))
        paid = due + pd.Timedelta(days=lag)
        if paid > SIM_END or (p == "delinquent" and RNG.random() < 0.30):
            paid_out = None
        else:
            paid_out = max(paid, issue + pd.Timedelta(days=1)).date()

        rows.append({
            "invoice_id": f"INV-{issue.year}-{inv_no:05d}",
            "shipment_id": s.shipment_id, "customer_id": s.customer_id,
            "amount": s.freight_amount, "currency": s.currency,
            "issue_date": issue.date(), "due_date": due.date(),
            "paid_date": paid_out,
        })
        inv_no += 1

    df = pd.DataFrame(rows)

    # ---- AML injection 1: structuring just below a 10,000 threshold ----
    structurer = 77  # a specific customer id
    struct_ship = shipments[shipments.customer_id == structurer].head(1)
    base_date = pd.Timestamp("2025-09-10")
    sid = struct_ship["shipment_id"].iloc[0] if len(struct_ship) else shipments["shipment_id"].iloc[0]
    extra = []
    for k in range(4):
        extra.append({
            "invoice_id": f"INV-2025-{90000 + k}",
            "shipment_id": sid, "customer_id": structurer,
            "amount": round(float(RNG.uniform(9_300, 9_940)), 2),
            "currency": "USD",
            "issue_date": (base_date + pd.Timedelta(days=k * 2)).date(),
            "due_date": (base_date + pd.Timedelta(days=k * 2 + 14)).date(),
            "paid_date": (base_date + pd.Timedelta(days=k * 2 + 3)).date(),
        })

    # ---- AML injection 2: duplicate invoices (same shipment+amount, new id) ----
    dup_source = df.sample(3, random_state=11)
    for j, (_, r) in enumerate(dup_source.iterrows()):
        extra.append({
            "invoice_id": f"INV-2025-{95000 + j}",
            "shipment_id": r["shipment_id"], "customer_id": r["customer_id"],
            "amount": r["amount"], "currency": r["currency"],
            "issue_date": (pd.Timestamp(r["issue_date"]) + pd.Timedelta(days=int(RNG.integers(3, 12)))).date(),
            "due_date": (pd.Timestamp(r["due_date"]) + pd.Timedelta(days=10)).date(),
            "paid_date": None,
        })

    return pd.concat([df, pd.DataFrame(extra)], ignore_index=True)


def make_fx():
    days = pd.date_range(SIM_START, SIM_END, freq="D")
    start = {"EUR": 1.075, "GBP": 1.265, "CNY": 0.1385, "UAH": 0.0242}
    vol = {"EUR": 0.0022, "GBP": 0.0026, "CNY": 0.0009, "UAH": 0.0011}
    rows = []
    for ccy, s in start.items():
        level = s
        for d in days:
            level = max(0.001, level * (1 + float(RNG.normal(0, vol[ccy]))))
            rows.append({"rate_date": d.date(), "currency": ccy,
                         "rate_to_usd": round(level, 6)})
    # USD parity for completeness
    for d in days:
        rows.append({"rate_date": d.date(), "currency": "USD", "rate_to_usd": 1.0})
    return pd.DataFrame(rows)


def main():
    DATA_DIR.mkdir(exist_ok=True)
    ports = make_ports()
    routes = make_routes()
    customers = make_customers()
    shipments, events = make_shipments_and_events(customers, routes)
    invoices = make_invoices(shipments, customers)
    fx = make_fx()

    ports.to_csv(DATA_DIR / "ports.csv", index=False)
    routes.to_csv(DATA_DIR / "shipping_routes.csv", index=False)
    customers.to_csv(DATA_DIR / "customers.csv", index=False)
    shipments.to_csv(DATA_DIR / "shipments.csv", index=False)
    events.to_csv(DATA_DIR / "shipment_events.csv", index=False)
    invoices.to_csv(DATA_DIR / "invoices.csv", index=False)
    fx.to_csv(DATA_DIR / "fx_rates.csv", index=False)

    print(f"ports:            {len(ports):>7,}")
    print(f"shipping_routes:  {len(routes):>7,}")
    print(f"customers:        {len(customers):>7,}")
    print(f"shipments:        {len(shipments):>7,}")
    print(f"shipment_events:  {len(events):>7,}")
    print(f"invoices:         {len(invoices):>7,}")
    print(f"fx_rates:         {len(fx):>7,}")


if __name__ == "__main__":
    main()
