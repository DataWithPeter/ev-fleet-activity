"""Make August 2026 sources: baseline by default, expanded_august_v1 explicitly."""

import csv
import hashlib
import json
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
import random
import sqlite3


def generate_baseline_sources(output_dir):
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


# Explicit membership: adding a different event type does not change this group.
READING_CHANGE_EVENT_TYPES = [
    'missing_telemetry', 'insufficient_readings', 'partial_coverage',
    'rejected_reading_in_day', 'odometer_decreased', 'conflicting_timestamp',
    'exact_duplicate',
]


def read_expanded_inputs(scenario_dir):
    """Step 1: read the settings and the sole defect input, then check them."""
    scenario_dir = Path(scenario_dir)
    config = json.loads((scenario_dir / 'scenario.json').read_text())
    if config['scenario'] != 'expanded_august_v1':
        raise ValueError('Unexpected scenario configuration')
    if config['events_file'] != 'events.csv':
        raise ValueError('Expanded defects must come from events.csv')
    with (scenario_dir / 'events.csv').open(newline='') as file:
        events = list(csv.DictReader(file))
    event_types = ['missing_telemetry', 'insufficient_readings', 'partial_coverage',
        'rejected_reading_in_day', 'odometer_decreased', 'conflicting_timestamp',
        'exact_duplicate', 'unregistered_vehicle', 'missing_vehicle',
        'invalid_timestamp', 'outside_report_period', 'malformed_json']
    if len({event['event_id'] for event in events}) != len(events):
        raise ValueError('Duplicate event ID')
    for event in events:
        if event['event_type'] not in event_types:
            raise ValueError('Unknown event type: ' + event['event_type'])
    start_date = date.fromisoformat(config['start_date'])
    end_date = date.fromisoformat(config['end_date'])
    for event in events:
        if not start_date <= date.fromisoformat(event['source_date']) <= end_date:
            raise ValueError('Event source file falls outside the reporting period')
    return config, events


def write_expanded_roster(output_dir, config, events):
    """Step 2: build the static roster, check event IDs, and save SQLite."""
    vehicles = []
    for first, last, model, depot in config['fleet_groups']:
        for number in range(first, last + 1):
            vehicles.append((f'EV{number:03}', model, depot))
    vehicles.sort()
    registered_ids = {vehicle for vehicle, _, _ in vehicles}
    for event in events:
        if event['event_type'] in READING_CHANGE_EVENT_TYPES and event['vehicle_id'] not in registered_ids:
            raise ValueError('Reading-change event needs a registered vehicle')
        if event['event_type'] == 'unregistered_vehicle' and event['vehicle_id'] in registered_ids:
            raise ValueError('Unregistered event must not use a roster ID')
    with sqlite3.connect(output_dir / 'fleet.sqlite') as database:
        database.execute('PRAGMA foreign_keys = ON')
        database.execute('CREATE TABLE IF NOT EXISTS depots (depot_id TEXT PRIMARY KEY, depot_name TEXT NOT NULL, latitude REAL NOT NULL, longitude REAL NOT NULL)')
        database.execute('CREATE TABLE IF NOT EXISTS vehicles (vehicle_id TEXT PRIMARY KEY, model TEXT NOT NULL, depot_id TEXT NOT NULL REFERENCES depots(depot_id))')
        database.execute('DELETE FROM vehicles')
        database.execute('DELETE FROM depots')
        database.executemany('INSERT INTO depots VALUES (?, ?, ?, ?)', config['depots'])
        database.executemany('INSERT INTO vehicles VALUES (?, ?, ?)', vehicles)
    return vehicles


def write_expanded_telemetry(output_dir, config, events, vehicles):
    """Step 3: write each day's normal readings with its CSV events applied."""
    telemetry_dir = output_dir / 'telemetry'
    telemetry_dir.mkdir(parents=True, exist_ok=True)
    random_numbers = random.Random(config['seed'])
    start_date = date.fromisoformat(config['start_date'])
    end_date = date.fromisoformat(config['end_date'])
    low_multiplier, high_multiplier = config['vehicle_multiplier_range']
    multipliers = {vehicle: random_numbers.uniform(low_multiplier, high_multiplier)
                   for vehicle, _, _ in vehicles}
    odometers = {vehicle: float(config['initial_odometer_km'] + i * config['odometer_spacing_km'])
                 for i, (vehicle, _, _) in enumerate(vehicles)}
    current_day = start_date
    while current_day <= end_date:
        day_text = current_day.isoformat()
        day_events = [event for event in events if event['source_date'] == day_text]
        readings = []
        for vehicle, model, _ in vehicles:
            profile = config['profiles'][model]
            probability = (profile['weekday_probability'] if current_day.weekday() < 5
                           else profile['weekend_probability'])
            moving = random_numbers.random() < probability
            normal = {}
            for i, hour in enumerate(config['reading_hours']):
                if i and moving:
                    odometers[vehicle] += random_numbers.uniform(profile['low_km'], profile['high_km']) * multipliers[vehicle]
                normal[hour] = {'vehicle_id': vehicle,
                    'event_timestamp': datetime(current_day.year, current_day.month,
                        current_day.day, hour, tzinfo=timezone.utc).isoformat(),
                    'odometer_km': round(odometers[vehicle], 2)}
            retained_hours = list(config['reading_hours'])
            extra_readings = []
            # Events alter emitted copies only; the underlying odometer stays normal.
            for event in day_events:
                kind = event['event_type']
                if event['vehicle_id'] != vehicle or kind not in READING_CHANGE_EVENT_TYPES:
                    continue
                if event['event_date'] != day_text:
                    raise ValueError('Reading-change date does not match source date')
                if kind == 'missing_telemetry':
                    retained_hours = []
                elif kind in ['insufficient_readings', 'partial_coverage']:
                    retained_hours = [int(hour) for hour in event['keep_hours'].split(';')]
                elif kind == 'rejected_reading_in_day':
                    normal[int(event['reading_hour'])]['odometer_km'] = float(event['value'])
                elif kind == 'odometer_decreased':
                    normal[int(event['reading_hour'])]['odometer_km'] = (
                        normal[int(event['reference_hour'])]['odometer_km'] + float(event['value']))
                elif kind == 'conflicting_timestamp':
                    original = normal[int(event['reading_hour'])]
                    extra_readings.append({**original, 'odometer_km': original['odometer_km'] + float(event['value'])})
                elif kind == 'exact_duplicate':
                    extra_readings.append(normal[int(event['reading_hour'])].copy())
            readings.extend(normal[hour] for hour in retained_hours)
            readings.extend(extra_readings)
        raw_lines = []
        for event in day_events:
            kind = event['event_type']
            if kind == 'unregistered_vehicle':
                event_day = date.fromisoformat(event['event_date'])
                for i, hour in enumerate(event['keep_hours'].split(';')):
                    readings.append({'vehicle_id': event['vehicle_id'],
                        'event_timestamp': datetime(event_day.year, event_day.month, event_day.day,
                                                   int(hour), tzinfo=timezone.utc).isoformat(),
                        'odometer_km': float(event['value']) + i * float(event['increment_km'])})
            elif kind in ['missing_vehicle', 'invalid_timestamp', 'outside_report_period']:
                readings.append({'vehicle_id': event['vehicle_id'] or None,
                    'event_timestamp': event['event_timestamp'], 'odometer_km': float(event['value'])})
            elif kind == 'malformed_json':
                raw_lines.append(event['raw_line'])
        path = telemetry_dir / f'{day_text}.jsonl'
        path.write_text(''.join(json.dumps(row) + '\n' for row in readings)
                        + ''.join(line + '\n' for line in raw_lines))
        current_day += timedelta(days=1)

def generate_expanded_sources(output_dir, scenario_dir):
    """Run three plain steps, then record the input provenance."""
    scenario_dir = Path(scenario_dir)
    config, events = read_expanded_inputs(scenario_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    vehicles = write_expanded_roster(output_dir, config, events)
    write_expanded_telemetry(output_dir, config, events, vehicles)
    # Provenance only. The independent expected CSV is never read by this generator.
    manifest = {'scenario': config['scenario'], 'seed': config['seed'],
        'period': [config['start_date'], config['end_date']], 'event_count': len(events),
        'input_sha256': {name: hashlib.sha256((scenario_dir / name).read_bytes()).hexdigest()
                         for name in ['scenario.json', 'events.csv']}}
    (output_dir / 'scenario_manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(f"Created {config['scenario']}: {len(vehicles)} vehicles from scenario.json; {len(events)} CSV events")


def generate_sources(output_dir, scenario='baseline', scenario_dir=None):
    if scenario not in ['baseline', 'expanded_august_v1']:
        raise ValueError('Unknown scenario: ' + scenario)
    directory = Path(output_dir) / 'telemetry'
    allowed = {f'2026-08-{day:02}.jsonl' for day in range(1, 31)}
    if directory.exists() and any(p.name not in allowed for p in directory.glob('*.jsonl')):
        raise ValueError('Unexpected telemetry file; use a clean source directory')
    if scenario == 'baseline':
        generate_baseline_sources(output_dir)
        (Path(output_dir) / 'scenario_manifest.json').write_text(json.dumps({'scenario': 'baseline'}, indent=2) + '\n')
    else:
        if scenario_dir is None:
            scenario_dir = Path(__file__).parent / 'scenarios' / scenario
        generate_expanded_sources(output_dir, scenario_dir)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path(__file__).parent / "data" / "sources")
    parser.add_argument("--scenario", choices=["baseline", "expanded_august_v1"], default="baseline")
    parser.add_argument("--scenario-dir", type=Path, help="Directory containing scenario.json and events.csv")
    arguments = parser.parse_args()
    generate_sources(arguments.output, arguments.scenario, arguments.scenario_dir)
