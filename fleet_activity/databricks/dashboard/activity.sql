-- One row per vehicle per UTC day. This query does not change Gold.
-- The dashboard filters these rows before calculating its totals.
SELECT
    event_date,
    vehicle_id,
    depot_name,
    model,
    weather_condition,
    registered_vehicle,
    distance_status,
    observed_distance_km,
    reading_count,
    CASE
        WHEN distance_status = 'trusted' THEN observed_distance_km
    END AS trusted_distance_km,
    CASE
        WHEN distance_status = 'trusted' AND observed_distance_km > 0
        THEN observed_distance_km
    END AS driving_distance_km,
    CASE WHEN distance_status = 'trusted' THEN 1 ELSE 0 END AS trusted_day,
    CASE
        WHEN distance_status <> 'trusted' THEN NULL
        WHEN observed_distance_km = 0 THEN 1
        ELSE 0
    END AS idle_day,
    CASE WHEN distance_status <> 'trusted' THEN 1 ELSE 0 END AS attention_day,
    CASE
        WHEN distance_status <> 'trusted' THEN distance_status
        WHEN registered_vehicle = false THEN 'not_in_fleet_roster'
    END AS review_reason
FROM ev_telematics.fleet_activity_demo_20260910.gold_daily_vehicle_activity
