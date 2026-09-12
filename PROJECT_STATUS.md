# Project status

Last updated: 12 September 2026.

This is the curated EV Fleet Activity portfolio. The initial Git history captures an existing project; it does not imply the project was built in one day.

## Verified

- Local Bronze → Silver → Gold notebooks and their Databricks companions preserve the same transformations and vehicle/day grain.
- Baseline: 721 Gold rows, 716 trusted days, 22 quarantined/held readings, 32,554.24 observed km. Exact evidence hashes and historical runs are in [execution evidence](fleet_activity/evidence/README.md).
- Daily Databricks job: 08:00 America/Chicago, Bronze → Silver → Gold with successful upstream dependencies, one concurrent run. The 12 September scheduled run succeeded. [Job review](fleet_activity/databricks/JOB_REVIEW.md).
- Native Databricks SQL dashboard: published and checked against live Gold, with fleet KPIs, charts, filters, and a review table. Access requires Databricks sign-in and data permissions. [Dashboard documentation and validation](fleet_activity/databricks/dashboard/README.md).
- Power BI: three report pages, three dimension-to-Fleet relationships, 15 measures. The working and published models import Databricks Gold. Service on-demand refresh completed in 9 seconds on 12 September.
- The saved Windows PBIP/TMDL was synchronized into this repository. Public source uses warehouse connection placeholders; report footer source text is corrected in the repository artifact.
- Codex queried the running post-migration Desktop model read-only: all 721 rows × 14 original fields reconcile to baseline; zero duplicate vehicle/date keys or orphan dimension keys. [Migration validation](fleet_activity/power_bi/migration_validation.json).

## Remaining external checks

- First automatic Power BI refresh at 09:00 Central on 13 September; failure-email delivery is untested.
- Full post-migration UI interaction checks and public embed propagation. Repository footer correction still needs to be applied and republished in the working report.
- The cloud-only `04_reports` notebook and final Databricks dashboard number formatting are not exported here; the SQL dashboard import file is an initial definition.

These limits do not prevent local reproduction. Schedules replay the fixed August demo; they do not ingest a new day or implement incremental MERGE. SQLite is local, weather is saved real Open-Meteo data, and multi-table refreshes are not one transaction. See [refresh setup](fleet_activity/power_bi/REFRESH_SETUP.md).
