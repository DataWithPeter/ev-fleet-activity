"""Exercise the actual notebook cells with small, independently specified cases."""

from datetime import date, datetime, timezone
from pathlib import Path

import nbformat
import pytest
from delta import configure_spark_with_delta_pip
from pyspark.sql import SparkSession, Window, functions as F




@pytest.fixture(scope="module")
def telemetry_result(spark, tmp_path_factory):
    tmp_path = tmp_path_factory.mktemp("telemetry")
    # A dip/rebound and a spike/recovery must both invalidate the whole day.
    cases = {
        "CLEAN": [100.0, 110.0, 125.0],
        "STILL": [100.0, 100.0],
        "DIP": [100.0, 90.0, 100.0],
        "SPIKE": [100.0, 900.0, 110.0],
        "RESET": [50000.0, 0.0, 10.0],
        "ONE": [100.0],
        "NEGATIVE": [100.0, -1.0, 110.0],
        "MISSING": [100.0, None, 110.0],
        "INFINITY": [100.0, float("inf"), 110.0],
        "NAN": [100.0, float("nan"), 110.0],
        "BADONLY": [-1.0],
    }
    rows = [(vehicle, f"2026-08-01T{8 + i:02}:00:00Z", value, None, "fixture.jsonl")
            for vehicle, values in cases.items() for i, value in enumerate(values)]
    rows.extend([
        ("CLEAN", "2026-08-01T08:00:00Z", 100.0, None, "duplicate.jsonl"),
        ("CONFLICT", "2026-08-01T08:00:00Z", 100.0, None, "fixture.jsonl"),
        ("CONFLICT", "2026-08-01T08:00:00Z", 150.0, None, "fixture.jsonl"),
        ("OVERNIGHT", "2026-08-01T23:00:00Z", 100.0, None, "fixture.jsonl"),
        ("OVERNIGHT", "2026-08-02T08:00:00Z", 150.0, None, "fixture.jsonl"),
        ("OVERNIGHT", "2026-08-02T09:00:00Z", 160.0, None, "fixture.jsonl"),
        ("BADTIME", "not-a-time", 1.0, None, "fixture.jsonl"),
        (None, None, None, "broken json", "fixture.jsonl"),
        ("FUTURE", "2027-01-01T08:00:00Z", 1.0, None, "fixture.jsonl"),
        (None, "not-a-time", -1.0, None, "multiple-errors.jsonl"),
    ])
    bronze = spark.createDataFrame(rows, "vehicle_id string, event_timestamp string, odometer_km double, _corrupt_record string, source_file string")
    context = dict(spark=spark, F=F, Window=Window, bronze=bronze, output_dir=tmp_path,
                   start_date=date(2026, 8, 1), end_date=date(2026, 8, 30),
                   )
    notebook = nbformat.read(Path(__file__).parents[1] / "notebooks/02_silver_cleaning.ipynb", as_version=4)
    for cell in notebook.cells:
        if cell.cell_type == "code" and set(cell.metadata.get("tags", [])) & {
            "parse", "validate", "deduplicate", "conflicts", "sequence", "day_issues",
            "accepted", "quarantine", "daily", "save_telemetry"
        }:
            exec(compile(cell.source, "fleet_activity.ipynb", "exec"), context)
    results = {(r.vehicle_id, str(r.event_date)): r for r in context["daily"].collect()}
    return context, results


@pytest.mark.parametrize("vehicle,expected_status,expected_distance", [
    ("CLEAN", "trusted", 25.0), ("STILL", "trusted", 0.0),
    ("ONE", "insufficient_readings", None),
    *[(vehicle, "untrusted", None) for vehicle in
      ["DIP", "SPIKE", "RESET", "NEGATIVE", "MISSING", "INFINITY", "NAN", "BADONLY", "CONFLICT"]],
])
def test_day_distance(telemetry_result, vehicle, expected_status, expected_distance):
    _, results = telemetry_result
    result = results[vehicle, "2026-08-01"]
    assert result.distance_status == expected_status
    assert result.observed_distance_km == expected_distance


def test_boundaries_and_duplicate(telemetry_result):
    context, results = telemetry_result
    assert results["OVERNIGHT", "2026-08-01"].observed_distance_km is None
    assert results["OVERNIGHT", "2026-08-02"].observed_distance_km == 10.0
    assert all("2026-08-01" <= day <= "2026-08-30" for _, day in results)
    assert context["exact_duplicates_removed"] == 1


def test_silver_excludes_all_untrusted_days(telemetry_result):
    context, _ = telemetry_result
    assert context["accepted"].join(context["day_issues"], ["vehicle_id", "event_date"], "inner").count() == 0
    spike_rows = context["quarantine"].filter("vehicle_id = 'SPIKE'").collect()
    assert len(spike_rows) == 3  # Hold the entire inconsistent sequence, not just its final reading.
    assert all("odometer_decreased" in row.reasons and row.quarantine_scope == "day_hold" for row in spike_rows)
    reasons = {reason for row in context["quarantine"].select("reasons").collect() for reason in row.reasons}
    assert {"malformed_json", "invalid_timestamp", "outside_report_period", "invalid_odometer", "conflicting_timestamp", "odometer_decreased"} <= reasons


def test_reject_reason_uses_first_failure(telemetry_result):
    context, _ = telemetry_result
    record = context["row_quarantine"].filter("source_file = 'multiple-errors.jsonl'").first()
    assert record.reasons == ["missing_vehicle"]
