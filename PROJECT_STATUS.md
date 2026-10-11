# Project status

Last updated: 11 October 2026.

**Status: completed portfolio project — public on GitHub.**

EV Fleet Activity combines a Databricks lakehouse pipeline, data-quality checks, and three dashboards: one native Databricks dashboard and two Power BI reports. The completed scope includes source preparation, Bronze ingestion, Silver cleaning and quarantine, Gold daily activity and quality outputs, scheduled execution, and Power BI and Databricks reporting.

The [repository](https://github.com/DataWithPeter/ev-fleet-activity) became public on 28 September 2026. The verification limits below describe the scope of the recorded evidence; they are not unfinished core pipeline stages.

## Historical September verification

- GitHub Actions passed for code revision `375e9d5` (unused setup imports removed): [successful validation run](https://github.com/DataWithPeter/ev-fleet-activity/actions/runs/36290015207). This is the latest code validation checked on 28 September; the dated cloud and reporting results below remain historical evidence, not a claim of a fresh cloud run today.
- Local Bronze → Silver → Gold notebooks and their Databricks companions preserve the same transformations and vehicle/day grain.
- Baseline: 721 Gold rows, 716 trusted days, 22 quarantined/held readings, 32,554.24 observed km. Exact evidence hashes and historical runs are in [execution evidence](fleet_activity/evidence/README.md).
- Daily Databricks job: 08:00 America/Chicago, Bronze → Silver → Gold with successful upstream dependencies, one concurrent run. The 12 and 13 September scheduled runs succeeded; success-email delivery was confirmed on 13 September. [Job review](fleet_activity/databricks/JOB_REVIEW.md).
- Native Databricks SQL dashboard: published and checked against live Gold, with fleet KPIs, charts, filters, and a review table. Access requires Databricks sign-in and data permissions. [Dashboard documentation and validation](fleet_activity/databricks/dashboard/README.md).
- Power BI: three report pages, three dimension-to-Fleet relationships, 15 measures. The working and published models import Databricks Gold. Service on-demand refresh completed on 12 September; the scheduled refresh on 13 September completed in 14m 52s.
- The saved Windows PBIP/TMDL was synchronized into this repository. Public source uses warehouse connection placeholders; report footer source text is corrected in the repository artifact.
- Read-only queries against the post-migration Desktop model confirmed: all 721 rows × 14 original fields reconcile to baseline; zero duplicate vehicle/date keys or orphan dimension keys. [Migration validation](fleet_activity/power_bi/migration_validation.json).
- The report was republished on 12 September. Public browser checks without sign-in verified `Source: Databricks Gold table` on all three pages, page navigation, the Overview Dallas filter and Reset, and baseline headline values. [Publication checks](fleet_activity/power_bi/publication_cleanup_validation.json).

## Known limitations

- Failure-email delivery is untested; success-email delivery and the first scheduled Power BI refresh are confirmed from supplied screenshots.
- Expanded Service values and layout were checked on 11 October. Broader interaction coverage, including expanded slicer/Reset behavior, remains unverified.
- The cloud-only `04_reports` notebook and final Databricks dashboard number formatting are not exported here; the SQL dashboard import file is an initial definition.

These limits do not prevent local reproduction. Schedules replay the fixed August demo; they do not ingest a new day or implement incremental MERGE. SQLite is local, weather is saved real Open-Meteo data, and multi-table refreshes are not one transaction. See [refresh setup](fleet_activity/power_bi/REFRESH_SETUP.md).

## Expanded August update — 11 October 2026

- The optional 60-vehicle scenario adds three model profiles, 96 explicit defect/coverage events and independent expected-day fixtures; the original 24-vehicle scenario remains the default.
- Bronze → Silver → Gold activity → Gold quality completed in the verified manual Databricks run. Gold contains 1,805 activity/quality days, 52 issue occurrences and one reconciliation row, with business SHA-256 `748ecf0d000032ea963e16567d3d63b187014be881780d815283cba0fb30dfea`. [Runtime evidence](fleet_activity/evidence/expanded_august_v1/live_runtime_validation.json).
- Fleet Activity Service refresh completed and its expanded coverage/status values were observed. Owner screenshots of Telemetry Exceptions confirmed 43 excluded days, 97.6% reportable share and the full snapshot audit card values. [Exact web verification scope](fleet_activity/power_bi/validation_expanded_august_v1.json).
- The repository includes the final Exceptions PBIP/TMDL definitions with required connection parameters and no Desktop caches. No Desktop refresh/synchronization or republish was part of integration.
- The native Databricks dashboard's expanded values are independently calculated; its fresh expanded UI/query verification remains separate. Its September screenshots and publication evidence are preserved.

Fresh isolated integration passed 62 baseline tests and 23 expanded scenario tests, preserving both reviewed business hashes. [Integration validation](fleet_activity/evidence/expanded_august_v1/integration_validation.json). GitHub Actions results are recorded separately from these local checks and dated web observations. The original baseline evidence, business hash and existing fixtures are preserved. See [scenario execution instructions](fleet_activity/README.md) for the separate baseline and expanded test commands.

The existing [Fleet Activity public link](https://app.powerbi.com/view?r=eyJrIjoiMzUzYmU0YWEtYzU4NC00NmE1LTk2NmYtZjI4YTViMDhjMjY1IiwidCI6IjhiYmMwZjRiLTVkNWItNGNiMy05ZWM5LTc1MTc0MjRmMzY0ZiJ9&pageName=overview) was verified in a fresh Incognito window on 11 October with no sign-in. It displayed 74,442 km, 63.52 km per driving day, 33.5% idle, 97.6% trusted and 43 days needing attention with filters set to All. This browser check did not produce a local screenshot file.

Telemetry Exceptions also has a [verified anonymous public link](https://app.powerbi.com/view?r=eyJrIjoiMWUzN2I0YjktYjBlZS00Y2E0LWI3OGYtOGNlYmIyYmRmYzkyIiwidCI6IjhiYmMwZjRiLTVkNWItNGNiMy05ZWM5LTc1MTc0MjRmMzY0ZiJ9). Both pages rendered in a fresh Incognito window on 11 October and matched the expanded card values. The repository showcase has one native Databricks dashboard (authorized sign-in required) and two anonymously accessible Power BI reports.
