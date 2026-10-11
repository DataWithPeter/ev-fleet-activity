# Run the Databricks pipeline

Clone this repository into a Databricks Git folder. Use `fleet_activity/databricks` for Databricks runs; `fleet_activity/notebooks` contains the local versions. Keep these five notebooks together:

| Notebook | Reads | Writes |
| --- | --- | --- |
| `00_prepare_demo` | Generator and bundled real weather responses | Demo input files and setup helpers |
| `01_bronze_ingestion` | JSONL, SQLite and weather snapshots/API helper | `bronze_telemetry`, `bronze_fleet`, `bronze_weather` |
| `02_silver_cleaning` | The three Bronze tables | `silver_telemetry`, `quarantine_telemetry`, `silver_day_issues`, `daily_observations`, `silver_fleet`, `silver_weather` |
| `03_gold_activity` | Daily observations, Silver fleet and Silver weather | `gold_daily_vehicle_activity` and small validation exports |
| `04_gold_quality` | Saved activity, Silver and quarantine snapshot | `gold_vehicle_day_quality`, `gold_vehicle_day_issue`, `gold_record_reconciliation` |

After pushing changes from your computer to GitHub, pull them into the Databricks Git folder before running the updated notebooks. The scheduled job uses the workspace copy.

Start with **01 → 02 → 03 → 04**, using Run all in each and waiting for success before continuing. Bronze calls `%run ./00_prepare_demo` itself. You do not need to run setup twice. Silver and Gold have their own imports and read saved Delta tables, so they work in fresh notebook sessions. They do not rerun earlier layers.

All tables use `ev_telematics.fleet_activity_demo_20260910`. The `files` volume holds input files and supporting outputs. The two new handoff tables (`bronze_weather` and `silver_fleet`) make layer boundaries explicit; the Gold columns and distance calculation stay the same. Quality adds three tables to the ten existing pipeline tables.

The Gold SQL summary validates aggregate results. Gold also feeds the [Power BI report](../POWER_BI.md) and the [native Databricks SQL dashboard](dashboard/README.md).

## Reruns and failures

The demo is a full refresh with a fixed 1–30 August 2026 UTC period. Reruns overwrite this dedicated namespace. Bronze regenerates synthetic inputs through preparation; this is deliberate demo behavior, not an incremental source feed. SQLite is queried on a driver copy and copied to the volume for provenance.

Stop if a notebook fails. Fix it and rerun that layer, then all following layers in order. Never run Gold after a failed upstream run: old tables may still exist. Individual Delta overwrites are atomic; multiple table writes are not one transaction. No automatic cross-stage freshness gate is implemented in the notebooks.

The `Fleet_activity` job runs daily at 08:00 America/Chicago. The September configuration used
Bronze → Silver → Gold with All succeeded dependencies, Serverless compute,
one concurrent run and queueing. The 12 September scheduled run succeeded
and passed the Gold reference check. See [job settings and run evidence](JOB_REVIEW.md).
Avoid overlapping manual notebook runs against the same tables. A later user
screenshot showed job-level Success and Failure email enabled. The 13 September scheduled run succeeded, and its success email was received. Failure-email delivery remains untested.
The job repeats the fixed demo period. Power BI now imports Gold directly on a
separate 09:00 Central schedule. The first verified scheduled Service refresh completed on 13 September, from 09:03:03 to 09:17:55 as displayed in Refresh history. See [refresh checkpoint](../power_bi/REFRESH_SETUP.md).

Weather in Databricks is an explicit offline replay of saved real Open-Meteo responses. The local Bronze notebook also supports normal and refresh API modes. A prior cloud live request was rate-limited; no new cloud live API success is claimed.

## Validation

The original three stage notebooks are validated by the historical [split-pipeline evidence](../evidence/notebook_split_validation.json) and [scheduled job evidence](JOB_REVIEW.md).

## Expanded replay — 11 October 2026

The reviewed preparation notebook selects `expanded_august_v1` and embeds its generator and scenario assets, so it does not need a local checkout path. The local generator still defaults to the original baseline. Gold activity accepts the separately reviewed baseline and expanded reference hashes; its business calculation is unchanged. Quality runs after Gold activity succeeds.

Manual run `250966450620707` succeeded across Bronze, Silver, Gold activity and Gold quality in 4m 22s. The saved runtime evidence was verified at 05:43 UTC. It reports 10,652 Bronze records, 1,805 activity days, 1,805 quality days, 52 issues and one reconciliation row. The business hash is `748ecf0d000032ea963e16567d3d63b187014be881780d815283cba0fb30dfea`.

Whole-snapshot counts are 10,517 accepted, 19 rejected, 106 held and a residual of 10; rejected plus held equals 125 quarantined. Rejected records split into 8 linked and 11 unlinked. Gold activity's 9 `unassigned_rejects` is a different missing-key count; it excludes two outside-period rejects that are unlinked in quality reconciliation.

This manual replay is separate from the September scheduled-run evidence. It does not by itself confirm a Power BI refresh, dashboard query refresh, current schedule settings or notification delivery. See the separate [expanded web verification](../power_bi/validation_expanded_august_v1.json); it records observed values and retains interaction limitations. Keep the older baseline evidence and screenshots unchanged.
