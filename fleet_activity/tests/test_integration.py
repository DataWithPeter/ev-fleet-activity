from datetime import date, datetime, timezone
from pathlib import Path

import nbformat
import pytest
from pyspark.sql import functions as F


def test_join_coverage_unknown_weather_and_report_denominators(spark, tmp_path):
    day = date(2026, 8, 1)
    fleet = spark.createDataFrame([
        ("A", "Model A", "D1", "Depot 1", 1.0, 1.0),
        ("B", "Model A", "D1", "Depot 1", 1.0, 1.0),
        ("C", "Model B", "D2", "Depot 2", 2.0, 2.0),
    ], "vehicle_id string, model string, depot_id string, depot_name string, latitude double, longitude double")
    daily = spark.createDataFrame([
        ("A", day, 2, datetime(2026, 8, 1, 8, tzinfo=timezone.utc), datetime(2026, 8, 1, 10, tzinfo=timezone.utc), "trusted", 10.0),
        ("B", day, 2, None, None, "untrusted", None),
        ("NEW", day, 2, None, None, "trusted", 7.0),
    ], "vehicle_id string, event_date date, reading_count long, first_reading timestamp, last_reading timestamp, distance_status string, observed_distance_km double")
    weather = spark.createDataFrame([
        ("D1", day, 20.0, None), ("D1", date(2026, 8, 2), 20.0, 0.0),
        ("D2", day, None, 2.0), ("D2", date(2026, 8, 2), 20.0, 0.0),
    ], "depot_id string, event_date date, temperature_c double, precipitation_mm double")
    notebook = nbformat.read(Path(__file__).parents[1] / "notebooks/03_gold_activity.ipynb", as_version=4)
    cells = {cell.metadata['tags'][0]: cell.source for cell in notebook.cells if cell.cell_type == 'code'}
    context = dict(spark=spark, F=F, fleet=fleet, daily=daily, weather=weather,
                   start_date=day, end_date=date(2026, 8, 2), output_dir=tmp_path)
    for tag in ["report_dates", "fleet_join", "gold", "report", "export"]:
        exec(compile(cells[tag], f"notebook:{tag}", "exec"), context)
    import csv
    exported = list(csv.DictReader((tmp_path / "daily_vehicle_activity.csv").open()))
    assert next(row for row in exported if row["vehicle_id"] == "A" and row["event_date"] == "2026-08-01")["first_reading"] == "2026-08-01T08:00:00Z"
    assert b"\r\n" not in (tmp_path / "daily_vehicle_activity.csv").read_bytes()
    gold = context["gold"]
    assert gold.count() == 7  # Six roster-days, plus one unknown vehicle-day.
    assert gold.filter("distance_status = 'missing_telemetry'").count() == 4
    unknown = gold.filter("vehicle_id = 'NEW'").first()
    assert unknown.depot_name == "Unknown depot" and unknown.observed_distance_km == 7.0
    assert unknown.weather_condition == "Unknown" and not unknown.registered_vehicle
    group = context["activity_report"].filter("depot_name = 'Depot 1' AND weather_condition = 'Unknown'").first()
    assert group.vehicle_days == 2 and group.trusted_vehicle_days == 1
    assert group.mean_observed_distance_km == 10.0 and group.untrusted_days == 1
    dry = context["activity_report"].filter("depot_name = 'Depot 1' AND weather_condition = 'Dry'").first()
    assert dry.mean_observed_distance_km is None  # Missing telemetry is not a zero.
    # A duplicated weather key must stop before overwriting Gold.
    context["weather"] = weather.unionByName(weather.limit(1))
    with pytest.raises(ValueError, match="multiplied"):
        exec(compile(cells["gold"], "notebook:gold", "exec", optimize=2), context)
    stored = spark.read.format("delta").load(str(tmp_path / "delta" / "gold_daily_vehicle_activity"))
    assert stored.count() == 7
