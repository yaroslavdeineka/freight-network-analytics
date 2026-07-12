WITH anchor AS (
    SELECT MAX(activity_date) AS d_max
    FROM port_activity_daily
),
w AS (
    SELECT
        pa.port_code,
        COUNT(*) FILTER (WHERE pa.activity_date > a.d_max - 90)   AS days_cur,
        SUM(pa.portcalls_container)
            FILTER (WHERE pa.activity_date > a.d_max - 90)        AS calls_cur,
        SUM(pa.portcalls_container)
            FILTER (WHERE pa.activity_date >  a.d_max - 455
                      AND pa.activity_date <= a.d_max - 365)      AS calls_prev,
        SUM(pa.import_total_tons + pa.export_total_tons)
            FILTER (WHERE pa.activity_date > a.d_max - 90)        AS tons_cur,
        SUM(pa.import_total_tons + pa.export_total_tons)
            FILTER (WHERE pa.activity_date >  a.d_max - 455
                      AND pa.activity_date <= a.d_max - 365)      AS tons_prev
    FROM port_activity_daily pa
    CROSS JOIN anchor a
    GROUP BY pa.port_code
)
SELECT
    p.port_name,
    p.region,
    a.d_max                                                        AS data_through,
    w.days_cur                                                     AS days_observed,
    ROUND(w.calls_cur * 1.0 / NULLIF(w.days_cur, 0), 1)            AS ctr_calls_per_day,
    ROUND(100.0 * (w.calls_cur - w.calls_prev)
                / NULLIF(w.calls_prev, 0), 1)                      AS ctr_calls_yoy_pct,
    ROUND(w.tons_cur / NULLIF(w.days_cur, 0) / 1000.0, 1)          AS cargo_kt_per_day,
    ROUND(100.0 * (w.tons_cur - w.tons_prev)
                / NULLIF(w.tons_prev, 0), 1)                       AS cargo_yoy_pct
FROM w
JOIN ports p USING (port_code)
CROSS JOIN anchor a
ORDER BY cargo_yoy_pct DESC NULLS LAST;
