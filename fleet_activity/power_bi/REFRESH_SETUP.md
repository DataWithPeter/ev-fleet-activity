# Databricks to Power BI refresh checkpoint

Status: 13 September 2026. Connection and Service run evidence comes from supplied screenshots. Model parity was checked separately through read-only Desktop queries.

## What is working

The Power BI Desktop working copy and published Fleet Activity semantic model now use the native Databricks connector in Import mode. `GoldSource` reads `ev_telematics.fleet_activity_demo_20260910.gold_daily_vehicle_activity` through a Databricks SQL warehouse, authenticated with OAuth (OIDC in Desktop; OAuth2 in Service). No manual CSV export is required for this connection.

The connection preview showed 721 rows and 14 fields. The migration replaced the CSV-based `GoldSource`, removed the unused `GoldCsvPath` parameter and temporary duplicate query, then applied the changes. Screenshots showed the existing three report pages rendering and the three dimension-to-Fleet relationships intact. Visible headline values remained 32,554 km, 54.90 km per driving day, 17.2% idle, 99.3% passing checks and 5 days needing attention. The initial screenshot comparison was followed by a read-only Desktop query: all 721 rows and 14 original fields reconciled to baseline, with zero key/relationship integrity issues. This does not certify every UI interaction. See [migration validation](migration_validation.json).

Power BI Service showed Databricks mapped to a Personal Cloud Connection. Refresh history confirmed:

| Field | Observed value |
| --- | --- |
| Date | 12 September 2026 |
| Type | On demand |
| Start | 1:50:16 PM |
| End | 1:50:25 PM |
| Status | Completed |
| Duration | 9 seconds |

Times above are transcribed as displayed in the browser. The row appears under the Scheduled history tab but its actual trigger type is **On demand**.

## First scheduled refresh — 13 September

Supplied Refresh history evidence shows Type **Scheduled**, Start **09:03:03 AM**, End **09:17:55 AM**, and Status **Completed**: an elapsed **14m 52s**. Times are transcribed as displayed; the configured schedule is 09:00 America/Chicago. The Databricks run was launched by scheduler at 08:00 and succeeded (Runs list: 3m 9s; success email: 3m 8s). The received email records a start at 13:00:17 UTC. These observations confirm both scheduled executions and success-email delivery, not the propagation of newly added source data.

## Daily sequence

| Stage | Schedule | Evidence |
| --- | --- | --- |
| Databricks Bronze → Silver → Gold | 08:00 America/Chicago daily | 12 September scheduled run succeeded; see [job review](../databricks/JOB_REVIEW.md). |
| Power BI semantic model Import refresh | 09:00 Central Time (US & Canada) daily | Refresh history shows Scheduled / Completed on 13 September, 09:03:03–09:17:55 (14m 52s). |

Both schedules use Central local time with daylight saving, rather than fixed UTC. Power BI refresh-failure notifications to the semantic model owner were seen enabled in the setup screenshot; delivery is untested. Databricks Job notifications showed Success and Failure email enabled at job level. Supplied screenshots confirm the 13 September scheduled job succeeded and its success email arrived at 08:03. Failure-email delivery remains untested.

The one-hour gap is a scheduling buffer, not a dependency. Power BI can refresh older Gold data if the pipeline fails. Inspect both histories after a failure, repair the pipeline, and refresh the semantic model after Gold succeeds. The pipeline still replays the fixed August 1–30 synthetic demo with saved weather responses; this does not implement incremental ingestion or a new daily weather fetch.

If a refresh fails with a credential error, re-sign in through the semantic model's data source credentials (or its mapped cloud connection), then run Refresh now and verify Completed in Refresh history. Re-enable the schedule if it was disabled.

## Footer publication check — 12 September

The three source-footer strings were corrected in the saved Windows report, with backups and JSON validation. A Desktop publication-success screenshot confirmed republication. Public browser checks without signing in verified the corrected footer on Overview, Vehicles, and Data Health. Navigation between all three pages worked. The Overview Dallas filter produced 16,644 km, 55.30 km per driving day, 16.4% idle, 100.0% trusted, and zero attention days; Reset restored All filters and the baseline. Vehicles showed 24 registered vehicles, 123 idle and 593 driving vehicle-days. Data Health showed the expected six review rows.

These are focused public UI checks, not a complete rerun of the earlier interaction suite or proof of a future scheduled/data refresh. The portfolio previews now use owner-supplied PNG screenshots of the corrected report; see [screenshot provenance](../../docs/screenshots/README.md). [Detailed record](publication_cleanup_validation.json).

## Reproduction

1. The saved Windows PBIP/TMDL has been synchronized. This repository uses required host/path parameters instead of the original warehouse identifiers. Set them and authenticate before refreshing a clone.
2. The first scheduled Service refresh is confirmed for 13 September. Continue to inspect Refresh history when investigating stale results.
3. After a Gold data change, inspect refresh history and the public report. The current public URL is in [POWER_BI.md](../POWER_BI.md). Footer publication and focused interaction checks passed above; broader interaction coverage and propagation of a future Gold data change remain unverified.

Obtain connection details from SQL Warehouses → the warehouse → Connection details. Authenticate with an authorized Databricks account in Desktop and Service, configure the semantic model's cloud connection, run Refresh now, and inspect Refresh history for Completed before relying on the schedule. This documentation omits private workspace identifiers and notification addresses.

Private account screenshots and connection identifiers are excluded from the curated repository. The refresh-history row above is a transcription of the supplied screenshot; it is not an exported Service audit record.

The source migration preserves DAX, relationships and pipeline transformations. The warehouse parameterization is deliberate; the working Windows report now has the same corrected source-footer wording as the repository. The earlier 42 + 9 interaction checks predate the migration. The earlier documentation review did not independently verify the live migration or Service refresh.

References: [Databricks connector](https://learn.microsoft.com/en-us/power-query/connectors/databricks), [Power BI scheduled refresh and refresh history](https://learn.microsoft.com/en-us/power-bi/connect-data/refresh-scheduled-refresh).
