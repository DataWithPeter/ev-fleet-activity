"""Run Bronze, Silver and Gold in separate kernels and preserve their outputs."""

import json
import os
from datetime import datetime, timezone
from pathlib import Path

import nbformat
from nbclient import NotebookClient


if __name__ == "__main__":
    project_dir = Path(__file__).resolve().parent
    os.environ["FLEET_PROJECT_DIR"] = str(project_dir)
    output_dir = project_dir / "output"
    output_dir.mkdir(exist_ok=True)
    status = {"state": "running", "started_at": datetime.now(timezone.utc).isoformat(), "completed": []}
    status_path = output_dir / "execution_status.json"
    status_path.write_text(json.dumps(status, indent=2))
    try:
        for name in ["01_bronze_ingestion", "02_silver_cleaning", "03_gold_activity"]:
            status["current_notebook"] = name
            status_path.write_text(json.dumps(status, indent=2))
            notebook = nbformat.read(project_dir / "notebooks" / f"{name}.ipynb", as_version=4)
            try:
                # A new client/kernel prevents accidental sharing of Python variables.
                NotebookClient(notebook, timeout=300, kernel_name="python3",
                               resources={"metadata": {"path": str(project_dir)}}).execute()
            finally:
                nbformat.write(notebook, output_dir / f"{name}_executed.ipynb")
            status["completed"].append(name)
            print(f"Passed: {name}", flush=True)
        status["state"] = "succeeded"
    except Exception as error:
        status.update(state="failed", error=str(error))
        raise
    finally:
        status["finished_at"] = datetime.now(timezone.utc).isoformat()
        status_path.write_text(json.dumps(status, indent=2))
    print("Bronze, Silver and Gold passed in separate kernels.")
