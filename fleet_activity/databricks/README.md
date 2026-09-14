# Run the Databricks pipeline

Keep these four notebooks together in `fleet-activity-demo`:

| Notebook | Reads | Writes |
| --- | --- | --- |
| `00_prepare_demo` | Generator and bundled real weather responses | Demo input files and setup helpers |
| `01_bronze_ingestion` | JSONL, SQLite and weather snapshots/API helper | `bronze_telemetry`, `bronze_fleet`, `bronze_weather` |
| `02_silver_cleaning` | The three Bronze tables | `silver_telemetry`, `quarantine_telemetry`, `silver_day_issues`, `daily_observations`, `silver_fleet`, `silver_weather` |
| `03_gold_activity` | Daily observations, Silver fleet and Silver weather | `gold_daily_vehicle_activity` and small validation exports |

Start with **01 → 02 → 03**, using Run all in each and waiting for success before continuing. Bronze calls `%run ./00_prepare_demo` itself. You do not need to run setup twice. Silver and Gold have their own imports and read saved Delta tables, so they work in fresh notebook sessions. They do not rerun earlier layers.

All tables use `ev_telematics.fleet_activity_demo_20260910`. The `files` volume holds input files and supporting outputs. The two new handoff tables (`bronze_weather` and `silver_fleet`) make layer boundaries explicit; the Gold columns and distance calculation stay the same. The schema now has ten pipeline tables.

The Gold SQL summary validates aggregate results. Gold also feeds the [Power BI report](../POWER_BI.md) and the [native Databricks SQL dashboard](dashboard/README.md).

## Reruns and failures

The demo is a full refresh with a fixed 1–30 August 2026 UTC period. Reruns overwrite this dedicated namespace. Bronze regenerates synthetic inputs through preparation; this is deliberate demo behavior, not an incremental source feed. SQLite is queried on a driver copy and copied to the volume for provenance.

Stop if a notebook fails. Fix it and rerun that layer, then all following layers in order. Never run Gold after a failed upstream run: old tables may still exist. Individual Delta overwrites are atomic; multiple table writes are not one transaction. No automatic cross-stage freshness gate is implemented in the notebooks.

The `Fleet_activity_demo` job runs daily at 08:00 America/Chicago. It uses
Bronze → Silver → Gold with All succeeded dependencies, Serverless compute,
one concurrent run and queueing. The 12 September scheduled run succeeded
and passed the Gold reference check. See [job settings and run evidence](JOB_REVIEW.md).
Avoid overlapping manual notebook runs against the same tables. A later user
screenshot showed job-level Success and Failure email enabled. The 13 September scheduled run succeeded, and its success email was received. Failure-email delivery remains untested.
The job repeats the fixed demo period. Power BI now imports Gold directly on a
separate 09:00 Central schedule. The first verified scheduled Service refresh completed on 13 September, from 09:03:03 to 09:17:55 as displayed in Refresh history. See [refresh checkpoint](../power_bi/REFRESH_SETUP.md).

Weather in Databricks is an explicit offline replay of saved real Open-Meteo responses. The local Bronze notebook also supports normal and refresh API modes. A prior cloud live request was rate-limited; no new cloud live API success is claimed.

## History

The old `fleet_activity_databricks_replay` is superseded. Historical source and execution records live under `evidence/archive/`; they do not certify these new notebooks. Current validation is recorded in `evidence/notebook_split_validation.json` after testing.
