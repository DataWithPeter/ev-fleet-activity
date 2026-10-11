# Report screenshots

The five historical baseline screenshots listed below are full-resolution PNG originals supplied by the project owner on 12 September 2026, copied byte-for-byte without resizing or recompression. The three Power BI images were replaced after footer republication and show Depot, Model, and Weather set to All. None of the screenshots have been retouched.

| File | Report page |
| --- | --- |
| [overview.png](overview.png) | Fleet Overview — 2368 × 1360 |
| [vehicles.png](vehicles.png) | Vehicles & Depots — 2338 × 1346 |
| [data-health.png](data-health.png) | Data Health — 2328 × 1334 |
| [databricks-overview.png](databricks-overview.png) | Native Databricks dashboard: KPIs and daily distance — 3196 × 1818 |
| [databricks-data-quality.png](databricks-data-quality.png) | Native Databricks dashboard: depot comparisons, data quality, and review table — 3188 × 1762 |

The report covers 1–30 August 2026. Fleet and telemetry records are synthetic; weather comes from Open-Meteo. These screenshots document visible report output, not real fleet performance or a completed audit of every interaction. The Databricks dashboard requires sign-in and data permissions; its screenshots do not provide public workspace access.

## Power BI source caption

The updated screenshots show `Source: Databricks Gold table`, matching the republished report. The Data Health capture clips the bottom edge of its footer; the original image is preserved. A separate browser check verified the complete caption on all three public pages on 12 September. See the [publication checks](../../fleet_activity/power_bi/publication_cleanup_validation.json) and [refresh checkpoint](../../fleet_activity/power_bi/REFRESH_SETUP.md).

Capturing the report does not verify propagation of a later Gold update or the first automatic scheduled refresh.

## Databricks date control

The supplied overview screenshot displays `09/12/2026` in both Date (UTC) fields while the chart covers August and the KPIs show the full August baseline. This mismatch is preserved in the image. The screenshot alone does not establish whether the control was applied or correctly bound to each visual; its behavior needs a live check before treating this as evidence of date filtering. Earlier dashboard validation remains a separate historical record.

## Expanded Telemetry Exceptions — 11 October 2026

The owner supplied the following Power BI Service PNG screenshots after refreshing the expanded data. These files are copied byte-for-byte from the supplied originals; no chart data, labels or pixels were retouched. Browser/Service controls remain visible and table content below the visible rows requires scrolling.

| File | Page and observed expanded values |
| --- | --- |
| [telemetry-exceptions-expanded.png](telemetry-exceptions-expanded.png) | Exceptions: 43 excluded, 18 held, 9 insufficient, 16 missing, 97.6% reportable; all slicers All |
| [telemetry-record-audit-expanded.png](telemetry-record-audit-expanded.png) | Record audit: 10,652 source, 10,517 accepted, 106 held, 19 rejected, residual 10; quarantine 125, linked rejects 8, unlinked rejects 11 |

The screenshots support the displayed values and header layout. They do not prove all table rows were inspected or that Reset and slicer interactions were tested. Existing September screenshots and their original captions remain historical baseline evidence. See [expanded web verification](../../fleet_activity/power_bi/validation_expanded_august_v1.json).
