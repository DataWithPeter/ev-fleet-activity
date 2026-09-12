"""Fetch a small, reproducible Open-Meteo snapshot for the two demo depots."""

from datetime import date, datetime, timedelta, timezone
import json
import math
from pathlib import Path
import time

import requests


API_URL = "https://archive-api.open-meteo.com/v1/archive"


def request_weather(parameters):
    # Retry transient HTTP failures, but never turn an outage into missing weather.
    for attempt in range(3):
        try:
            response = requests.get(API_URL, params=parameters, timeout=30)
        except (requests.Timeout, requests.ConnectionError):
            if attempt == 2:
                raise
            time.sleep(2 ** attempt)
            continue
        if response.status_code == 429 or response.status_code >= 500:
            if attempt < 2:
                time.sleep(2 ** attempt)
                continue
        response.raise_for_status()
        if response.status_code != 200:
            raise ValueError(f"Expected HTTP 200, received {response.status_code}")
        payload = response.json()
        if not isinstance(payload, dict):
            raise ValueError("Weather response must be a JSON object")
        if payload.get("error"):
            raise ValueError(f"Open-Meteo error: {payload.get('reason')}")
        return payload


def parse_daily(payload, start_date, end_date):
    if not isinstance(payload, dict):
        raise ValueError("Weather response must be a JSON object")
    if payload.get("error") or payload.get("utc_offset_seconds") != 0:
        raise ValueError("Weather response must be successful and use UTC days")
    daily = payload.get("daily", {})
    units = payload.get("daily_units", {})
    fields = ["time", "temperature_2m_mean", "precipitation_sum"]
    for field in fields:
        if not isinstance(daily.get(field), list):
            raise ValueError("Weather response is missing daily arrays")

    expected_dates = []
    current_day = start_date
    while current_day <= end_date:
        expected_dates.append(current_day.isoformat())
        current_day = current_day + timedelta(days=1)
    if daily["time"] != expected_dates:
        raise ValueError("Weather dates do not match the requested period")
    for field in fields:
        if len(daily[field]) != len(expected_dates):
            raise ValueError("Weather array lengths do not match the requested period")
    if units.get("temperature_2m_mean") != "°C" or units.get("precipitation_sum") != "mm":
        raise ValueError("Unexpected weather units")
    rows = []
    # The same index in each array describes the same UTC day.
    for i in range(len(expected_dates)):
        day = daily["time"][i]
        temperature = daily["temperature_2m_mean"][i]
        precipitation = daily["precipitation_sum"][i]
        for value in [temperature, precipitation]:
            if value is None:
                continue
            # bool is a Python number subclass, but true/false is not weather.
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise ValueError("Weather values must be finite numbers or null")
            if not math.isfinite(value):
                raise ValueError("Weather values must be finite numbers or null")
        if precipitation is not None and precipitation < 0:
            raise ValueError("Precipitation cannot be negative")
        rows.append((date.fromisoformat(day), temperature, precipitation))
    return rows


def load_weather(depots, start_date, end_date, cache_dir, refresh=False, offline=False):
    cache_dir = Path(cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)
    weather_rows = []
    snapshots = []
    if offline and refresh:
        raise ValueError("Offline mode cannot refresh weather")
    for depot in depots:
        parameters = {
            "latitude": depot["latitude"], "longitude": depot["longitude"],
            "start_date": str(start_date), "end_date": str(end_date),
            "daily": "temperature_2m_mean,precipitation_sum",
            "timezone": "GMT", "temperature_unit": "celsius",
            "precipitation_unit": "mm",
        }
        path = cache_dir / f"{depot['depot_id']}_{start_date}_{end_date}.json"
        if path.exists() and not refresh:
            snapshot = json.loads(path.read_text())
            if snapshot["request"] != parameters:
                raise ValueError("Cached weather request changed; explicitly refresh the snapshot")
            payload = snapshot["response"]
        else:
            if offline:
                raise FileNotFoundError(f"Offline weather snapshot missing: {path}")
            payload = request_weather(parameters)
            snapshot = {"source": API_URL, "request": parameters,
                        "fetched_at": datetime.now(timezone.utc).isoformat(), "response": payload}
        daily_rows = parse_daily(payload, start_date, end_date)
        if not path.exists() or refresh:
            path.write_text(json.dumps(snapshot, indent=2) + "\n")
        for day, temperature, precipitation in daily_rows:
            if temperature is not None:
                temperature = float(temperature)
            if precipitation is not None:
                precipitation = float(precipitation)
            weather_rows.append((depot["depot_id"], day, temperature, precipitation))
        snapshots.append({"file": path.name, "fetched_at": snapshot["fetched_at"], "request": parameters})
    return weather_rows, snapshots
