# Databricks to Power BI refresh checkpoint

Status: 12 September 2026. Evidence is Niko's screenshots and source code shared during the guided setup, reviewed by Codex. A later read-only Desktop model query and source synchronization are recorded below; Service run evidence remains screenshot-based.

## What is working

The Power BI Desktop working copy and published Fleet Activity semantic model now use the native Databricks connector in Import mode. `GoldSource` reads `ev_telematics.fleet_activity_demo_20260910.gold_daily_vehicle_activity` through a Databricks SQL warehouse, authenticated with OAuth (OIDC in Desktop; OAuth2 in Service). No manual CSV export is required for this connection.

The connection preview showed 721 rows and 14 fields. Niko replaced the CSV-based `GoldSource`, removed the unused `GoldCsvPath` parameter and temporary duplicate query, then applied the changes. Screenshots showed the existing three report pages rendering and the three dimension-to-Fleet relationships intact. Visible headline values remained 32,554 km, 54.90 km per driving day, 17.2% idle, 99.3% passing checks and 5 days needing attention. The initial screenshot comparison was followed by a read-only Desktop query: all 721 rows and 14 original fields reconciled to baseline, with zero key/relationship integrity issues. This does not certify every UI interaction. See [migration validation](migration_validation.json).

Power BI Service showed Databricks mapped to a Personal Cloud Connection. Refresh history confirmed:

| Field | Observed value |
| --- | --- |
| Date | 12 September 2026 |
| Type | On demand |
| Start | 1:50:16 PM |
| End | 1:50:25 PM |
| Status | Completed |
| Duration | 9 seconds |

Times above are transcribed as displayed in Niko's browser. The row appears under the Scheduled history tab but its actual trigger type is **On demand**.

## Daily sequence

| Stage | Schedule | Evidence |
| --- | --- | --- |
| Databricks Bronze → Silver → Gold | 08:00 America/Chicago daily | 12 September scheduled run succeeded; see [job review](../databricks/JOB_REVIEW.md). |
| Power BI semantic model Import refresh | 09:00 Central Time (US & Canada) daily | Niko confirmed the schedule change; workspace screenshot shows next refresh 13 September 2026 at 09:00 AM. First automatic execution remains unverified. |

Both schedules use Central local time with daylight saving, rather than fixed UTC. Power BI refresh-failure notifications to the semantic model owner were seen enabled in the setup screenshot; delivery is untested. Niko's later Databricks Job notifications screenshot showed both Success and Failure email enabled at job level; email delivery has not been tested by forcing a failure.

The one-hour gap is a scheduling buffer, not a dependency. Power BI can refresh older Gold data if the pipeline fails. Inspect both histories after a failure, repair the pipeline, and refresh the semantic model after Gold succeeds. The pipeline still replays the fixed August 1–30 synthetic demo with saved weather responses; this does not implement incremental ingestion or a new daily weather fetch.

If a refresh fails with a credential error, re-sign in through the semantic model's data source credentials (or its mapped cloud connection), then run Refresh now and verify Completed in Refresh history. Re-enable the schedule if it was disabled.

## Reproduction and remaining work

1. The saved Windows PBIP/TMDL has been synchronized. This repository uses required host/path parameters instead of the original warehouse identifiers. Set them and authenticate before refreshing a clone.
2. Confirm the first scheduled Service refresh after 13 September at 09:00 Central. A successful manual refresh proves Service connectivity, not that the future trigger has fired.
3. Recheck the public report after refresh, including page navigation and filters. The current public URL is in [POWER_BI.md](../POWER_BI.md); public embed propagation and full post-migration interaction checks remain unverified.
4. The repository footer has been corrected to `Databricks Gold table`. Apply the same footer correction in the working Desktop project and republish; no change to the currently hosted footer is claimed.

Obtain connection details from SQL Warehouses → the warehouse → Connection details. Authenticate with an authorized Databricks account in Desktop and Service, configure the semantic model's cloud connection, run Refresh now, and inspect Refresh history for Completed before relying on the schedule. This documentation omits private workspace identifiers and notification addresses.

Private account screenshots and connection identifiers are excluded from the curated repository. The refresh-history row above is a transcription of the supplied screenshot; it is not an exported Service audit record.

The source migration preserves DAX, relationships and pipeline transformations. Only the warehouse parameterization and three source-footer strings differ deliberately from the saved Windows source. The earlier 42 + 9 interaction checks predate the migration. Claude's earlier review covered documentation alignment, not independent live migration or refresh verification.

References: [Databricks connector](https://learn.microsoft.com/en-us/power-query/connectors/databricks), [Power BI scheduled refresh and refresh history](https://learn.microsoft.com/en-us/power-bi/connect-data/refresh-scheduled-refresh).
