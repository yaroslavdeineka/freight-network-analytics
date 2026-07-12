-- ============================================================================
-- 07b · PAYMENT DISCIPLINE & DSO — WHO ACTUALLY PAYS?
-- ----------------------------------------------------------------------------
-- Business question: which customers drive the collection risk, how late do
-- they habitually pay, and what is DSO — company-wide and per account?
--
-- DSO here is the simple method: outstanding AR ÷ credit sales of the
-- trailing 365 days × 365. The '── ALL CUSTOMERS ──' line is the company
-- total, produced in the same pass with GROUPING SETS; below it, the 15
-- accounts holding the most unpaid cash.
--
-- Techniques: ASOF JOIN USD normalisation, GROUPING SETS for an inline
--             total row, FILTER-ed conditional aggregation, data-derived
--             as-of anchor (same as module 07 — the two always agree).
-- ============================================================================

WITH as_of AS (
    SELECT MAX(issue_date) AS today FROM invoices
),
usd AS (
    SELECT
        i.*,
        i.amount * fx.rate_to_usd AS amount_usd
    FROM invoices i
    ASOF JOIN fx_rates fx
        ON fx.currency = i.currency AND i.issue_date >= fx.rate_date
)
SELECT
    CASE WHEN GROUPING(u.customer_id) = 1 THEN '── ALL CUSTOMERS ──'
         ELSE MAX(c.customer_name) END                              AS customer,
    COUNT(*)                                                        AS invoices,
    COUNT(u.paid_date)                                              AS paid,
    -- payment habit: how many days past due the paid invoices landed
    ROUND(AVG(date_diff('day', u.due_date, u.paid_date))
          FILTER (WHERE u.paid_date IS NOT NULL), 1)                AS avg_days_late,
    ROUND(100.0 * COUNT(*) FILTER (WHERE u.paid_date > u.due_date)
          / NULLIF(COUNT(u.paid_date), 0), 1)                       AS paid_late_pct,
    CAST(ROUND(SUM(u.amount_usd)
          FILTER (WHERE u.paid_date IS NULL), 0) AS BIGINT)         AS outstanding_usd,
    CAST(ROUND(SUM(u.amount_usd)
          FILTER (WHERE u.paid_date IS NULL
                    AND u.due_date < a.today - 90), 0) AS BIGINT)   AS overdue_90d_usd,
    -- DSO = AR / trailing-365d credit sales × 365
    ROUND(365.0 * SUM(u.amount_usd) FILTER (WHERE u.paid_date IS NULL)
          / NULLIF(SUM(u.amount_usd)
                   FILTER (WHERE u.issue_date > a.today - 365), 0), 0) AS dso_days
FROM usd u
JOIN customers c USING (customer_id)
CROSS JOIN as_of a
GROUP BY GROUPING SETS ((u.customer_id), ())
HAVING SUM(u.amount_usd) FILTER (WHERE u.paid_date IS NULL) > 0
ORDER BY GROUPING(u.customer_id) DESC, outstanding_usd DESC
LIMIT 16;   -- company total + 15 riskiest accounts
