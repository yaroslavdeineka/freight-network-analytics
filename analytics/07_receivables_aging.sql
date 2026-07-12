WITH open_items AS (
    SELECT
        i.*,
        i.amount * fx.rate_to_usd                          AS amount_usd,
        date_diff('day', i.due_date, DATE '2026-06-30')    AS days_overdue
    FROM invoices i
    ASOF JOIN fx_rates fx
        ON fx.currency = i.currency AND i.issue_date >= fx.rate_date
    WHERE i.paid_date IS NULL
)
SELECT
    CASE
        WHEN days_overdue <  0  THEN '1 · Not yet due'
        WHEN days_overdue <= 30 THEN '2 · 1-30 days overdue'
        WHEN days_overdue <= 60 THEN '3 · 31-60 days overdue'
        WHEN days_overdue <= 90 THEN '4 · 61-90 days overdue'
        ELSE                         '5 · 90+ days overdue'
    END                                          AS aging_bucket,
    COUNT(*)                                     AS invoices,
    ROUND(SUM(amount_usd), 0)                    AS outstanding_usd,
    ROUND(100.0 * SUM(amount_usd)
          / SUM(SUM(amount_usd)) OVER (), 1)     AS share_pct,
    COUNT(DISTINCT customer_id)                  AS customers_affected
FROM open_items
GROUP BY 1
ORDER BY 1;
