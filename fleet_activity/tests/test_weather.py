from datetime import date
from pathlib import Path
import sys

import pytest
import requests

sys.path.insert(0, str(Path(__file__).parents[1]))
import weather


def payload():
    return {
        "utc_offset_seconds": 0,
        "daily_units": {"temperature_2m_mean": "°C", "precipitation_sum": "mm"},
        "daily": {"time": ["2026-08-01", "2026-08-02"],
                  "temperature_2m_mean": [20.0, None], "precipitation_sum": [0.0, None]},
    }


def test_successful_null_weather_is_preserved():
    assert weather.parse_daily(payload(), date(2026, 8, 1), date(2026, 8, 2)) == [
        (date(2026, 8, 1), 20.0, 0.0), (date(2026, 8, 2), None, None)]


@pytest.mark.parametrize("fault", ["timezone", "dates", "length", "units", "error", "negative", "nonfinite", "boolean", "text"])
def test_bad_response_fails(fault):
    value = payload()
    if fault == "timezone": value["utc_offset_seconds"] = -18000
    if fault == "dates": value["daily"]["time"] = ["2026-08-01", "2026-08-01"]
    if fault == "length": value["daily"]["precipitation_sum"] = [0.0]
    if fault == "units": value["daily_units"]["precipitation_sum"] = "inch"
    if fault == "error": value["error"] = True
    if fault == "negative": value["daily"]["precipitation_sum"][0] = -1.0
    if fault == "nonfinite": value["daily"]["temperature_2m_mean"][0] = float("inf")
    if fault == "boolean": value["daily"]["temperature_2m_mean"][0] = True
    if fault == "text": value["daily"]["temperature_2m_mean"][0] = "20"
    with pytest.raises(ValueError):
        weather.parse_daily(value, date(2026, 8, 1), date(2026, 8, 2))


def response(status):
    result = requests.Response()
    result.status_code = status
    result._content = b'{"ok": true}'
    return result


def test_transient_error_retries_and_succeeds(monkeypatch):
    replies = iter([response(429), response(503), response(200)])
    calls = []
    def get(*args, **kwargs):
        calls.append(kwargs)
        return next(replies)
    monkeypatch.setattr(weather.requests, "get", get)
    monkeypatch.setattr(weather.time, "sleep", lambda seconds: None)
    assert weather.request_weather({"timezone": "GMT"}) == {"ok": True}
    assert len(calls) == 3 and all(call["timeout"] == 30 for call in calls)


@pytest.mark.parametrize("status,expected_calls", [(400, 1), (503, 3), (429, 3)])
def test_http_failure_is_not_missing_weather(monkeypatch, status, expected_calls):
    calls = []
    def get(*args, **kwargs):
        calls.append(1)
        return response(status)
    monkeypatch.setattr(weather.requests, "get", get)
    monkeypatch.setattr(weather.time, "sleep", lambda seconds: None)
    with pytest.raises(requests.HTTPError):
        weather.request_weather({})
    assert len(calls) == expected_calls


def test_timeout_is_bounded(monkeypatch):
    calls = []
    def get(*args, **kwargs):
        calls.append(1)
        raise requests.Timeout("simulated")
    monkeypatch.setattr(weather.requests, "get", get)
    monkeypatch.setattr(weather.time, "sleep", lambda seconds: None)
    with pytest.raises(requests.Timeout):
        weather.request_weather({})
    assert len(calls) == 3


def test_snapshot_rerun_does_not_call_api(monkeypatch, tmp_path):
    depots = [{"depot_id": "TEST", "latitude": 41.88, "longitude": -87.63}]
    monkeypatch.setattr(weather, "request_weather", lambda parameters: payload())
    first, snapshots = weather.load_weather(depots, date(2026, 8, 1), date(2026, 8, 2), tmp_path)
    def unexpected_call(parameters):
        raise AssertionError("A rebuild must reuse the saved response")
    monkeypatch.setattr(weather, "request_weather", unexpected_call)
    second, reused = weather.load_weather(depots, date(2026, 8, 1), date(2026, 8, 2), tmp_path)
    assert first == second and snapshots == reused
    with pytest.raises(AssertionError):
        weather.load_weather(depots, date(2026, 8, 1), date(2026, 8, 2), tmp_path, refresh=True)


def test_offline_missing_snapshot_never_calls_api(monkeypatch, tmp_path):
    def unexpected_call(parameters):
        raise AssertionError("Offline mode cannot call the API")
    monkeypatch.setattr(weather, "request_weather", unexpected_call)
    with pytest.raises(FileNotFoundError):
        weather.load_weather([{"depot_id": "TEST", "latitude": 0.0, "longitude": 0.0}],
            date(2026, 8, 1), date(2026, 8, 2), tmp_path, offline=True)
