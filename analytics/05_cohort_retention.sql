WITH cohorts AS (
    SELECT
        customer_id,
        date_trunc('quarter', onboarded_date) AS cohort_q
    FROM customers
),
activity AS (
    SELECT DISTINCT
        s.customer_id,
        date_trunc('quarter', s.booked_date) AS active_q
    FROM shipments s
),
matrix AS (
    SELECT
        c.cohort_q,
        date_diff('quarter', c.cohort_q, a.active_q) AS quarters_since,
        COUNT(DISTINCT a.customer_id)                AS active_customers
    FROM cohorts c
    JOIN activity a USING (customer_id)
    WHERE a.active_q >= c.cohort_q
    GROUP BY 1, 2
),
cohort_size AS (
    SELECT cohort_q, COUNT(*) AS cohort_n
    FROM cohorts GROUP BY 1
)
SELECT
    strftime(m.cohort_q, '%Y-Q') ||
        CAST((EXTRACT(month FROM m.cohort_q) + 2) / 3 AS INTEGER) AS cohort,
    cs.cohort_n                                                   AS size,
    MAX(CASE WHEN quarters_since = 0 THEN active_customers END)   AS q0,
    ROUND(100.0 * MAX(CASE WHEN quarters_since = 1 THEN active_customers END) / cs.cohort_n, 0) AS q1_pct,
    ROUND(100.0 * MAX(CASE WHEN quarters_since = 2 THEN active_customers END) / cs.cohort_n, 0) AS q2_pct,
    ROUND(100.0 * MAX(CASE WHEN quarters_since = 3 THEN active_customers END) / cs.cohort_n, 0) AS q3_pct,
    ROUND(100.0 * MAX(CASE WHEN quarters_since = 4 THEN active_customers END) / cs.cohort_n, 0) AS q4_pct,
    ROUND(100.0 * MAX(CASE WHEN quarters_since = 5 THEN active_customers END) / cs.cohort_n, 0) AS q5_pct,
    ROUND(100.0 * MAX(CASE WHEN quarters_since = 6 THEN active_customers END) / cs.cohort_n, 0) AS q6_pct
FROM matrix m
JOIN cohort_size cs USING (cohort_q)
GROUP BY m.cohort_q, cs.cohort_n
ORDER BY m.cohort_q;
