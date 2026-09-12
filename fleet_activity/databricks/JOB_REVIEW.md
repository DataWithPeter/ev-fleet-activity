# Daily pipeline job review

Reviewed in the signed-in Databricks UI: 12 September 2026.

Niko created `Fleet_activity_demo`. Its core configuration is correct for the
current full-refresh demo. Codex inspected the three task configurations,
schedule, concurrency, run history and the scheduled Gold task's proof output.
The daily trigger has fired successfully. A later user screenshot showed
job-level Success and Failure email enabled; delivery has not been tested.

## What the current notebooks support

The repository notebooks were inspected for this review:

- `01_bronze_ingestion` calls `%run ./00_prepare_demo`, regenerates the seeded
  synthetic inputs and overwrites the three Bronze tables.
- Preparation explicitly sets `FLEET_OFFLINE=1`; weather uses saved real
  Open-Meteo responses.
- `02_silver_cleaning` reads persisted Bronze tables and overwrites Silver
  and quality tables.
- `03_gold_activity` reads persisted Silver tables and overwrites Gold. Its
  final proof checks the established CSV hash, 721 Gold rows and 22
  quarantined/held rows.
- All stages use the fixed 1–30 August 2026 UTC reporting period.

A daily schedule therefore repeats the full-refresh demo. It does not add
new dates, implement incremental ingestion or prove a live weather fetch.
Business values should remain stable, while ingestion timestamps, run IDs
and Delta history may change. The scheduled Gold output confirmed the fixed
period, saved weather mode and unchanged business CSV hash. This review did
not export and compare every cloud source cell against the repository.

## Verified configuration

Notebook paths below are relative to Niko's Databricks user workspace folder.
All tasks use Workspace sources, not a Git checkout.

| Task | Notebook | Depends on | Run if |
| --- | --- | --- | --- |
| `Bronze_ingestion` | `fleet-activity-demo/01_bronze_ingestion` | None | Root task |
| `Silver_cleaning` | `fleet-activity-demo/02_silver_cleaning` | `Bronze_ingestion` | All succeeded |
| `Gold_activity` | `fleet-activity-demo/03_gold_activity` | `Silver_cleaning` | All succeeded |

- Schedule: Active, Scheduled, every Day at 08:00, `America/Chicago`.
  The UI shows UTC−05:00 and DST on the review date; this is a Chicago local
  time schedule, not a fixed 13:00 UTC schedule throughout the year.
- Maximum concurrent runs: 1; queue enabled.
- Compute: Serverless; performance optimized enabled. The successful run used
  Notebook Environment version 5 and reported Spark 4.2.0.
- Run as: Niko's workspace user, also the job owner. The successful run
  demonstrates the access needed for this execution; permissions were not changed.
- Retries: each task shows immediate retry, at most 3 retries (4 total attempts).
- Job parameters and task parameter lists: empty.
- Notifications at initial inspection: Gold-only task alerts. A later Niko screenshot
  showed Success and Failure email checked in Job notifications. Delivery is untested.
- No job duration/streaming thresholds are configured. A hard timeout value
  was not independently inspected; no timeout guarantee is claimed.
- Git settings and job description: not configured. Workspace edits can affect
  later runs; a run is not pinned to a repository commit.

There is no separate preparation task, which is appropriate because the
repository Bronze notebook already calls `00_prepare_demo`.

## Observed runs and output

| Run on 12 September 2026 (Chicago time) | Trigger | Result | Duration shown in Runs list |
| --- | --- | --- | --- |
| 00:05 | Manually | Succeeded | 3m 15s |
| 08:00 | By scheduler | Succeeded | 3m 6s |

The scheduled run's graph showed all three tasks succeeded: Bronze 1m 12s,
Silver 1m 8s, Gold 43s. The run detail panel displayed 3m 5s overall, while
the Runs list displayed 3m 6s; both are recorded without treating that display
difference as a failure.

The scheduled Gold notebook's final cell visibly printed:

```text
PLATFORM_REPLAY_VALIDATION_PASSED
Weather mode: saved real API snapshots; no cloud fetch claimed
Business SHA-256: 766345118556c0b8901c8fbed8998a143c7741910c9faac6daade370e532c44c
```

The executed proof cell checks 721 Gold rows and 22 quarantined/held rows
before printing the success marker. The summary displayed 4,316 Bronze rows
and the 1–30 August reporting period. Delta history showed Gold version 7 at
2026-09-12 13:02:59 UTC. This is new scheduled-run evidence; earlier local
execution snapshots and historical validation files have not been rewritten.

## Recommended follow-up

The original recommendation to add job-level failure email was addressed in
Niko's later Job notifications screenshot, with Success and Failure checked.
Codex did not change the setting, and failure delivery was not tested by
intentionally breaking the pipeline.

A short job description would help explain its purpose: "Daily full-refresh
replay of the fixed August 2026 fleet demo: Bronze → Silver → Gold. Uses saved
weather responses and validates Gold against the demo reference."

Use success dependencies so a failed upstream stage does not allow a later
stage to read tables left by an older run. Databricks documents this as
[All succeeded](https://docs.databricks.com/aws/en/jobs/run-if).
The [job configuration guide](https://docs.databricks.com/aws/en/jobs/configure-job)
describes concurrent-run controls; the [schedule guide](https://docs.databricks.com/aws/en/jobs/scheduled)
describes schedule timezones. Failure alerts can be configured through
[job notifications](https://docs.databricks.com/aws/en/jobs/notifications).

## Reporting and recovery

Power BI now imports directly from Gold and has a separate 09:00 Central
refresh schedule. A Service on-demand refresh completed on 12 September;
its first automatic execution remains unverified. The Power BI schedule is
not conditional on job success. See [refresh checkpoint](../power_bi/REFRESH_SETUP.md). The native
Databricks dashboard reads Gold when its queries refresh; dashboard refresh
must be distinguished from completion of the pipeline job.

If a stage fails, inspect its error before retrying. Repair or rerun that
stage and the downstream stages only when inputs have not changed and no
other run is writing the shared tables. Otherwise rerun the full chain.
Individual Delta writes are atomic; the entire multi-table pipeline is not
one transaction. Avoid simultaneous manual notebook runs against these
same outputs.

## Review boundaries

This is a UI-observed review, not an exported Jobs API configuration or a new
local test-suite run. A temporary Databricks List-view error was recovered by
returning to and reloading the graph; it did not change the recorded run result.
No job changes, new runs, pipeline/model edits, commit or push were made.
Workspace URLs, organization IDs and private notification addresses are
omitted from this record. Claude can review this document for alignment;
independent Claude inspection of the live job is not claimed.
