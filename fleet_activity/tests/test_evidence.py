"""Tie execution evidence to all three active source notebooks."""
import hashlib
import json
from pathlib import Path

import nbformat


def test_published_evidence_matches_source_and_data():
    root = Path(__file__).parents[1]
    for name in ["01_bronze_ingestion", "02_silver_cleaning", "03_gold_activity"]:
        source = nbformat.read(root / "notebooks" / f"{name}.ipynb", as_version=4)
        executed = nbformat.read(root / "evidence" / f"{name}_executed.ipynb", as_version=4)
        nbformat.validate(source)
        nbformat.validate(executed)
        assert [c.source for c in source.cells] == [c.source for c in executed.cells]
        for cell in executed.cells:
            if cell.cell_type == "code":
                assert cell.execution_count is not None
                assert all(output.output_type != "error" for output in cell.outputs)
    summary = json.loads((root / "evidence/run_summary.json").read_text())
    data = (root / "evidence/daily_vehicle_activity.csv").read_bytes()
    assert hashlib.sha256(data).hexdigest() == summary["business_output_sha256"]
    assert b"\r\n" not in data
