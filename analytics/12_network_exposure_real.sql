-- ============================================================================
-- 12 · NETWORK EXPOSURE TO REAL PORT TRENDS — SYNTHETIC ⋈ REAL
-- ----------------------------------------------------------------------------
-- Business question: at which ports is OUR book of business concentrated,
-- and what does real satellite data say those ports are doing right now?
-- A port that handles a big share of our volume AND shows declining real
-- container traffic is a commercial risk (schedule slippage, blank
-- sailings); a booming port hints at congestion risk instead.
--
-- Joins our shipments (last 180 days, both legs: origin + destination)
-- against the real 90-day-vs-year-ago container-call trend from IMF
-- PortWatch (module 11's source table).
--
-- Techniques: UNION ALL leg unpivot, LEFT JOIN survives missing real data,
--             CASE-based signal classification, share-of-book window calc.
-- ============================================================================

WITH anchor AS (
    SELECT MAX(activity_date) AS d_max
    FROM port_activity_daily
),
book AS (                       -- our exposure per port, both legs
    SELECT port_code,
           SUM(n)   AS shipments_180d,
           SUM(cbm) AS cbm_180d
    FROM (
        SELECT s.origin_port AS port_code, COUNT(*) AS n, SUM(s.volume_cbm) AS cbm
        FROM shipments s
        WHERE s.booked_date > (SELECT MAX(booked_date) FROM shipments) - 180
        GROUP BY 1
        UNION ALL
        SELECT s.dest_port, COUNT(*), SUM(s.volume_cbm)
        FROM shipments s
        WHERE s.booked_date > (SELECT MAX(booked_date) FROM shipments) - 180
        GROUP BY 1
    )
    GROUP BY port_code
),
trend AS (                      -- real container-call AND tonnage trend
    SELECT
        pa.port_code,
        SUM(pa.portcalls_container)
            FILTER (WHERE pa.activity_date > a.d_max - 90)     AS calls_cur,
        SUM(pa.portcalls_container)
            FILTER (WHERE pa.activity_date >  a.d_max - 455
                      AND pa.activity_date <= a.d_max - 365)   AS calls_prev,
        SUM(pa.import_total_tons + pa.export_total_tons)
            FILTER (WHERE pa.activity_date > a.d_max - 90)     AS tons_cur,
        SUM(pa.import_total_tons + pa.export_total_tons)
            FILTER (WHERE pa.activity_date >  a.d_max - 455
                      AND pa.activity_date <= a.d_max - 365)   AS tons_prev
    FROM port_activity_daily pa
    CROSS JOIN anchor a
    GROUP BY pa.port_code
)
SELECT
    p.port_name,
    p.region,
    b.shipments_180d,
    CAST(ROUND(b.cbm_180d, 0) AS BIGINT)                       AS cbm_180d,
    ROUND(100.0 * b.cbm_180d / SUM(b.cbm_180d) OVER (), 1)     AS share_of_book_pct,
    ROUND(100.0 * (t.calls_cur - t.calls_prev)
                / NULLIF(t.calls_prev, 0), 1)                  AS real_calls_yoy_pct,
    CASE
        WHEN t.calls_cur IS NULL
          THEN 'no real data — run fetch_real_data.py'
        WHEN t.calls_prev IS NULL OR t.calls_prev = 0
          THEN 'baseline too short'
        -- sanity guard: vessel calls collapsing while tonnage holds is a
        -- satellite-feed artifact, not a real-world event — say so instead
        -- of shouting "declining traffic" (seen at Jebel Ali, 2026-06)
        WHEN (t.calls_cur - t.calls_prev) * 100.0 / t.calls_prev < -60
         AND (t.tons_cur  - t.tons_prev)  * 100.0
             / NULLIF(t.tons_prev, 0)                    > -20
          THEN '?  feed anomaly — verify source'
        WHEN (t.calls_cur - t.calls_prev) * 100.0 / t.calls_prev < -10
          THEN '!! declining traffic'
        WHEN (t.calls_cur - t.calls_prev) * 100.0 / t.calls_prev < -3
          THEN '!  softening'
        WHEN (t.calls_cur - t.calls_prev) * 100.0 / t.calls_prev > 10
          THEN '▲ surging (congestion watch)'
        ELSE 'stable'
    END                                                        AS real_world_signal
FROM book b
JOIN ports p USING (port_code)
LEFT JOIN trend t USING (port_code)
ORDER BY b.cbm_180d DESC;
