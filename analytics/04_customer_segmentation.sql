WITH customer_activity AS (
    SELECT
        c.customer_id,
        c.customer_name,
        c.industry,
        date_diff('day', MAX(s.booked_date), DATE '2026-06-30') AS days_since_last,
        COUNT(*)                                                AS shipment_count,
        ROUND(SUM(s.freight_amount *
              COALESCE(fx.rate_to_usd, 1.0)), 0)                AS revenue_usd
    FROM customers c
    JOIN shipments s  ON s.customer_id = c.customer_id
    ASOF LEFT JOIN fx_rates fx
        ON fx.currency = s.currency
       AND s.booked_date >= fx.rate_date
    GROUP BY 1, 2, 3
),
rfm AS (
    SELECT *,
        NTILE(5) OVER (ORDER BY days_since_last DESC) AS r_score,  
        NTILE(5) OVER (ORDER BY shipment_count)       AS f_score, 
        NTILE(5) OVER (ORDER BY revenue_usd)          AS m_score  
    FROM customer_activity
),
segmented AS (
    SELECT *,
        CASE
            WHEN r_score >= 4 AND f_score >= 4 AND m_score >= 4 THEN 'Champion'
            WHEN r_score >= 4 AND f_score >= 3                  THEN 'Loyal'
            WHEN r_score <= 2 AND m_score >= 4                  THEN 'At Risk (high value)'
            WHEN r_score <= 2 AND f_score <= 2                  THEN 'Dormant'
            WHEN r_score >= 4 AND f_score <= 2                  THEN 'New / Developing'
            ELSE 'Core'
        END AS segment,
        ROUND(100.0 * SUM(revenue_usd) OVER (ORDER BY revenue_usd DESC)
              / SUM(revenue_usd) OVER (), 1) AS cumulative_revenue_pct
    FROM rfm
)
SELECT
    segment,
    COUNT(*)                                                   AS customers,
    SUM(shipment_count)                                        AS shipments,
    ROUND(SUM(revenue_usd), 0)                                 AS revenue_usd,
    ROUND(100.0 * SUM(revenue_usd) / SUM(SUM(revenue_usd)) OVER (), 1)
                                                               AS revenue_share_pct,
    COUNT(*) FILTER (WHERE cumulative_revenue_pct <= 80)       AS class_a_customers,
    COUNT(*) FILTER (WHERE cumulative_revenue_pct >  80
                       AND cumulative_revenue_pct <= 95)       AS class_b_customers,
    COUNT(*) FILTER (WHERE cumulative_revenue_pct >  95)       AS class_c_customers
FROM segmented
GROUP BY segment
ORDER BY revenue_usd DESC;
