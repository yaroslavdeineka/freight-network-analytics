
CREATE TABLE cities (
    city     VARCHAR PRIMARY KEY,
    country  VARCHAR NOT NULL,
    latitude  DOUBLE,
    longitude DOUBLE
);

INSERT INTO cities VALUES
    ('Poltava',  'Ukraine', 49.59, 34.55),
    ('Kyiv',     'Ukraine', 50.45, 30.52),
    ('Kharkiv',  'Ukraine', 49.99, 36.23),
    ('Lviv',     'Ukraine', 49.84, 24.03),
    ('Warsaw',   'Poland',  52.23, 21.01);

CREATE TABLE inland_legs (
    from_port    VARCHAR NOT NULL,          
    dest_city    VARCHAR NOT NULL,         
    mode         VARCHAR NOT NULL CHECK (mode IN ('truck', 'rail')),
    distance_km  INTEGER NOT NULL,
    transit_days INTEGER NOT NULL,          
    cost_per_cbm DECIMAL(8,2) NOT NULL,     
    note         VARCHAR
);

CREATE TABLE route_requests (
    origin_port VARCHAR NOT NULL,
    dest_city   VARCHAR NOT NULL
);

INSERT INTO route_requests VALUES
    ('CNSHA', 'Poltava'),
    ('CNSZX', 'Poltava'),
    ('CNSHA', 'Kyiv');
