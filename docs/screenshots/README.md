# Public report screenshots

These JPEGs were captured directly from the public Power BI report on 12 September 2026, without signing in. They show the complete report viewport, including Power BI navigation, with Depot, Model, and Weather set to All. The screenshots have not been retouched.

| File | Report page |
| --- | --- |
| [overview.jpg](overview.jpg) | Fleet Overview |
| [vehicles.jpg](vehicles.jpg) | Vehicles & Depots |
| [data-health.jpg](data-health.jpg) | Data Health |

The report covers 1–30 August 2026. Fleet and telemetry records are synthetic; weather comes from Open-Meteo. These screenshots demonstrate the public report's visible output and page navigation, not real fleet performance or a completed audit of every interaction.

## Known footer discrepancy

The hosted report still displays `Source: Gold CSV extract`. That caption is stale: the published semantic model was migrated to Databricks Gold Import. The repository's report definitions have the corrected footer, but the hosted footer update remains pending. The screenshots preserve the hosted report exactly as seen. See the [refresh checkpoint](../../fleet_activity/power_bi/REFRESH_SETUP.md) for migration evidence and outstanding checks.

Capturing the report does not verify propagation of a later Gold update or the first automatic scheduled refresh.
