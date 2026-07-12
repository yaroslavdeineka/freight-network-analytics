WITH RECURSIVE paths AS (

    SELECT
        r.origin_port,
        r.dest_port,
        [r.origin_port, r.dest_port]          AS path,      
        [r.mode]                              AS modes,
        r.transit_days                        AS total_days,
        r.cost_per_cbm                        AS total_cost,
        1                                     AS legs
    FROM shipping_routes r
    WHERE r.origin_port = 'UAODS'

    UNION ALL

    SELECT
        p.origin_port,
        r.dest_port,
        list_append(p.path, r.dest_port),
        list_append(p.modes, r.mode),
        p.total_days + r.transit_days,
        p.total_cost + r.cost_per_cbm,
        p.legs + 1
    FROM paths p
    JOIN shipping_routes r
      ON r.origin_port = p.dest_port
    WHERE p.legs < 3
      AND NOT list_contains(p.path, r.dest_port)
)
SELECT
    list_aggr(path, 'string_agg', ' → ')      AS routing,
    legs,
    list_aggr(modes, 'string_agg', ' / ')     AS modes,
    total_days                                AS transit_days,
    ROUND(total_cost, 2)                      AS cost_per_cbm_usd,
    RANK() OVER (ORDER BY total_cost)         AS cost_rank,
    RANK() OVER (ORDER BY total_days)         AS speed_rank
FROM paths
WHERE dest_port = 'CNSHA'
ORDER BY total_cost
LIMIT 12;
