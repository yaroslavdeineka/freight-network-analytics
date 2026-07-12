-- ============================================================================
-- FREIGHT NETWORK ANALYTICS — SCHEMA
-- ----------------------------------------------------------------------------
-- Data model for an LCL/FCL freight-forwarding operation:
--   * ports                — nodes of the shipping network (UN/LOCODE codes)
--   * shipping_routes      — directed edges of the network (sea / rail legs)
--   * customers            — the client book
--   * shipments            — one row per consignment
--   * shipment_events      — the operational event stream (milestones)
--   * invoices             — billing, multi-currency, with payment behaviour
--   * fx_rates             — daily FX fixings used to normalise revenue to USD
-- ============================================================================

CREATE TABLE ports (
    port_code   VARCHAR(5) PRIMARY KEY,          -- UN/LOCODE, e.g. 'NLRTM'
    port_name   VARCHAR NOT NULL,
    country     VARCHAR NOT NULL,
    region      VARCHAR NOT NULL,                 -- Europe / Asia / MEA / Americas
    latitude    DOUBLE,
    longitude   DOUBLE
);

CREATE TABLE shipping_routes (
    route_id     INTEGER PRIMARY KEY,
    origin_port  VARCHAR NOT NULL REFERENCES ports(port_code),
    dest_port    VARCHAR NOT NULL REFERENCES ports(port_code),
    mode         VARCHAR NOT NULL CHECK (mode IN ('sea', 'rail')),
    transit_days INTEGER NOT NULL CHECK (transit_days > 0),
    cost_per_cbm DECIMAL(8,2) NOT NULL CHECK (cost_per_cbm > 0)
);

CREATE TABLE customers (
    customer_id      INTEGER PRIMARY KEY,
    customer_name    VARCHAR NOT NULL,
    country          VARCHAR NOT NULL,
    industry         VARCHAR NOT NULL,
    onboarded_date   DATE NOT NULL,
    credit_limit_usd DECIMAL(12,2) NOT NULL
);

CREATE TABLE shipments (
    shipment_id    VARCHAR PRIMARY KEY,           -- 'SHP-2025-00421'
    customer_id    INTEGER NOT NULL REFERENCES customers(customer_id),
    origin_port    VARCHAR NOT NULL REFERENCES ports(port_code),
    dest_port      VARCHAR NOT NULL REFERENCES ports(port_code),
    service        VARCHAR NOT NULL CHECK (service IN ('LCL', 'FCL')),
    volume_cbm     DECIMAL(8,2) NOT NULL,
    weight_kg      DECIMAL(10,1) NOT NULL,
    booked_date    DATE NOT NULL,
    etd            DATE NOT NULL,                 -- estimated departure
    eta            DATE NOT NULL,                 -- estimated arrival
    atd            DATE,                          -- actual departure (NULL = not departed)
    ata            DATE,                          -- actual arrival   (NULL = in transit)
    status         VARCHAR NOT NULL,
    freight_amount DECIMAL(12,2) NOT NULL,
    currency       VARCHAR(3) NOT NULL
);

CREATE TABLE shipment_events (
    event_id    INTEGER PRIMARY KEY,
    shipment_id VARCHAR NOT NULL REFERENCES shipments(shipment_id),
    event_type  VARCHAR NOT NULL,                 -- BOOKED, LOADED, DEPARTED, ...
    event_time  TIMESTAMP NOT NULL,
    location    VARCHAR NOT NULL                  -- port code or 'ONLINE'
);

CREATE TABLE invoices (
    invoice_id  VARCHAR PRIMARY KEY,              -- 'INV-2025-01042'
    shipment_id VARCHAR NOT NULL REFERENCES shipments(shipment_id),
    customer_id INTEGER NOT NULL REFERENCES customers(customer_id),
    amount      DECIMAL(12,2) NOT NULL,
    currency    VARCHAR(3) NOT NULL,
    issue_date  DATE NOT NULL,
    due_date    DATE NOT NULL,
    paid_date   DATE                              -- NULL = outstanding
);

CREATE TABLE fx_rates (
    rate_date   DATE NOT NULL,
    currency    VARCHAR(3) NOT NULL,
    rate_to_usd DECIMAL(10,6) NOT NULL,
    PRIMARY KEY (rate_date, currency)
);

-- REAL data: daily satellite-AIS port activity from IMF PortWatch
-- (portwatch.imf.org). Populated from data/real/port_activity_daily.csv,
-- which is refreshed by fetch_real_data.py. Tonnages are metric tons.
CREATE TABLE port_activity_daily (
    activity_date         DATE NOT NULL,
    port_code             VARCHAR NOT NULL REFERENCES ports(port_code),
    portwatch_id          VARCHAR NOT NULL,     -- e.g. 'port1114'
    portwatch_name        VARCHAR,
    portcalls_container   INTEGER,
    portcalls_total       INTEGER,
    import_container_tons BIGINT,
    import_total_tons     BIGINT,
    export_container_tons BIGINT,
    export_total_tons     BIGINT,
    PRIMARY KEY (activity_date, port_code)
);

-- REAL data: daily transit counts through maritime chokepoints (Suez,
-- Bosporus, Bab el-Mandeb, ...) from IMF PortWatch, cached in
-- data/real/chokepoint_transits_daily.csv by fetch_real_data.py.
CREATE TABLE chokepoints (
    chokepoint_code VARCHAR PRIMARY KEY,          -- e.g. 'SUEZ'
    chokepoint_name VARCHAR NOT NULL,
    portwatch_id    VARCHAR NOT NULL              -- e.g. 'chokepoint1'
);

INSERT INTO chokepoints VALUES
    ('SUEZ',   'Suez Canal',           'chokepoint1'),
    ('BOSPOR', 'Bosporus Strait',      'chokepoint3'),
    ('BABMND', 'Bab el-Mandeb Strait', 'chokepoint4'),
    ('MALACC', 'Malacca Strait',       'chokepoint5'),
    ('HORMUZ', 'Strait of Hormuz',     'chokepoint6'),
    ('GIBRAL', 'Gibraltar Strait',     'chokepoint8'),
    ('DOVER',  'Dover Strait',         'chokepoint9'),
    ('ORESUN', 'Oresund Strait',       'chokepoint10');

-- Which chokepoints a shipment on each trade lane sails through.
-- Reference data derived from standard liner routings (e.g. Shanghai →
-- Rotterdam = Malacca + Bab el-Mandeb + Suez + Gibraltar + Dover).
-- Transpacific and transatlantic lanes cross none of the tracked straits.
-- (no FK to ports: this reference data is inserted before ports are loaded;
--  referential integrity is asserted by the data-quality suite instead)
CREATE TABLE lane_chokepoints (
    origin_port     VARCHAR NOT NULL,
    dest_port       VARCHAR NOT NULL,
    chokepoint_code VARCHAR NOT NULL REFERENCES chokepoints(chokepoint_code),
    PRIMARY KEY (origin_port, dest_port, chokepoint_code)
);

INSERT INTO lane_chokepoints VALUES
    -- Asia → North Europe (via Singapore hub, Suez routing)
    ('CNSHA','NLRTM','MALACC'), ('CNSHA','NLRTM','BABMND'), ('CNSHA','NLRTM','SUEZ'), ('CNSHA','NLRTM','GIBRAL'), ('CNSHA','NLRTM','DOVER'),
    ('CNSZX','DEHAM','MALACC'), ('CNSZX','DEHAM','BABMND'), ('CNSZX','DEHAM','SUEZ'), ('CNSZX','DEHAM','GIBRAL'), ('CNSZX','DEHAM','DOVER'),
    ('CNSHA','GBFXT','MALACC'), ('CNSHA','GBFXT','BABMND'), ('CNSHA','GBFXT','SUEZ'), ('CNSHA','GBFXT','GIBRAL'), ('CNSHA','GBFXT','DOVER'),
    ('KRPUS','NLRTM','MALACC'), ('KRPUS','NLRTM','BABMND'), ('KRPUS','NLRTM','SUEZ'), ('KRPUS','NLRTM','GIBRAL'), ('KRPUS','NLRTM','DOVER'),
    -- Black Sea ↔ Asia / North Europe
    ('UAODS','CNSHA','BOSPOR'), ('UAODS','CNSHA','SUEZ'), ('UAODS','CNSHA','BABMND'), ('UAODS','CNSHA','MALACC'),
    ('UAODS','NLRTM','BOSPOR'), ('UAODS','NLRTM','GIBRAL'), ('UAODS','NLRTM','DOVER'),
    ('UAODS','DEHAM','ORESUN'),          -- overland to Gdansk, feeder onward
    ('AEJEA','UAODS','HORMUZ'), ('AEJEA','UAODS','BABMND'), ('AEJEA','UAODS','SUEZ'), ('AEJEA','UAODS','BOSPOR'),
    -- Med / Gulf / India → North Europe
    ('TRMER','DEHAM','GIBRAL'), ('TRMER','DEHAM','DOVER'),
    ('INNSA','NLRTM','HORMUZ'), ('INNSA','NLRTM','BABMND'), ('INNSA','NLRTM','SUEZ'), ('INNSA','NLRTM','GIBRAL'), ('INNSA','NLRTM','DOVER'),
    ('EGALY','PLGDN','GIBRAL'), ('EGALY','PLGDN','DOVER'), ('EGALY','PLGDN','ORESUN'),
    -- North Europe → US East Coast (through the Channel)
    ('NLRTM','USNYC','DOVER');
    -- CNSHA→USLGB, SGSIN→USLGB (transpacific): no tracked chokepoint

CREATE TABLE chokepoint_transits_daily (
    transit_date       DATE NOT NULL,
    chokepoint_code    VARCHAR NOT NULL REFERENCES chokepoints(chokepoint_code),
    n_container        INTEGER,                   -- container-vessel transits
    n_cargo            INTEGER,                   -- all cargo vessels
    n_total            INTEGER,                   -- incl. tankers
    capacity_container BIGINT,                    -- container capacity, tons
    PRIMARY KEY (transit_date, chokepoint_code)
);

-- Helpful indexes for the analytical workload
CREATE INDEX idx_shipments_customer ON shipments(customer_id);
CREATE INDEX idx_shipments_booked   ON shipments(booked_date);
CREATE INDEX idx_events_shipment    ON shipment_events(shipment_id, event_time);
CREATE INDEX idx_invoices_customer  ON invoices(customer_id);
