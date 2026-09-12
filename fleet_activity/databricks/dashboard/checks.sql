-- Run against the live Gold table before publishing either reporting tool.
-- Blank unreliable distances must stay blank, not become zero.
SELECT
    COUNT(*) AS vehicle_days,
    COUNT(CASE WHEN distance_status = 'trusted' THEN 1 END) AS trusted_days,
    COUNT(CASE WHEN distance_status <> 'trusted' THEN 1 END) AS attention_days,
    SUM(CASE WHEN distance_status = 'trusted' THEN observed_distance_km END)
        AS distance_km,
    AVG(CASE
        WHEN distance_status = 'trusted' AND observed_distance_km > 0
        THEN observed_distance_km
    END) AS km_per_driving_day,
    COUNT(CASE
        WHEN distance_status = 'trusted' AND observed_distance_km = 0 THEN 1
    END) AS idle_days,
    COUNT(CASE
        WHEN distance_status <> 'trusted' OR registered_vehicle = false THEN 1
    END) AS review_rows
FROM ev_telematics.fleet_activity_demo_20260910.gold_daily_vehicle_activity;

SELECT
    depot_name,
    COUNT(*) AS vehicle_days,
    SUM(CASE WHEN distance_status = 'trusted' THEN observed_distance_km END)
        AS distance_km
FROM ev_telematics.fleet_activity_demo_20260910.gold_daily_vehicle_activity
GROUP BY depot_name
ORDER BY depot_name;
