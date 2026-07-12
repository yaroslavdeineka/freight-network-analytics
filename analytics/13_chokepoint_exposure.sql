-- ============================================================================
-- 13 · CHOKEPOINT EXPOSURE — HOW MUCH OF OUR BOOK SAILS THROUGH EACH STRAIT?
-- ----------------------------------------------------------------------------
-- Business question: what share of our cargo depends on Suez, Bab el-Mandeb,
-- the Bosporus, Malacca...? And what is REALLY happening at each strait right
-- now, measured from orbit? A forwarder whose book is 60% Suez-routed needs
-- to know the day Red Sea transits start falling — before carriers announce
-- Cape re-routings and surcharges.
--
-- Sources: our shipments (last 180 days) mapped to straits via the
-- lane_chokepoints reference table, joined against REAL daily transit counts
-- from IMF PortWatch (Daily_Chokepoints_Data, satellite AIS), cached by
-- fetch_real_data.py. Trend = most recent 90 days vs the same window a year
-- earlier.
--
-- NOTE: shares do not sum to 100% — one Shanghai→Rotterdam box crosses four
-- straits, and transpacific/transatlantic lanes cross none.
--
-- Techniques: many-to-many exposure join, FILTER-ed sliding windows over
--             live data, NULLIF-protected YoY, signal classification with
--             a data-gap guard (a satellite feed can glitch; the SQL says so
--             instead of shouting "collapse").
-- ============================================================================

WITH anchor AS (
    SELECT MAX(transit_date) AS d_max
    FROM chokepoint_transits_daily
),
book AS (                        -- our lanes, last 180 days of bookings
    SELECT
        s.origin_port,
        s.dest_port,
        COUNT(*)          AS shipments,
        SUM(s.volume_cbm) AS cbm
    FROM shipments s
    WHERE s.booked_date > (SELECT MAX(booked_date) FROM shipments) - 180
    GROUP BY 1, 2
),
book_total AS (
    SELECT SUM(cbm) AS cbm_total FROM book
),
exposure AS (                    -- lanes → straits (many-to-many)
    SELECT
        lc.chokepoint_code,
        COUNT(DISTINCT lc.origin_port || '→' || lc.dest_port) AS lanes,
        SUM(b.shipments)                                      AS shipments_180d,
        SUM(b.cbm)                                            AS cbm_180d
    FROM book b
    JOIN lane_chokepoints lc USING (origin_port, dest_port)
    GROUP BY 1
),
trend AS (                       -- real container transits, 90d vs year ago
    SELECT
        t.chokepoint_code,
        COUNT(*) FILTER (WHERE t.transit_date > a.d_max - 90)  AS days_cur,
        SUM(t.n_container)
            FILTER (WHERE t.transit_date > a.d_max - 90)       AS cur,
        SUM(t.n_container)
            FILTER (WHERE t.transit_date >  a.d_max - 455
                      AND t.transit_date <= a.d_max - 365)     AS prev
    FROM chokepoint_transits_daily t
    CROSS JOIN anchor a
    GROUP BY 1
)
SELECT
    c.chokepoint_name                                          AS chokepoint,
    e.lanes,
    e.shipments_180d,
    CAST(ROUND(e.cbm_180d, 0) AS BIGINT)                       AS cbm_180d,
    ROUND(100.0 * e.cbm_180d / bt.cbm_total, 1)                AS share_of_book_pct,
    ROUND(t.cur * 1.0 / NULLIF(t.days_cur, 0), 1)              AS transits_per_day,
    ROUND(100.0 * (t.cur - t.prev) / NULLIF(t.prev, 0), 1)     AS transits_yoy_pct,
    CASE
        WHEN t.cur IS NULL
            THEN 'no real data — run fetch_real_data.py'
        WHEN t.prev IS NULL OR t.prev = 0
            THEN 'baseline too short'
        WHEN t.days_cur < 60
            THEN 'data gap — verify feed'
        WHEN (t.cur - t.prev) * 100.0 / t.prev < -25
            THEN '!! transits collapsing — re-route risk'
        WHEN (t.cur - t.prev) * 100.0 / t.prev < -8
            THEN '!  transits falling'
        WHEN (t.cur - t.prev) * 100.0 / t.prev >  8
            THEN '▲ transits rising'
        ELSE 'stable'
    END                                                        AS real_world_signal
FROM exposure e
JOIN chokepoints c  USING (chokepoint_code)
LEFT JOIN trend t   USING (chokepoint_code)
CROSS JOIN book_total bt
ORDER BY e.cbm_180d DESC;
