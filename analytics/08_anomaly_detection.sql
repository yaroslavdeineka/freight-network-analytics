WITH lane_stats AS (
    SELECT
        s.shipment_id,
        s.customer_id,
        s.origin_port || ' → ' || s.dest_port                    AS lane,
        date_diff('day', s.atd, s.ata)                           AS actual_days,
        AVG(date_diff('day', s.atd, s.ata))
            OVER (PARTITION BY s.origin_port, s.dest_port)       AS lane_avg,
        STDDEV_SAMP(date_diff('day', s.atd, s.ata))
            OVER (PARTITION BY s.origin_port, s.dest_port)       AS lane_std,
        COUNT(*)
            OVER (PARTITION BY s.origin_port, s.dest_port)       AS lane_n,
        s.eta,
        s.ata
    FROM shipments s
    WHERE s.status = 'DELIVERED'
)
SELECT
    shipment_id,
    lane,
    actual_days,
    ROUND(lane_avg, 1)                                    AS lane_avg_days,
    ROUND((actual_days - lane_avg) / NULLIF(lane_std, 0), 2) AS z_score,
    date_diff('day', eta, ata)                            AS days_late_vs_eta,
    CASE
        WHEN (actual_days - lane_avg) / NULLIF(lane_std, 0) > 3 THEN '🔴 investigate'
        ELSE '🟡 monitor'
    END                                                   AS severity
FROM lane_stats
WHERE lane_n >= 30                                       
  AND (actual_days - lane_avg) / NULLIF(lane_std, 0) > 2.0
ORDER BY z_score DESC
LIMIT 20;
