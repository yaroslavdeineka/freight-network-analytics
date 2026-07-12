-- ============================================================================
-- 10 · DATA QUALITY SUITE — TRUST, BUT VERIFY
-- ----------------------------------------------------------------------------
-- Before anyone believes the dashboards above, the data itself has to pass
-- inspection. Each check below returns its own violation count; the suite
-- reads like a test report. In production these would gate the pipeline
-- (fail the load if any critical check > 0).
--
-- Techniques: assertion-style UNION ALL suite, anti-joins for referential
--             checks, EXISTS for orphan detection, temporal sanity checks.
-- ============================================================================

SELECT * FROM (

    SELECT '01 · Shipments with ATA before ATD (time travel)' AS check_name,
           'critical' AS severity,
           COUNT(*)   AS violations
    FROM shipments WHERE ata IS NOT NULL AND ata < atd

    UNION ALL
    SELECT '02 · Delivered shipments missing arrival date', 'critical', COUNT(*)
    FROM shipments WHERE status = 'DELIVERED' AND ata IS NULL

    UNION ALL
    SELECT '03 · Orphan events (no parent shipment)', 'critical', COUNT(*)
    FROM shipment_events e
    WHERE NOT EXISTS (SELECT 1 FROM shipments s WHERE s.shipment_id = e.shipment_id)

    UNION ALL
    SELECT '04 · Orphan invoices (no parent shipment)', 'critical', COUNT(*)
    FROM invoices i
    WHERE NOT EXISTS (SELECT 1 FROM shipments s WHERE s.shipment_id = i.shipment_id)

    UNION ALL
    SELECT '05 · Invoices paid before they were issued', 'critical', COUNT(*)
    FROM invoices WHERE paid_date IS NOT NULL AND paid_date < issue_date

    UNION ALL
    SELECT '06 · Shipments referencing unknown ports', 'critical', COUNT(*)
    FROM shipments s
    LEFT JOIN ports po ON po.port_code = s.origin_port
    LEFT JOIN ports pd ON pd.port_code = s.dest_port
    WHERE po.port_code IS NULL OR pd.port_code IS NULL

    UNION ALL
    SELECT '07 · Non-positive volumes or amounts', 'critical', COUNT(*)
    FROM shipments WHERE volume_cbm <= 0 OR freight_amount <= 0

    UNION ALL
    SELECT '08 · Currency codes without an FX fixing', 'warning', COUNT(*)
    FROM (
        SELECT DISTINCT i.currency FROM invoices i
        WHERE NOT EXISTS (SELECT 1 FROM fx_rates f WHERE f.currency = i.currency)
    )

    UNION ALL
    SELECT '09 · Shipments billed more than once (review)', 'warning', COUNT(*)
    FROM (
        SELECT shipment_id FROM invoices
        GROUP BY shipment_id HAVING COUNT(*) > 1
    )

    UNION ALL
    SELECT '10 · Bookings dated before customer onboarding', 'warning', COUNT(*)
    FROM shipments s JOIN customers c USING (customer_id)
    WHERE s.booked_date < c.onboarded_date

    UNION ALL
    -- lane_chokepoints carries no FK to ports (loaded before them),
    -- so its referential integrity is asserted here instead
    SELECT '11 · Chokepoint lanes referencing unknown ports', 'critical', COUNT(*)
    FROM lane_chokepoints lc
    LEFT JOIN ports po ON po.port_code = lc.origin_port
    LEFT JOIN ports pd ON pd.port_code = lc.dest_port
    WHERE po.port_code IS NULL OR pd.port_code IS NULL

) checks
ORDER BY severity, check_name;
