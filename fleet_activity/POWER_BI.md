# Gold to Power BI

The data pipeline prepares reliable tables. The published Power BI report now imports directly from the Databricks Gold table; the repository includes the synchronized Databricks model with configurable warehouse placeholders. No HTML, CSS or Matplotlib is required.

Telemetry files + fleet SQLite database + weather API → Bronze/Silver processing → Gold → Power BI.

## Start with one Gold table

Databricks table: `ev_telematics.fleet_activity_demo_20260910.gold_daily_vehicle_activity`.
Local equivalent: `output/delta/gold_daily_vehicle_activity/`.
Small offline extract: `output/daily_vehicle_activity.csv`.

**Grain:** one row per `event_date` and `vehicle_id`. Dates and reading timestamps use UTC.

| Fields | Use in Power BI |
| --- | --- |
| event_date | Date filter and trend axis |
| vehicle_id | Vehicle detail |
| depot_id, depot_name, model | Grouping and filters |
| observed_distance_km | Sum or mean of trusted observed distance |
| distance_status | Separate trusted, untrusted, insufficient_readings, missing_telemetry |
| reading_count, first_reading, last_reading | Explain coverage |
| registered_vehicle | Expose vehicles absent from the roster |
| temperature_c, precipitation_mm, weather_condition | Weather context and wet/dry grouping |

Distance is the range between within-day odometer observations after quality checks. Missing or unreliable distance stays blank; do not replace it with zero. A trusted stationary day can have zero distance. Count all rows for coverage, and only nonblank distance rows for the mean denominator. Do not average pre-aggregated averages from `activity_report.csv`; use the vehicle-day Gold table. Weather is repeated across vehicles at a depot on a day, so do not sum precipitation over vehicle rows.

## Connection and first exercise

Use Power BI's Databricks connector with the SQL warehouse's Server Hostname and HTTP Path, authenticate with an authorized account, and select the Gold table. Start with Import mode for this small learning dataset. Desktop access and an on-demand Power BI Service refresh were demonstrated on 12 September. See the [refresh checkpoint](power_bi/REFRESH_SETUP.md) for evidence and remaining checks.

Official instructions: [Connect Power BI Desktop to Databricks](https://docs.databricks.com/aws/en/partners/bi/power-bi/desktop).
Power BI Desktop requires Windows: [Microsoft installation requirements](https://learn.microsoft.com/en-us/power-bi/fundamentals/desktop-get-the-desktop). Confirm your Windows environment when beginning the Power BI phase.

First build a table visual and check 721 vehicle-days: 716 trusted, 3 untrusted, 1 insufficient and 1 missing. Compare depot/model/weather totals and means with the notebook's SQL validation query. Then add a distance trend, depot/model comparison and quality counts. Keep this as a separate report; the pipeline should not depend on it.

The CSV remains an offline validation baseline, not the current Power BI source. The published model now imports Gold through the Databricks connector. Power BI Service refresh is configured daily at 09:00 Central, after the 08:00 Databricks job. This is an independent schedule, not a pipeline-success trigger; the first scheduled Power BI execution remains unverified.

Fleet and telemetry are synthetic; weather is real Open-Meteo data. These visuals demonstrate integration, not real fleet behavior or weather effects. Preserve Open-Meteo attribution in the eventual report.

## Current status

The editable three-page project is in `power_bi/`. It was synchronized from the saved Windows working copy on 12 September. Set `DatabricksHost` and `DatabricksHttpPath` to your own warehouse details in Power Query and authenticate. The template deliberately omits the original workspace identifiers. Catalog/schema navigation uses the demo names above; adapt it if you deploy elsewhere.

The running post-migration Desktop model reconciled to all 721 baseline rows and 14 original fields. This proves the imported snapshot matches; it does not prove a future refresh or every report interaction. See [setup](power_bi/README.md), [migration validation](power_bi/migration_validation.json), and [refresh evidence](power_bi/REFRESH_SETUP.md).

Public recruiter report: [Fleet Activity](https://app.powerbi.com/view?r=eyJrIjoiMzUzYmU0YWEtYzU4NC00NmE1LTk2NmYtZjI4YTViMDhjMjY1IiwidCI6IjhiYmMwZjRiLTVkNWItNGNiMy05ZWM5LTc1MTc0MjRmMzY0ZiJ9&pageName=overview). It is intentionally public and may be indexed by search engines; it contains synthetic fleet/telemetry data and real Open-Meteo weather context.
