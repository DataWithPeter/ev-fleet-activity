"""Check business-cell parity and helpers in the active stage notebooks."""
from pathlib import Path

import nbformat


def test_databricks_companion_keeps_business_cells():
    root = Path(__file__).parents[1]
    for name in ["01_bronze_ingestion", "02_silver_cleaning", "03_gold_activity"]:
        local = nbformat.read(root / "notebooks" / f"{name}.ipynb", as_version=4)
        cloud = nbformat.read(root / "databricks" / f"{name}.ipynb", as_version=4)
        for notebook in [local, cloud]:
            nbformat.validate(notebook)
            for cell in notebook.cells:
                if cell.cell_type == "code" and cell.metadata["tags"][0] != "prepare":
                    compile(cell.source, name, "exec")
        a = {c.metadata["tags"][0]: c.source for c in local.cells if c.cell_type == "code"}
        b = {c.metadata["tags"][0]: c.source for c in cloud.cells if c.cell_type == "code"}
        for tag in ["parse", "validate", "deduplicate", "conflicts", "sequence", "day_issues",
                    "accepted", "quarantine", "daily", "report_dates", "fleet_join", "report", "export"]:
            if tag in a:
                assert b[tag] == a[tag], tag
        if "gold" in a:
            assert b["gold"].split("gold_table =")[0] == a["gold"].split("gold_path =")[0]
        if "weather" in a:
            assert b["weather"].split("weather.write")[0] == a["weather"].split("weather.write")[0]
        if "fleet_check" in a:
            assert b["fleet_check"].split("fleet.write")[0] == a["fleet_check"].split("fleet.write")[0]
        if "weather_ingest" in a:
            assert b["weather_ingest"].split("offline =", 1)[1].split("weather.write")[0] == a["weather_ingest"].split("offline =", 1)[1].split("weather.write")[0]
    setup_path = root / "databricks/00_prepare_demo.ipynb"
    setup = nbformat.read(setup_path, as_version=4)
    cells = {c.metadata["tags"][0]: c.source for c in setup.cells if c.cell_type == "code"}
    assert cells["weather_helpers"] == (root / "weather.py").read_text()
    assert cells["source_generator"] == (root / "generate_sources.py").read_text().split('if __name__ == "__main__":')[0]


def test_databricks_quality_companion_keeps_business_cells():
    root = Path(__file__).parents[1]
    local = nbformat.read(root / "notebooks/04_gold_quality.ipynb", as_version=4)
    cloud = nbformat.read(root / "databricks/04_gold_quality.ipynb", as_version=4)
    assert len(local.cells) == len(cloud.cells)
    for notebook in [local, cloud]:
        nbformat.validate(notebook)
        for cell in notebook.cells:
            if cell.cell_type == "code":
                compile(cell.source, "04_gold_quality", "exec")
    for a, b in zip(local.cells, cloud.cells):
        assert a.cell_type == b.cell_type
        if a.cell_type == "markdown":
            assert a.source == b.source
        else:
            assert a.metadata["tags"] == b.metadata["tags"]
            if a.metadata["tags"][0] not in ["setup", "publish"]:
                assert a.source == b.source
    cloud_code = {c.metadata["tags"][0]: c.source for c in cloud.cells if c.cell_type == "code"}
    for name in ["bronze_telemetry", "silver_telemetry", "quarantine_telemetry",
                 "silver_day_issues", "gold_daily_vehicle_activity"]:
        assert f'spark.table(schema_name + ".{name}")' in cloud_code["setup"]
    expected_publish = local.cells[-1].source
    for name in ["gold_vehicle_day_quality", "gold_vehicle_day_issue", "gold_record_reconciliation"]:
        expected_publish = expected_publish.replace(
            f'.save(str(output_dir / "delta" / "{name}"))',
            f'.saveAsTable(schema_name + ".{name}")')
    assert cloud.cells[-1].source == expected_publish
