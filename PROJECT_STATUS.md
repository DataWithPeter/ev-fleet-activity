# Project status

Last updated: 28 September 2026.

**Status: completed portfolio project — public on GitHub.**

EV Fleet Activity combines a Databricks lakehouse pipeline, data-quality checks, and two reporting interfaces. The completed scope includes source preparation, Bronze ingestion, Silver cleaning and quarantine, Gold daily activity, scheduled execution, and Power BI and Databricks reporting.

The [repository](https://github.com/DataWithPeter/ev-fleet-activity) became public on 28 September 2026. The verification limits below describe the scope of the recorded evidence; they are not unfinished core pipeline stages.

## Verified

- GitHub Actions passed for code revision `375e9d5` (unused setup imports removed): [successful validation run](https://github.com/DataWithPeter/ev-fleet-activity/actions/runs/36290015207). This is the latest code validation checked on 28 September; the dated cloud and reporting results below remain historical evidence, not a claim of a fresh cloud run today.
- Local Bronze → Silver → Gold notebooks and their Databricks companions preserve the same transformations and vehicle/day grain.
- Baseline: 721 Gold rows, 716 trusted days, 22 quarantined/held readings, 32,554.24 observed km. Exact evidence hashes and historical runs are in [execution evidence](fleet_activity/evidence/README.md).
- Daily Databricks job: 08:00 America/Chicago, Bronze → Silver → Gold with successful upstream dependencies, one concurrent run. The 12 and 13 September scheduled runs succeeded; success-email delivery was confirmed on 13 September. [Job review](fleet_activity/databricks/JOB_REVIEW.md).
- Native Databricks SQL dashboard: published and checked against live Gold, with fleet KPIs, charts, filters, and a review table. Access requires Databricks sign-in and data permissions. [Dashboard documentation and validation](fleet_activity/databricks/dashboard/README.md).
- Power BI: three report pages, three dimension-to-Fleet relationships, 15 measures. The working and published models import Databricks Gold. Service on-demand refresh completed on 12 September; the scheduled refresh on 13 September completed in 14m 52s.
- The saved Windows PBIP/TMDL was synchronized into this repository. Public source uses warehouse connection placeholders; report footer source text is corrected in the repository artifact.
- Read-only queries against the post-migration Desktop model confirmed: all 721 rows × 14 original fields reconcile to baseline; zero duplicate vehicle/date keys or orphan dimension keys. [Migration validation](fleet_activity/power_bi/migration_validation.json).
- The report was republished on 12 September. Public browser checks without sign-in verified `Source: Databricks Gold table` on all three pages, page navigation, the Overview Dallas filter and Reset, and baseline headline values. [Publication checks](fleet_activity/power_bi/publication_cleanup_validation.json).

## Verification limits and optional follow-up

- Failure-email delivery is untested; success-email delivery and the first scheduled Power BI refresh are confirmed from supplied screenshots.
- Broader post-migration interaction coverage beyond the focused publication checks above; propagation of a future Gold data change remains unverified.
- The cloud-only `04_reports` notebook and final Databricks dashboard number formatting are not exported here; the SQL dashboard import file is an initial definition.

These limits do not prevent local reproduction. Schedules replay the fixed August demo; they do not ingest a new day or implement incremental MERGE. SQLite is local, weather is saved real Open-Meteo data, and multi-table refreshes are not one transaction. See [refresh setup](fleet_activity/power_bi/REFRESH_SETUP.md).
