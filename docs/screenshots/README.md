# Report screenshots

The Power BI Overview and two Databricks screenshots are full-resolution PNG originals supplied by the project owner on 12 September 2026, copied byte-for-byte without resizing or recompression. The Vehicles and Data Health JPEGs were captured directly from the public Power BI report that day, without signing in. Power BI screenshots show Depot, Model, and Weather set to All. None of the screenshots have been retouched.

| File | Report page |
| --- | --- |
| [overview.png](overview.png) | Fleet Overview — 3204 × 1824 |
| [vehicles.jpg](vehicles.jpg) | Vehicles & Depots |
| [data-health.jpg](data-health.jpg) | Data Health |
| [databricks-overview.png](databricks-overview.png) | Native Databricks dashboard: KPIs and daily distance — 3196 × 1818 |
| [databricks-data-quality.png](databricks-data-quality.png) | Native Databricks dashboard: depot comparisons, data quality, and review table — 3188 × 1762 |

The report covers 1–30 August 2026. Fleet and telemetry records are synthetic; weather comes from Open-Meteo. These screenshots document visible report output, not real fleet performance or a completed audit of every interaction. The Databricks dashboard requires sign-in and data permissions; its screenshots do not provide public workspace access.

## Known footer discrepancy

The hosted report still displays `Source: Gold CSV extract`. That caption is stale: the published semantic model was migrated to Databricks Gold Import. The repository's report definitions have the corrected footer, but the hosted footer update remains pending. The screenshots preserve the hosted report exactly as seen. See the [refresh checkpoint](../../fleet_activity/power_bi/REFRESH_SETUP.md) for migration evidence and outstanding checks.

Capturing the report does not verify propagation of a later Gold update or the first automatic scheduled refresh.

## Databricks date control

The supplied overview screenshot displays `09/12/2026` in both Date (UTC) fields while the chart covers August and the KPIs show the full August baseline. This mismatch is preserved in the image. The screenshot alone does not establish whether the control was applied or correctly bound to each visual; its behavior needs a live check before treating this as evidence of date filtering. Earlier dashboard validation remains a separate historical record.
