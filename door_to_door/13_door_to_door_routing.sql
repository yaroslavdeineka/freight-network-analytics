WITH RECURSIVE
params AS (
    SELECT 1.5 AS usd_per_cbm_day        
),
port_risk (port_code, risk_usd_cbm) AS (
    VALUES ('UAODS', 12.0)               -- war-risk insurance surcharge, Odesa
),
anchor AS (
    SELECT MAX(activity_date) AS d_max FROM port_activity_daily
),
trend AS (
    SELECT pa.port_code,
           SUM(pa.portcalls_container)
               FILTER (WHERE pa.activity_date > a.d_max - 90)      AS calls_cur,
           SUM(pa.portcalls_container)
               FILTER (WHERE pa.activity_date >  a.d_max - 455
                         AND pa.activity_date <= a.d_max - 365)    AS calls_prev
    FROM port_activity_daily pa
    CROSS JOIN anchor a
    GROUP BY pa.port_code
),
congestion AS (                          
    SELECT port_code,
           CASE WHEN calls_prev IS NULL OR calls_prev = 0        THEN 0
                WHEN (calls_cur - calls_prev) * 100.0 / calls_prev < -10 THEN 3
                WHEN (calls_cur - calls_prev) * 100.0 / calls_prev < -3  THEN 1
                ELSE 0 END AS penalty_days
    FROM trend
),
paths AS (                             
    SELECT r.origin_port                                    AS origin,
           r.dest_port                                      AS gateway,
           r.origin_port || ' → ' || r.dest_port            AS path,
           r.transit_days + 2                               AS days, 
           r.cost_per_cbm                                   AS cost,
           1                                                AS legs
    FROM shipping_routes r
    WHERE r.origin_port IN (SELECT origin_port FROM route_requests)

    UNION ALL

    SELECT p.origin,
           r.dest_port,
           p.path || ' → ' || r.dest_port,
           p.days + r.transit_days + 3,
           p.cost + r.cost_per_cbm,
           p.legs + 1
    FROM paths p
    JOIN shipping_routes r ON r.origin_port = p.gateway
    WHERE p.legs < 3
      AND NOT contains(p.path, r.dest_port)                
),
options AS (
    SELECT q.origin_port,
           q.dest_city,
           p.path,
           p.gateway,
           il.mode                                          AS inland_mode,
           p.days                                           AS sea_days,
           il.transit_days                                  AS inland_days,
           COALESCE(c.penalty_days, 0)                      AS congestion_days,
           p.cost                                           AS sea_usd_cbm,
           il.cost_per_cbm                                  AS inland_usd_cbm,
           COALESCE(pr.risk_usd_cbm, 0)                     AS risk_usd_cbm
    FROM route_requests q
    JOIN paths p        ON p.origin = q.origin_port
    JOIN inland_legs il ON il.from_port = p.gateway
                       AND il.dest_city = q.dest_city
    LEFT JOIN port_risk  pr ON pr.port_code = p.gateway
    LEFT JOIN congestion c  ON c.port_code  = p.gateway
),
scored AS (
    SELECT *,
           sea_days + inland_days + congestion_days          AS total_days,
           sea_usd_cbm + inland_usd_cbm + risk_usd_cbm       AS total_usd_cbm,
           sea_usd_cbm + inland_usd_cbm + risk_usd_cbm
             + (sea_days + inland_days + congestion_days)
               * (SELECT usd_per_cbm_day FROM params)        AS score
    FROM options
)
SELECT
    origin_port || ' → ' || dest_city                        AS request,
    ROW_NUMBER() OVER (PARTITION BY origin_port, dest_city
                       ORDER BY score)                       AS rank,
    path || ' ⇒ ' || dest_city                               AS route,
    gateway,
    inland_mode,
    total_days,
    ROUND(total_usd_cbm, 1)                                  AS usd_per_cbm,
    congestion_days                                          AS real_data_buffer_d,
    ROUND(score, 1)                                          AS score
FROM scored
QUALIFY rank <= 3
ORDER BY origin_port, dest_city, rank;
