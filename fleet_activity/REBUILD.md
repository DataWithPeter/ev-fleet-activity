# Rebuild one layer at a time

Use these notebooks as your map:

- `01_bronze_ingestion`: read the three sources and save Bronze.
- `02_silver_cleaning`: read Bronze, apply quality decisions and save Silver.
- `03_gold_activity`: read Silver, join the sources and save Gold for Power BI.

Each starts with imports and table reads. A DataFrame from another notebook is not automatically available; `spark.table("catalog.schema.table")` loads the persisted result. The local equivalent is `spark.read.format("delta").load(path)`. These reads are the handoff between layers. Bronze calls `00_prepare_demo` in Databricks; Silver and Gold do not.


Use a blank notebook and the supplied source data. Keep these prompts open; hide the completed notebook until you need a hint. Syntax references are allowed. Stop after one checkpoint if that fills your session.

The map: **JSONL → Bronze → checked readings → daily distance → SQL roster → weather → Gold → separate Power BI report.**

## What you own first

Rebuild the data reading, quality decisions, SQL window, joins and Gold table. You can run the provided setup. You do not need to recreate the data generator, API retry/cache machinery, test runner, hashes, CSV export on your first pass. Learn what those parts do when troubleshooting them.

## 1. Read three fields

Write a schema for vehicle ID, timestamp text and odometer. Add a corrupt-record field and use PERMISSIVE mode. Save/read a Delta table, then count the records and inspect one broken row.

Check: 4,316 rows, including one malformed record. Explain why the timestamp starts as text. If schema syntax is new, practise a two-field schema on unrelated data first.

## 2. Label a bad row

Normalize IDs, parse the timestamp, then use a `when` chain for one rejection reason. Check in this order: malformed JSON, missing vehicle, invalid timestamp, outside the reporting period, invalid odometer. Stop at the first failure. Null means no failure found.

Check: four rejected records in the demo. If one record has both a missing ID and bad timestamp, predict its reason before running. Remove identical business readings; expect one duplicate removed.

## 3. Compare readings in SQL

First group by vehicle and timestamp to find conflicts after deduplication. Leave those timestamps out of the ordered comparison. Register the remaining readings as a SQL view. Use `LAG` per vehicle and UTC day to compare odometers.

Check on paper: 100 → 90 → 100 and 100 → 900 → 110. Both days are inconsistent. We cannot identify the wrong reading just from the falling pair. After excluding conflicts, the demo has one decreasing-odometer day.

Then list problem days: a decrease, a conflict, or an assignable rejected record. Keep accepted readings only from days without issues. Expect three problem days. Quarantine assembly is a later exercise; initially explain its two groups: four rejected records and eighteen held readings.

## 4. Make the daily distance table

Group by vehicle and UTC date. Keep reading count and first/last times. Only calculate max minus min when there are at least two readings and no known issue. Retain a day even if all its readings were rejected.

Check: two equal valid readings give zero; one reading gives null; 50000 → 0 → 10 gives null. Explain why overnight travel is outside this metric.

## 5. Add the SQL roster

Query the SQLite roster. Build the 30 dates using a loop, then the expected vehicle × date grid. Join observations to it. Also retain any unknown vehicles seen in telemetry.

Check: 24 × 30 roster-days plus one unknown vehicle-day = 721 rows. One day has missing telemetry. Explain why an inner join would hide it.

## 6. Turn weather arrays into rows

Open one saved weather response and print its `daily` object. Read its dates, temperatures and precipitation. Use an index loop to append one row per day. Then add the second depot. Study `parse_daily` in `weather.py` as a reference after attempting it.

Check: 60 depot-days. A null precipitation value stays null. Join on depot and date, not date alone. Add one duplicate Chicago weather row to the 720 roster-day example: predict 732 rows, then write the check that stops that multiplication.

Later, request a short period for one depot with `requests.get`. Check the response status before reading JSON. Explain how the supplied helper retries temporary failures and reuses saved responses. API failures must stop the pipeline, not become null weather.

## 7. Explain and troubleshoot

Write the depot/model/weather report with SQL. Show trusted, missing and unreliable counts beside averages. Predict the effect of changing one reading, run, and compare.

Explain the three sources, the Gold grain, join keys, day-quality policy and one limitation. Rerun from saved inputs and compare the business results; the supplied appendix can compare hashes for you. Deliberately remove an offline snapshot and find the error. Old reports may survive a failed run; the notebook is not one transaction.

Record what you rebuilt without the solution and what still needed a hint. Completed execution is not evidence of your personal proficiency. This is an AI-assisted reference implementation to practise from; claim ownership through work you can demonstrate.

## 8. Build a separate Power BI report
After rebuilding the pipeline, connect Power BI to Gold. Start with one table visual, compare its counts and distances with the notebook SQL check, then add charts and filters. See [POWER_BI.md](POWER_BI.md). HTML, CSS and Matplotlib are outside this project scope.
