"""Checkpoint B: execute notebook cells against saved demo and adversarial fixtures."""
from datetime import date
from pathlib import Path

import nbformat
import pytest
from pyspark.sql import functions as F
from pyspark.sql.types import LongType

ROOT = Path(__file__).parents[1]
CELLS = {c.metadata["tags"][0]: c.source for c in
         nbformat.read(ROOT / "notebooks/04_gold_quality.ipynb", as_version=4).cells
         if c.cell_type == "code"}
DAY = date(2026, 8, 1)
DICTIONARY = {
    "conflicting_timestamp": ("Conflicting timestamp", 10),
    "odometer_decreased": ("Odometer decreased", 20),
    "rejected_reading_in_day": ("Rejected reading in day", 30),
    "missing_telemetry": ("Missing telemetry", 40),
    "insufficient_readings": ("Insufficient readings", 50),
    "unregistered_vehicle": ("Vehicle absent from roster", 60),
}


def run(context, tags=None):
    for tag in tags or [t for t in CELLS if t not in ("setup", "publish")]:
        exec(compile(CELLS[tag], f"04:{tag}", "exec", optimize=2), context)
    return context


@pytest.fixture(scope="module")
def demo(spark):
    context = dict(spark=spark, F=F)
    for variable, table in [("bronze", "bronze_telemetry"), ("accepted", "silver_telemetry"),
                            ("quarantine", "quarantine_telemetry"), ("day_issues", "silver_day_issues"),
                            ("gold", "gold_daily_vehicle_activity")]:
        context[variable] = spark.read.format("delta").load(str(ROOT / "output/delta" / table))
    return run(context)


def fixture(spark, status="trusted", registered=True, reasons=()):
    return dict(spark=spark, F=F,
        gold=spark.createDataFrame([("A", DAY, "D1", "Depot", "Model", registered, status, 2)],
            "vehicle_id string, event_date date, depot_id string, depot_name string, model string, "
            "registered_vehicle boolean, distance_status string, reading_count long"),
        bronze=spark.createDataFrame([(1,), (2,), (3,), (4,)], "record int"),
        accepted=spark.createDataFrame([], "vehicle_id string, event_date date"),
        quarantine=spark.createDataFrame([], "vehicle_id string, event_date date, quarantine_scope string"),
        day_issues=spark.createDataFrame([("A", DAY, list(reasons))] if reasons else [],
            "vehicle_id string, event_date date, reasons array<string>"))


def test_Q01_Q02_day_domain_and_status_parity(demo):
    q, g = demo["quality"], demo["gold"]
    assert q.count() == q.select("vehicle_day_key").distinct().count() == 721
    assert q.select("vehicle_id", "event_date").subtract(g.select("vehicle_id", "event_date")).count() == 0
    assert g.select("vehicle_id", "event_date").subtract(q.select("vehicle_id", "event_date")).count() == 0
    copied = demo["day_columns"]
    assert q.select(*copied).subtract(g.select(*copied)).count() == 0
    assert q.filter(F.col("vehicle_id").isNull() | (F.trim("vehicle_id") == "") |
                    F.col("event_date").isNull()).count() == 0
    assert {r.distance_status: r["count"] for r in q.groupBy("distance_status").count().collect()} == {
        "trusted": 716, "untrusted": 3, "insufficient_readings": 1, "missing_telemetry": 1}
    assert "reconciliation_key" not in q.columns + demo["issues"].columns + demo["reconciliation"].columns
    assert all(r.vehicle_day_key == f"{r.vehicle_id}|{r.event_date.isoformat()}" for r in q.collect())


def test_Q04_native_counts_and_six_fixtures(demo):
    q = demo["quality"]
    for col in ["accepted_reading_count", "rejected_record_count", "held_reading_count", "issue_count"]:
        assert isinstance(q.schema[col].dataType, LongType)
        assert q.filter(F.col(col).isNull() | (F.col(col) < 0)).count() == 0
    for vehicle, day, status, accepted, rejected, held, readings in [
        ("EV002", 3, "untrusted", 0, 1, 5, 5), ("EV003", 4, "untrusted", 0, 0, 6, 6),
        ("EV004", 5, "untrusted", 0, 0, 7, 5), ("EV006", 7, "missing_telemetry", 0, 0, 0, 0),
        ("EV007", 8, "insufficient_readings", 1, 0, 0, 1), ("UNKNOWN", 1, "trusted", 2, 0, 0, 2)]:
        row = q.filter((F.col("vehicle_id") == vehicle) & (F.col("event_date") == date(2026, 8, day))).first()
        assert (row.distance_status, row.accepted_reading_count, row.rejected_record_count,
                row.held_reading_count, row.reading_count) == (status, accepted, rejected, held, readings)
        assert row.issue_count == 1
        assert row.primary_issue == {"EV002": "rejected_reading_in_day", "EV003": "odometer_decreased",
            "EV004": "conflicting_timestamp", "EV006": "missing_telemetry",
            "EV007": "insufficient_readings", "UNKNOWN": "unregistered_vehicle"}[vehicle]


def test_Q05_dictionary_unique_issues_and_no_orphans(demo):
    i = demo["issues"]
    assert i.count() == i.select("vehicle_day_key").distinct().count() == 6
    assert i.select("vehicle_day_key", "issue_code").distinct().count() == 6
    assert i.join(demo["quality"], "vehicle_day_key", "left_anti").count() == 0
    assert {r.issue_code: (r.issue_label, r.primary_priority) for r in i.collect()} == DICTIONARY
    assert {r.issue_code: (r.issue_label, r.primary_priority) for r in demo["issue_dictionary"].collect()} == DICTIONARY


def test_Q07_reporting_impact_and_clean_days(demo):
    q = demo["quality"]
    assert q.filter(F.col("distance_status") != "trusted").count() == 5
    assert q.filter(F.col("issue_count") > 0).count() == 6
    unknown = q.filter(F.col("vehicle_id") == "UNKNOWN").first()
    assert unknown.distance_status == "trusted" and unknown.primary_issue == "unregistered_vehicle"
    clean = q.filter((F.col("distance_status") == "trusted") & F.col("registered_vehicle"))
    assert clean.filter((F.col("issue_count") != 0) | F.col("primary_issue").isNotNull()).count() == 0
    dedup = q.filter((F.col("vehicle_id") == "EV005") & (F.col("event_date") == date(2026, 8, 6))).first()
    assert dedup.accepted_reading_count == 6 and dedup.issue_count == 0


def test_Q08_Q14_multi_issue_duplicate_reasons_and_fanout(spark):
    c = fixture(spark, "untrusted", reasons=["odometer_decreased", "conflicting_timestamp", "conflicting_timestamp"])
    c["day_issues"] = c["day_issues"].unionByName(c["day_issues"])
    c["quarantine"] = spark.createDataFrame([("A", DAY, "day_hold")] * 4,
        "vehicle_id string, event_date date, quarantine_scope string")
    run(c)
    row = c["quality"].first()
    assert c["quality"].count() == 1 and c["issues"].count() == 2
    assert row.issue_count == 2 and row.primary_issue == "conflicting_timestamp"
    assert row.held_reading_count == 4 and row.reading_count == 2


def test_Q09_combined_registry_reporting_is_one_affected_day(spark):
    c = run(fixture(spark, "untrusted", False, ["odometer_decreased"]))
    assert c["quality"].filter(F.col("distance_status") != "trusted").count() == 1
    assert c["issues"].count() == 2
    assert c["quality"].first().primary_issue == "odometer_decreased"


@pytest.mark.parametrize("status,reasons,error", [
    ("untrusted", [], "missing Silver reason"), ("unexpected", [], "Unknown distance status"),
    (None, [], "Unknown distance status"), ("untrusted", ["unknown_reason"], "Unknown issue reason"),
    ("untrusted", [None], "Unknown issue reason"),
    ("untrusted", ["missing_telemetry"], "Unsupported Silver issue reason")])
def test_Q10_invalid_status_or_reason_fails(spark, status, reasons, error):
    with pytest.raises(ValueError, match=error):
        run(fixture(spark, status, reasons=reasons))


def test_Q10_clean_day_and_empty_outputs(spark):
    c = run(fixture(spark))
    row = c["quality"].first()
    assert row.issue_count == 0 and row.primary_issue is None
    assert c["issues"].count() == 0


@pytest.mark.parametrize("scope", ["other", None])
def test_Q11_Q12_unknown_scope_fails(spark, scope):
    c = fixture(spark)
    c["quarantine"] = spark.createDataFrame([("A", DAY, scope)],
        "vehicle_id string, event_date date, quarantine_scope string")
    with pytest.raises(ValueError, match="Unsupported quarantine scope"):
        run(c)


def test_Q11_Q12_incomplete_and_unmatched_rejects_unlinked_only(spark):
    c = fixture(spark)
    c["quarantine"] = spark.createDataFrame([
        ("A", DAY, "record"), (None, DAY, "record"), ("A", None, "record"), ("OTHER", DAY, "record")],
        "vehicle_id string, event_date date, quarantine_scope string")
    run(c)
    r = c["reconciliation"].first()
    assert (r.rejected_record_count, r.linked_reject_count, r.unlinked_reject_count) == (4, 1, 3)
    assert c["quality"].first().rejected_record_count == 1
    assert c["quality"].count() == 1  # No invented day, and trusted keys can link rejects.


@pytest.mark.parametrize("source", ["accepted", "held", "issues"])
def test_Q11_Q12_orphan_sources_fail(spark, source):
    c = fixture(spark)
    if source == "accepted":
        c["accepted"] = spark.createDataFrame([("OTHER", DAY)], "vehicle_id string, event_date date")
    elif source == "held":
        c["quarantine"] = spark.createDataFrame([("OTHER", DAY, "day_hold")],
            "vehicle_id string, event_date date, quarantine_scope string")
    else:
        c["day_issues"] = spark.createDataFrame([("OTHER", DAY, ["odometer_decreased"])],
            "vehicle_id string, event_date date, reasons array<string>")
    with pytest.raises(ValueError, match="Orphan"):
        run(c)


def test_Q13_independent_sums_and_snapshot_counts(demo):
    q = demo["quality"]
    r = demo["reconciliation"].first()
    assert demo["reconciliation"].count() == 1
    assert tuple(r) == (4316, 4293, 4, 18, 22, 1, 3, 1)
    assert q.agg(F.sum("accepted_reading_count")).first()[0] == demo["accepted"].count()
    assert q.agg(F.sum("held_reading_count")).first()[0] == demo["held"].count()
    assert q.agg(F.sum("rejected_record_count")).first()[0] == r.linked_reject_count
    assert r.linked_reject_count + r.unlinked_reject_count == demo["rejected"].count()
    assert demo["rejected"].count() + demo["held"].count() == demo["quarantine"].count()


@pytest.mark.parametrize("invalid", ["duplicate", "null_vehicle", "blank_vehicle", "null_date"])
def test_Q14_invalid_gold_keys_fail(spark, invalid):
    c = fixture(spark)
    if invalid == "duplicate":
        c["gold"] = c["gold"].unionByName(c["gold"])
    elif invalid == "null_vehicle":
        c["gold"] = c["gold"].withColumn("vehicle_id", F.lit(None).cast("string"))
    elif invalid == "blank_vehicle":
        c["gold"] = c["gold"].withColumn("vehicle_id", F.lit("   "))
    else:
        c["gold"] = c["gold"].withColumn("event_date", F.lit(None).cast("date"))
    with pytest.raises(ValueError, match="Gold vehicle-day key"):
        run(c)


def test_Q14_three_source_counts_do_not_multiply(spark):
    c = fixture(spark, "untrusted", reasons=["rejected_reading_in_day"])
    c["accepted"] = spark.createDataFrame([("A", DAY)] * 2, "vehicle_id string, event_date date")
    c["quarantine"] = spark.createDataFrame([("A", DAY, "record"), ("A", DAY, "day_hold")],
        "vehicle_id string, event_date date, quarantine_scope string")
    run(c)
    row = c["quality"].first()
    assert c["quality"].count() == 1
    assert (row.accepted_reading_count, row.rejected_record_count, row.held_reading_count) == (2, 1, 1)


def test_invalid_snapshot_does_not_reach_publish(spark, tmp_path):
    c = fixture(spark, "untrusted")
    c["output_dir"] = tmp_path
    with pytest.raises(ValueError, match="missing Silver reason"):
        run(c, [t for t in CELLS if t != "setup"])
    assert not (tmp_path / "delta").exists()
