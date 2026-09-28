# Fleet Activity — Power BI report

Open `Fleet Activity.pbip` from this folder in Power BI Desktop on Windows. Keep your existing working project backed up before opening a separate clone.

The published report and Windows working copy now import directly from Databricks Gold. A Service on-demand refresh completed on 12 September 2026 in 9 seconds; daily refresh is configured for 09:00 Central after the 08:00 pipeline. See [refresh setup and evidence](REFRESH_SETUP.md).

**Repository artifact:** saved Windows PBIP/TMDL synchronized on 12 September. It uses Databricks Import; the original warehouse host/path were replaced with required `DatabricksHost` and `DatabricksHttpPath` text parameters. No credentials or cached model data are included.

For your own deployment:

1. Run the [Databricks companion](../databricks/README.md) to create Gold.
2. Open this PBIP in Desktop, then Transform data → Manage Parameters. Enter Server Hostname and HTTP Path from your SQL warehouse's Connection details.
3. In `GoldSource`, adapt catalog/schema names if they differ from `ev_telematics.fleet_activity_demo_20260910`.
4. Sign in with an authorized Databricks account and refresh. Compare the baseline below when using the included demo inputs.
5. Publish to your workspace, authenticate its cloud connection, and verify a Service refresh before enabling the schedule. See [refresh setup](REFRESH_SETUP.md).

The offline CSV remains in `../evidence/` for validation. It is not a second Power BI model or an automatic fallback.

## Layout

The dark layout follows the SaaS Metrics dashboard pattern.

- **Header:** each page has a title with an **ⓘ** button, tab buttons (Overview · Vehicles · Data Health), a **Reset** button, and Depot, Model and Weather filters.
- **Body:** below the header, a row of KPIs sits above one main chart and supporting visuals.
- **ⓘ panel:** opens the definitions for that page; **Close** hides it again.
- **Reset:** clears that page's filters only. To clear a highlight made by clicking a chart, click an empty part of the page.
- **Colors:** green means good, orange means needs attention.

| Tab | Page title | Message | Visuals |
| --- | --- | --- | --- |
| Overview | Fleet Overview | How much the fleet drove, and why some days are lower. | <ul><li>KPIs: Distance · Km per driving day · Idle days % · Data trusted · Days needing attention</li><li>Daily distance vs vehicles on the road</li><li>Distance by depot</li><li>Idle days % by weekday</li><li>Km per driving day: dry vs wet (weather from Open-Meteo)</li></ul> |
| Vehicles | Vehicles & Depots | Vehicles differ in how often they sit idle, not how far they drive. | <ul><li>KPIs: Registered vehicles · Idle vehicle-days · Driving vehicle-days · Idle days %</li><li>Idle days % by depot and model</li><li>Km per driving day by depot and model</li><li>Idle days vs distance for each vehicle</li><li>Vehicle leaderboard</li></ul> |
| Data Health | Data Health | Whether the totals can be trusted, and where the gaps are. | <ul><li>KPIs: Data trusted · Vehicles with problem days · Unregistered vehicle-days · Unregistered km</li><li>Vehicle-days by day: trusted vs needs attention</li><li>Problem days by type</li><li>Needs review (problem days plus the unregistered vehicle)</li></ul> |

## Definitions

- **Trusted vehicle-day:** the pipeline checks passed. Missing or untrusted distance stays blank, never zero.
- **Idle vehicle-day:** a trusted vehicle-day with 0 observed km.
  - This is an operational definition: no distance between the available readings. It is not proof the vehicle never moved.
  - Missing and untrusted days are never counted as idle.
- **Idle days %:** idle vehicle-days ÷ trusted vehicle-days. It is not a fleet-wide active-vehicle rate, which remains deferred.
- **Km per driving day:** mean distance over trusted vehicle-days with more than 0 km.
- **Vehicles on the road:** trusted vehicle-days with more than 0 km. For a single day, that's the number of vehicles that drove.
- **Status:** a friendly label for `distance_status`, for example "Missing telemetry".
- **Registered vehicles:** distinct registered vehicle IDs in the current activity selection. The scatter also excludes the unregistered vehicle; the leaderboard retains it.
- **Driving vehicle-days:** trusted vehicle-days above 0 km. Across several dates, this is not a distinct vehicle count.
- **Needs review:** a problem day (untrusted, missing telemetry, insufficient readings) or a day from a vehicle missing from the fleet roster.

**Reading the analysis:** daily distance and vehicles on the road move together. That is partly arithmetic, so don't treat it as proof of cause. Fleet and telemetry are synthetic, and weather comparisons are descriptive.

## Model and measures

The model is a small star schema: Fleet (daily activity), DimDate, DimVehicle and DimDepot, plus a disconnected Measures table. All relationships are one-to-many, filtering from dimensions into Fleet.

See [Model and DAX reference](MODEL_AND_DAX.md) for the flow, relationships and formulas. `MEASURES.dax` contains the 15 measures and two calculated label columns. The vehicle leaderboard uses native table sorting; no custom ranking measure is required.

`Idle vehicle-days` compares with `==` so a blank distance never matches 0. `KEEPFILTERS` preserves the user's selections. These correctness choices remain in the simplified measures.

## Historical baseline checks — September 11, 2026

- **Load:** opened in Power BI Desktop 2.156.951.0. 721 Gold rows: 716 trusted, 5 needing attention.
- **Figures:** recomputed from the CSV with Python and read back from Desktop.

  | Selection | Distance | Km per driving day | Idle days % | Data trusted | Days needing attention |
  | --- | --- | --- | --- | --- | --- |
  | All | 32,554 km | 54.90 | 17.2% (123 idle days) | 99.3% (716 / 721) | 5 |
  | Chicago | 15,900 km | 54.64 | 18.0% | 98.6% (355 / 360) | 5 |
  | Dallas | 16,644 km | 55.30 | 16.4% | 100.0% | 0 |

- **Interaction tests after the model change:** 42 checks passed in Desktop:
  - filters and Reset on every page, and pages not affecting each other;
  - ⓘ panels opening and closing;
  - the 6-row Needs review table, including the unregistered vehicle (0 rows for Dallas);
  - tab navigation.
- **Earlier layout recheck:** after the last layout tweak before the model change, KPIs and the ⓘ panel were rechecked on every page (9 checks).
- **Validation:** `powerbi-report-author validate` reports 0 errors and one schema warning. Microsoft's `visualContainer/2.11.0` URL returns 404, so exact-version coverage is incomplete. The separate compatibility check passed all 79 PBIR files with 0 errors; 39 visual files were checked against public 2.9.0 in memory.
- **Final targeted checks:** 9 checks passed after the chart/table grouping filters. All 721 rows and 14 original fields match Gold when reconstructed through the dimensions; 120 direct visual bindings resolve. See [validation results](validation.json).
- **Saved state:** Overview active; 79 report definition files and 10 model definition files match the saved Windows copy.
- **Review scope:** The documentation review included recomputing figures. That alignment pass did not open or visually review the report; it does not certify the later migration.
- **Model format:** TMDL in both the saved Windows project and this folder. The duplicate `model.bim` format is retired.

## Migration checkpoint — September 12, 2026

The running Desktop model was queried read-only after the Databricks source change. All 721 rows and 14 original fields match the CSV baseline; no duplicate vehicle/date keys or orphan dimension keys were found, and all three relationships remain active and single-direction. See [migration results](migration_validation.json) and the [model/DAX guide](MODEL_AND_DAX.md).

The working report was corrected and republished on 12 September. Public browser checks verified `Source: Databricks Gold table` on all three public pages, navigation, the Overview Dallas filter and Reset, and baseline headline values. See [publication checks](publication_cleanup_validation.json). The portfolio previews now use owner-supplied PNG screenshots of the corrected report; see [screenshot provenance](../../docs/screenshots/README.md).

**Confirmed on 13 September:** the scheduled Service refresh completed and the Databricks success email was received.

**Future improvements:** failure-notification delivery, broader post-migration UI interactions beyond the focused publication checks, and propagation of a future Gold data change. [Refresh checkpoint](REFRESH_SETUP.md).

The Date filter was removed because the data covers one month; the line under each title shows the period.

The editable artifact is PBIP/TMDL; no PBIX is maintained. The report is published in Power BI Service and a public report link is recorded in `fleet_activity/POWER_BI.md`.

Fleet and telemetry are synthetic. Weather is from Open-Meteo.
