WITH ordered_events AS (
    SELECT
        shipment_id,
        event_type,
        location,
        event_time,
        LAG(event_type) OVER w  AS prev_event,
        LAG(event_time) OVER w  AS prev_time
    FROM shipment_events
    WINDOW w AS (PARTITION BY shipment_id ORDER BY event_time)
),
stage_durations AS (
    SELECT
        prev_event || ' → ' || event_type                       AS stage,
        location,
        date_diff('hour', prev_time, event_time) / 24.0         AS days_in_stage
    FROM ordered_events
    WHERE prev_event IS NOT NULL
      AND date_diff('hour', prev_time, event_time) >= 0
)
SELECT
    stage,
    location,
    COUNT(*)                                        AS observations,
    ROUND(MEDIAN(days_in_stage), 2)                 AS median_days,
    ROUND(quantile_cont(days_in_stage, 0.90), 2)    AS p90_days,
    ROUND(MAX(days_in_stage), 1)                    AS worst_case_days,
    ROUND(quantile_cont(days_in_stage, 0.90)
          / NULLIF(MEDIAN(days_in_stage), 0), 1)    AS p90_to_median_ratio
FROM stage_durations
GROUP BY stage, location
HAVING COUNT(*) >= 40
ORDER BY p90_days DESC
LIMIT 15;
