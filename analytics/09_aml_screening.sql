WITH near_threshold AS (
    SELECT
        i.*,
        COUNT(*) OVER w                         AS cluster_size,
        SUM(i.amount) OVER w                    AS cluster_amount
    FROM invoices i
    WHERE i.currency = 'USD'
      AND i.amount BETWEEN 9_000 AND 9_999.99   
    WINDOW w AS (
        PARTITION BY i.customer_id
        ORDER BY i.issue_date
        RANGE BETWEEN INTERVAL 14 DAY PRECEDING
                  AND INTERVAL 14 DAY FOLLOWING
    )
),
structuring_alerts AS (
    SELECT
        'A · STRUCTURING'                        AS screen,
        c.customer_name,
        n.invoice_id,
        n.issue_date,
        n.amount,
        n.cluster_size                           AS evidence_count,
        ROUND(n.cluster_amount, 2)               AS evidence_amount
    FROM near_threshold n
    JOIN customers c USING (customer_id)
    WHERE n.cluster_size >= 3
),

dupes AS (
    SELECT
        i.*,
        COUNT(*) OVER (PARTITION BY i.shipment_id, i.amount) AS copies
    FROM invoices i
),
duplicate_alerts AS (
    SELECT
        'B · DUPLICATE BILLING'                  AS screen,
        c.customer_name,
        d.invoice_id,
        d.issue_date,
        d.amount,
        d.copies                                 AS evidence_count,
        d.amount * d.copies                      AS evidence_amount
    FROM dupes d
    JOIN customers c USING (customer_id)
    WHERE d.copies > 1
)

SELECT * FROM structuring_alerts
UNION ALL
SELECT * FROM duplicate_alerts
ORDER BY screen, customer_name, issue_date;
