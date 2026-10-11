# Telemetry Exceptions — Power BI source

[Open Telemetry Exceptions in Power BI](https://app.powerbi.com/view?r=eyJrIjoiMWUzN2I0YjktYjBlZS00Y2E0LWI3OGYtOGNlYmIyYmRmYzkyIiwidCI6IjhiYmMwZjRiLTVkNWItNGNiMy05ZWM5LTc1MTc0MjRmMzY0ZiJ9) — public access, no sign-in required.

Open `Telemetry Exceptions.pbip` in Power BI Desktop to adapt a separate copy. This repository contains report and semantic-model definitions, not an imported model cache. The working Service reports were verified on the web; this repository integration did not refresh Desktop, synchronize its cache or republish either report.

Set the required `DatabricksHost` and `DatabricksHttpPath` parameters to your SQL warehouse connection details, and authenticate with your own authorized account. The three table partitions use `ev_telematics.fleet_activity_demo_20260910`; adapt those names for another deployment. These parameters replace the working project's concrete host/path only in the public source.

Run Bronze → Silver → Gold activity → Gold quality before refreshing a deployment. Quality contributes `gold_vehicle_day_quality`, `gold_vehicle_day_issue` and `gold_record_reconciliation`. The only relationship is quality one-to-many issue through `vehicle_day_key`, filtering toward issues. Reconciliation is intentionally disconnected and covers the whole saved snapshot.

The Exceptions page shows excluded vehicle-days, held days, insufficient readings, missing telemetry and reportable share; a primary-cause chart and review table explain the affected days. A separate registry table retains trusted unregistered days. Record audit accounts for all source records and separates rejected records from held readings. Its eight cards do not change with day-level slicers.

For the expanded August scenario, Exceptions shows 43 / 18 / 9 / 16 / 97.6%. Record audit shows 10,652 source, 10,517 accepted, 106 held, 19 rejected, residual 10, quarantine 125, linked rejects 8 and unlinked rejects 11. Residual is arithmetic reconciliation, not independent deduplication evidence. There are 43 reporting-affected days, 47 exception-bearing days and 52 issue occurrences. The registry table contains four trusted unregistered days; an additional unregistered day with insufficient readings belongs in the review table.

[Expanded web verification](../validation_expanded_august_v1.json) records observed screenshot values and layout. Slicer and Reset interactions remain unverified for expanded data. [Exact calculated expectations](../../evidence/expanded_august_v1/report_expectations.json) include filter cases and the distinction between BLANK and zero. `MEASURES.dax` and `DISPLAY_COLUMNS.dax` mirror the model definitions.

The source report layout is unchanged from the reviewed report. Local `.pbi` settings, cached data, private DAX queries and concrete warehouse connection values are excluded. Historical baseline screenshots and validation remain elsewhere in the repository; they have not been relabeled as expanded results.

Both pages were independently opened in a fresh Incognito window on 11 October 2026, with no sign-in. Their expanded values, readable layout and four reportable registry rows were confirmed. Reset and slicer interactions remain unverified.
