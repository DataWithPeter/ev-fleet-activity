"""Check the active stage notebooks and preserve the old cloud proof honestly."""
import hashlib
import json
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
    proof = json.loads((root / "evidence/databricks_run.json").read_text())
    assert proof["source_notebook_sha256"] == hashlib.sha256((root / "evidence/archive/databricks_before_power_bi.ipynb").read_bytes()).hexdigest()
    assert proof["setup_notebook_sha256"] == hashlib.sha256(setup_path.read_bytes()).hexdigest()
