WITH monthly AS (
    SELECT
        date_trunc('month', s.booked_date)                        AS month,
        COUNT(*)                                                  AS shipments,
        ROUND(SUM(s.volume_cbm), 1)                               AS total_cbm,
        COUNT(DISTINCT s.customer_id)                             AS active_customers,
        ROUND(100.0 * AVG(
            CASE WHEN s.ata IS NOT NULL
                 THEN CASE WHEN s.ata <= s.eta + INTERVAL 2 DAY THEN 1 ELSE 0 END
            END), 1)                                              AS on_time_pct,
        ROUND(AVG(CASE WHEN s.ata IS NOT NULL
                       THEN date_diff('day', s.atd, s.ata) END), 1) AS avg_transit_days
    FROM shipments s
    GROUP BY 1
)
SELECT
    strftime(month, '%Y-%m')                                       AS month,
    shipments,
    shipments - LAG(shipments) OVER (ORDER BY month)               AS mom_change,
    ROUND(100.0 * (shipments - LAG(shipments) OVER (ORDER BY month))
          / NULLIF(LAG(shipments) OVER (ORDER BY month), 0), 1)    AS mom_growth_pct,
    total_cbm,
    SUM(total_cbm) OVER (ORDER BY month)                           AS cumulative_cbm,
    ROUND(AVG(shipments) OVER (
        ORDER BY month ROWS BETWEEN 2 PRECEDING AND CURRENT ROW), 1) AS shipments_3mo_avg,
    active_customers,
    on_time_pct,
    avg_transit_days
FROM monthly
ORDER BY month;
