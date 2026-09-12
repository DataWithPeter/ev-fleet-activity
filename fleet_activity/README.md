# Run the fleet project

The pipeline combines 30 telemetry files, a 24-vehicle SQL roster and weather for two depots over **1–30 August 2026, UTC**. The pipeline is split into [Bronze](notebooks/01_bronze_ingestion.ipynb), [Silver](notebooks/02_silver_cleaning.ipynb), and [Gold](notebooks/03_gold_activity.ipynb). Read and run them in that order. Each reads persisted tables rather than sharing Python variables. `weather.py` is the only imported project helper.

## Setup and run locally

Use Python 3.12 or later and Java 17. From the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r fleet_activity/requirements.txt
python fleet_activity/generate_sources.py
python fleet_activity/run_notebook.py
```

On macOS with Homebrew Java 17, first set `export JAVA_HOME=/opt/homebrew/opt/openjdk@17/libexec/openjdk.jdk/Contents/Home` if Java is not already discoverable. Spark also downloads its Delta JVM dependencies from Maven on first use.

The first normal run fetches weather; later runs reuse those snapshots. To reproduce the included evidence without calling Open-Meteo:

```bash
FLEET_OFFLINE=1 python fleet_activity/run_notebook.py
```

To deliberately fetch updated weather:

```bash
FLEET_REFRESH_WEATHER=1 python fleet_activity/run_notebook.py
```

Offline mode never calls the API and fails if a snapshot is missing. Do not combine offline and refresh. `examples/weather/` contains real responses fetched on 10 September 2026, with request parameters and timestamps. Weather data is attributed to [Open-Meteo](https://open-meteo.com/en/docs/historical-weather-api), [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Generated vehicle activity is independent of weather, so group differences demonstrate integration, not real effects.

After the runner reports success, inspect the Gold Delta table under `output/delta/gold_daily_vehicle_activity/`. The output also includes three executed notebooks, two small validation CSVs, and a summary with input hashes. Build the report separately in Power BI; see [the handoff](POWER_BI.md). `execution_status.json` records whether the most recent runner invocation succeeded. After a failure, older output files may still exist; do not treat them as a successful new run.

## How to read the notebook

1. Read/save telemetry with three business fields and audit metadata.
2. Parse and check records, deduplicate, identify inconsistent days.
3. Publish usable readings and quarantine; calculate daily observed distance.
4. Query the SQL roster and create the expected vehicle/day grid.
5. Fetch or reuse daily weather, with matching UTC days.
6. Join at vehicle/day grain, validate, save Gold, and check coverage.

A window detects decreases. The day is flagged; we cannot identify the bad reading merely from a falling pair. **Every usable-looking reading on an untrusted day is held out of accepted Silver**, and Gold distance is null. The day-issues table explains why. Quarantine therefore includes held records, not just individually invalid ones.

Record checks use the first failure in this order: malformed JSON, missing vehicle, invalid timestamp, outside-report-period date, invalid odometer. Multiple simultaneous row failures produce one reason; acceptance and the whole-day hold policy are unchanged. Day issues can still retain several reasons.

Other checks handle malformed JSON, missing/invalid fields, dates outside the report period, non-finite/negative odometers and conflicting timestamps. Identical readings are deduplicated. At least two readings are needed for a distance. Unknown vehicles remain visible under Unknown depot/model; no-telemetry roster-days are labelled missing. Null precipitation gets an Unknown weather bucket; precipitation >=1 mm is Wet, otherwise Dry.

“Trusted” means these checks passed, not that the reading is guaranteed physically correct. A plausible-looking monotonic error can pass. The conservative day policy may withhold usable partial information. Unassignable rejects are counted separately and cannot be attached to a particular vehicle-day.

## Tests and failure behavior

```bash
python -m pytest fleet_activity/tests -q
```

Tests execute the actual notebook cells with small fixtures, plus API mocks. The full three-notebook run verifies actual malformed-file parsing, SQL extraction and Delta persistence. Tests cover resets, dips/rebounds, spikes, conflicts, missing telemetry, missing weather, join multiplication, period boundaries, and HTTP/timeout failures.

The API makes at most three attempts for transient failures (two retries) with a 30-second request timeout. Exhausted errors, wrong units, unexpected dates or invalid payloads stop before final Gold publication. Rerunning fully replaces these demo tables and their schemas; it does not append duplicates. Keep these output paths dedicated to this project. **There is no cross-table transaction:** a failure can leave newer intermediate tables beside older Gold/export files. Use the runner status and rerun from saved inputs.

## Platform boundary

The local pipeline is validated with Spark/Delta. The [Databricks companion](databricks/README.md) uses Unity Catalog managed tables and a volume, with the same business transformations. It explicitly replays saved real weather responses: the cloud live API attempt received HTTP 429 and stopped before Gold. See the evidence page for the completed platform checks. No remote database credentials or cloud account are required for the local run. SQLite is not a claimed remote JDBC source.

Study one stage notebook at a time. Each step has a visible check; the appendix contains export and evidence code. Start with `parse_daily` when studying the weather helper; its retry/cache code can wait.

The generator is source infrastructure; `run_notebook.py` is execution infrastructure. You can study the notebook first and recreate those helpers later. See [REBUILD.md](REBUILD.md).
