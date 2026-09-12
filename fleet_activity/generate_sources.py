"""Make fictional telemetry and a fleet database for the August 2026 demo."""

import json
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
import random
import sqlite3


def generate_sources(output_dir):
    output_dir = Path(output_dir)
    telemetry_dir = output_dir / "telemetry"
    telemetry_dir.mkdir(parents=True, exist_ok=True)
    random_numbers = random.Random(42)
    depots = [
        ("CHI", "Chicago", 41.88, -87.63),
        ("DAL", "Dallas", 32.78, -96.80),
    ]
    vehicles = [
        (f"EV{number:03}", "Model A" if number % 2 else "Model B",
         "CHI" if number <= 12 else "DAL")
        for number in range(1, 25)
    ]
    # This small database represents a static fleet-management snapshot.
    with sqlite3.connect(output_dir / "fleet.sqlite") as database:
        database.execute("PRAGMA foreign_keys = ON")
        database.execute("CREATE TABLE IF NOT EXISTS depots (depot_id TEXT PRIMARY KEY, depot_name TEXT NOT NULL, latitude REAL NOT NULL, longitude REAL NOT NULL)")
        database.execute("CREATE TABLE IF NOT EXISTS vehicles (vehicle_id TEXT PRIMARY KEY, model TEXT NOT NULL, depot_id TEXT NOT NULL REFERENCES depots(depot_id))")
        database.execute("DELETE FROM vehicles")
        database.execute("DELETE FROM depots")
        database.executemany("INSERT INTO depots VALUES (?, ?, ?, ?)", depots)
        database.executemany("INSERT INTO vehicles VALUES (?, ?, ?)", vehicles)

    odometers = {vehicle[0]: 10000.0 + i * 1000 for i, vehicle in enumerate(vehicles)}
    for day_number in range(30):
        day = date(2026, 8, 1) + timedelta(days=day_number)
        readings = []
        for vehicle_id, _, _ in vehicles:
            moving = random_numbers.random() > 0.2
            for reading_number in range(6):
                if reading_number:
                    odometers[vehicle_id] += random_numbers.uniform(4, 18) if moving else 0
                reading = {
                    "vehicle_id": vehicle_id,
                    "event_timestamp": datetime(day.year, day.month, day.day, 8 + 2 * reading_number, tzinfo=timezone.utc).isoformat(),
                    "odometer_km": round(odometers[vehicle_id], 2),
                }
                # A few deliberate problems, each used in a later exercise.
                if vehicle_id == "EV002" and day_number == 2 and reading_number == 2:
                    reading["odometer_km"] = -1.0
                if vehicle_id == "EV003" and day_number == 3 and reading_number == 2:
                    reading["odometer_km"] -= 100.0
                if vehicle_id == "EV006" and day_number == 6:
                    continue  # No telemetry is unknown activity, not zero activity.
                if vehicle_id == "EV007" and day_number == 7 and reading_number > 0:
                    continue
                readings.append(reading)
                if vehicle_id == "EV004" and day_number == 4 and reading_number == 2:
                    readings.append({**reading, "odometer_km": reading["odometer_km"] + 100.0})
                if vehicle_id == "EV005" and day_number == 5 and reading_number == 2:
                    readings.append(reading.copy())
        if day_number == 0:
            readings.extend([
                {"vehicle_id": None, "event_timestamp": "2026-08-01T08:00:00Z", "odometer_km": 100.0},
                {"vehicle_id": "EV008", "event_timestamp": "not-a-time", "odometer_km": 100.0},
                {"vehicle_id": "UNKNOWN", "event_timestamp": "2026-08-01T08:00:00Z", "odometer_km": 10.0},
                {"vehicle_id": "UNKNOWN", "event_timestamp": "2026-08-01T10:00:00Z", "odometer_km": 20.0},
            ])
        path = telemetry_dir / f"{day}.jsonl"
        path.write_text("".join(json.dumps(row) + "\n" for row in readings))
        if day_number == 0:
            with path.open("a") as file:
                file.write('{"vehicle_id": broken json\n')
    print(f"Created 30 telemetry files, 24 vehicles and 2 depots in {output_dir}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path(__file__).parent / "data" / "sources")
    generate_sources(parser.parse_args().output)
