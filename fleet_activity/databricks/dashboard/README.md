# Native Databricks dashboard

Status: built, tested against live Gold and published on 2026-09-11.

Open **EV Fleet Activity — SQL Dashboard** from the Databricks workspace's Dashboards area. The workspace-specific URL is intentionally omitted from committed project documentation.

The published dashboard uses individual viewer data permissions. It requires
Databricks sign-in and access to the Gold table; this is not an anonymous public link.

This dashboard uses the live Gold table. The published Power BI model now imports
that Gold table directly; the repository Power BI model contains the synchronized Databricks source with warehouse placeholders. The Databricks version provides a SQL-based fleet overview;
Power BI provides the three-page report with its star schema and DAX. Neither
report changes the pipeline.

## Screenshots

[Dashboard overview](../../../docs/screenshots/databricks-overview.png) · [Data quality and review table](../../../docs/screenshots/databricks-data-quality.png)

These full-resolution screenshots were supplied on 12 September 2026. The overview's date control shows September 12 while the visuals show August; this discrepancy needs a live check. See [capture notes](../../../docs/screenshots/README.md#databricks-date-control). It does not change the historical publication checks below.

## Dashboard page

- Filters: UTC date, depot, model and weather.
- Cards: observed distance, km per driving day, idle share, trusted coverage,
  and days needing attention.
- Charts: daily distance, distance by depot, and daily quality coverage.
- Review table: vehicle-days with unreliable distance or no fleet registration.

Use `activity.sql` as the row-level dataset. Apply the same filters to the
cards and charts. Sum `trusted_distance_km`, average `driving_distance_km`,
and calculate idle share as `AVG(idle_day)`. The SQL sets `idle_day` to
null for untrusted days, so its mean is exactly idle days divided by trusted
days. Coverage is `AVG(trusted_day)` across all vehicle-days. These averages
operate on one row per vehicle-day, not pre-aggregated daily percentages. Count attention days separately from review
rows: the latter also include unregistered vehicles.

Distance means the within-day observed odometer range after quality checks.
Idle means a trusted zero-distance vehicle-day, not proof of fleet utilization.
Missing or unreliable distance stays blank. Fleet and telemetry are synthetic;
weather is real Open-Meteo data. Weather comparisons are descriptive.

## Publication checks

Run `checks.sql` against live Gold, then compare the dashboard and Power BI:

| Check | Expected from the current CSV baseline |
| --- | ---: |
| Vehicle-days | 721 |
| Trusted days | 716 |
| Days needing attention | 5 |
| Observed distance | 32,554.24 km |
| Km per driving day | 54.90 km |
| Idle days | 123 |
| Idle share | 17.2% |
| Review rows | 6 |
| Chicago distance | 15,900 km |
| Dallas distance | 16,644.24 km |
| Unknown depot distance | 10 km |

Live checks passed for the baseline, Chicago, Chicago + Wet, Dallas, Model A,
a date preset outside the demo period, and reset. The review table shows six
rows overall and no rows for Dallas. Unreliable distances remain null. See
`validation.json` for the observed values.

`Fleet Activity.import.lvdash.json` is the initial import definition, not an
exact export of the final dashboard. Native field formatting was finished in
the UI: distance uses grouped whole numbers, driving-day mean uses two decimal
places, and both percentages use one decimal place. The dashboard saved in
Databricks is the source of truth for those formatting changes. The attempted
UI export did not yield a local file. Do not replace the published dashboard
with the initial import file without reapplying those formats.

Power BI is published separately under the new account and has a public report
link recorded in `fleet_activity/POWER_BI.md`. It now imports Databricks Gold directly, with a completed Service on-demand refresh.
See [refresh evidence and known limitations](../../power_bi/REFRESH_SETUP.md).

Both reports can be edited later. Republish their changes and refresh Power BI's
imported data after a successful Gold update.
