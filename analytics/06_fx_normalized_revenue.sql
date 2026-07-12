SELECT
    CASE WHEN GROUPING(p.region) = 1 THEN '── TOTAL ──'
         ELSE p.region END                                     AS region,
    CASE WHEN GROUPING(qtr) = 1 AND GROUPING(p.region) = 0
         THEN 'subtotal'
         WHEN GROUPING(qtr) = 1 THEN ''
         ELSE strftime(qtr, '%Y-Q') ||
              CAST((EXTRACT(month FROM qtr) + 2) / 3 AS INTEGER) END AS quarter,
    COUNT(i.invoice_id)                                        AS invoices,
    ROUND(SUM(i.amount * fx.rate_to_usd), 0)                   AS revenue_usd,
    ROUND(AVG(i.amount * fx.rate_to_usd), 0)                   AS avg_invoice_usd,
    COUNT(DISTINCT i.currency)                                 AS currencies_billed
FROM (
    SELECT *, date_trunc('quarter', issue_date) AS qtr
    FROM invoices
) i
ASOF JOIN fx_rates fx
    ON  fx.currency  = i.currency
    AND i.issue_date >= fx.rate_date
JOIN shipments s ON s.shipment_id = i.shipment_id
JOIN ports p     ON p.port_code   = s.origin_port
GROUP BY ROLLUP (p.region, qtr)
ORDER BY GROUPING(p.region), p.region, GROUPING(qtr), qtr;
