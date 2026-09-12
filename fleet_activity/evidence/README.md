# Execution evidence

Local validation on 11 September 2026 used Python 3.14 and Spark/Delta 4.1.0. The pipeline now has three stage notebooks. Each ran in a separate local kernel; the executed snapshots are [Bronze](01_bronze_ingestion_executed.ipynb), [Silver](02_silver_cleaning_executed.ipynb), and [Gold](03_gold_activity_executed.ipynb). Their sources match the active notebooks. The prior monolith is retained only in `archive/`.

## Results

| Check | Result |
| --- | ---: |
| Telemetry input records | 4,316 |
| Identical readings removed | 1 |
| Quarantined or held records | 22 |
| Individually rejected records | 4 |
| Records held due to day issues | 18 |
| Unassignable rejected records | 3 |
| Gold vehicle-days | 721 |
| Trusted vehicle-days | 716 |
| Untrusted vehicle-days | 3 |
| Insufficient-reading days | 1 |
| Missing-telemetry days | 1 |
| Unregistered vehicle-days | 1 |
| Weather depot-days | 60 |

Gold includes 24 × 30 registered vehicle-days plus one unregistered vehicle-day. Quarantine includes all held readings from inconsistent days, not just individually bad records. “Trusted” means the stated checks passed; it is not proof of physical accuracy.

The [run summary](run_summary.json) records input hashes, weather request parameters/fetch times, runtime and business-output hash. Real weather responses are stored under `../examples/weather/` with attribution. Fleet/telemetry are generated independently of weather.

## Verification

- The same behavioral, evidence and companion parity suite is used for this revision; current results are recorded in `notebook_split_validation.json`. The curated repository runs the same suite and a fresh offline replay in GitHub Actions.
- `FLEET_OFFLINE=1 python fleet_activity/run_notebook.py`: all three stage notebooks passed in separate kernels with real Delta writes and saved real weather inputs.
- Before the readability changes, a full rerun with the host timezone changed from UTC to America/Chicago produced identical daily and aggregate CSVs, the same 721 Gold rows, and one new Delta version: [replay proof](replay.json).
- An independent Python calculation from the exported daily CSV reconciled all nine report groups, totals, trusted denominators and means.
- The former HTML/chart report is archived and is no longer generated. The Power BI report is built and published; a later direct Databricks connection and Service on-demand refresh are recorded in [the refresh checkpoint](../power_bi/REFRESH_SETUP.md). Earlier CSV validation remains historical; the first automatic Service refresh is pending; synchronized source and post-migration row checks are recorded in the linked checkpoint.
- The malformed JSON parser is exercised by the end-to-end notebook; small transformation tests inject already-parsed fixture rows.

The [daily CSV](daily_vehicle_activity.csv) and [SQL validation CSV](activity_report.csv) come from the current successful local run. Local execution status in `output/execution_status.json` identifies the most recent runner attempt; these tracked files are a historical snapshot.

## Current stage split

On 11 September, Codex observed all three Databricks notebooks pass: Bronze 6 code cells, Silver 14, Gold 9. The final proof printed `PLATFORM_REPLAY_VALIDATION_PASSED`, matched the local business CSV hash, and checked 721 Gold rows and 22 quarantined/held rows. Gold was written at Delta version 3. Weather used saved real API responses. See `notebook_split_validation.json` for source hashes and the UI-observed result.

## Scheduled Databricks run

For the newer **12 September scheduled job run**, see [daily job review](../databricks/JOB_REVIEW.md).
All three tasks succeeded and the scheduled Gold proof matched the established
CSV hash, 721 Gold rows and 22 quarantined/held rows. Gold history showed version 7.
This was a UI-observed scheduler-triggered run; the earlier notebook snapshots
and validation JSON files remain historical records of their respective runs.

## Historical Databricks replay

The following result predates the Power BI split. Its original source is preserved byte-for-byte in `archive/databricks_before_power_bi.ipynb`. The active cloud pipeline is now split into three notebooks. Their current execution status is recorded in `notebook_split_validation.json`. This earlier replay history does not certify the split revision.

Codex observed all **24 code cells pass**, including the `%run` setup call, on Databricks Free Edition serverless (Spark 4.2.0). The final proof compared the cloud business CSV with the local CSV: the full SHA-256 matched, as did 721 Gold rows and 22 quarantine/held rows. The final run overwrote the managed Unity Catalog Gold table at version 2. The previous versions remain in Delta history. The nine-group report was displayed in the notebook.

See [recorded UI results](databricks_run.json). The private proof screenshot is not bundled in this curated repository. The original companion snapshot is in `archive/`; the unchanged `00_prepare_demo` remains in `../databricks/`. Their original source hashes are recorded in the UI evidence. A native executed notebook export was attempted but did not produce a downloadable artifact; no exported cloud notebook is claimed.

The first cloud live-weather call returned HTTP 429 and stopped before Gold/report publication. The successful cloud run is an **explicit replay of saved real weather responses**. Local live API ingestion and cloud replay are separate verified results.

## Independent review

Checkpoint 8 and its focused recheck verified the current split code, independent kernels, unchanged business results and requested cleanup. Final validation metadata was refreshed by Codex after that recheck. Claude did not run Databricks.

Detailed private review conversations and the prior development repository history are not included here. The historical validation records retain their original scope and source hashes. They are not claims that every later artifact was independently reviewed.

For the fresh repository checks and post-migration Power BI row comparison, see [publication validation](publication_validation.json) and [migration validation](../power_bi/migration_validation.json).

## Boundaries

- Databricks replay is tracked separately in [platform evidence](databricks_run.json). The cloud live API request received HTTP 429; successful cloud API ingestion is not claimed.
- SQLite is a local SQL database, not a remote JDBC source.
- UTC days are shared across telemetry and weather. Depot weather is contextual, not vehicle-route weather.
- Distance covers the observed within-day span, not overnight or unobserved travel.
- Static fleet membership is assumed for the demo period; no SCD2 or historical roster logic.
- Each Delta overwrite is atomic. Multiple table writes and CSV output are not a single transaction.
- Rebuilding proficiency and real business impact are not claimed by these execution results.

Current source hashes, execution results and review status are recorded in `notebook_split_validation.json`. Historical reviews above do not certify later revisions.
