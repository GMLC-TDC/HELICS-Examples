import json
from pathlib import Path

import pytest


RESULTS_FILE = Path(__file__).with_name("fundamental_default_results.json")
SAMPLE_PERIOD_SECONDS = 60
SAMPLE_COUNT = 7 * 24 * 60

EXPECTED_VOLTAGES = {
    "Charger/EV1_voltage": 240.0,
    "Charger/EV2_voltage": 240.0,
    "Charger/EV3_voltage": 240.0,
    "Charger/EV4_voltage": 240.0,
    "Charger/EV5_voltage": 630.0,
}

EXPECTED_CURRENT_PROFILES = {
    "Battery/EV1_current": {"initial": 4.613610, "first_zero_time": 108960.0},
    "Battery/EV2_current": {"initial": 5.703422, "first_zero_time": 114120.0},
    "Battery/EV3_current": {"initial": 2.932551, "first_zero_time": 87000.0},
    "Battery/EV4_current": {"initial": 2.698448, "first_zero_time": 321120.0},
    "Battery/EV5_current": {"initial": 8.272059, "first_zero_time": 53400.0},
}


@pytest.fixture(scope="module")
def series_by_key():
    with RESULTS_FILE.open(encoding="utf-8") as results_file:
        points = json.load(results_file)["points"]

    series = {}
    for point in points:
        point["value"] = float(point["value"])
        series.setdefault(point["key"], []).append(point)

    return series


def test_records_every_expected_publication(series_by_key):
    expected_keys = set(EXPECTED_VOLTAGES) | set(EXPECTED_CURRENT_PROFILES)

    assert set(series_by_key) == expected_keys
    assert all(len(points) == SAMPLE_COUNT for points in series_by_key.values())


@pytest.mark.parametrize("key, expected_voltage", EXPECTED_VOLTAGES.items())
def test_charger_voltage_profiles(series_by_key, key, expected_voltage):
    points = series_by_key[key]

    assert points[0]["time"] == pytest.approx(SAMPLE_PERIOD_SECONDS)
    assert points[-1]["time"] == pytest.approx(SAMPLE_COUNT * SAMPLE_PERIOD_SECONDS)
    assert all(point["value"] == expected_voltage for point in points)


@pytest.mark.parametrize("key, expected", EXPECTED_CURRENT_PROFILES.items())
def test_battery_current_profiles(series_by_key, key, expected):
    points = series_by_key[key]
    values = [point["value"] for point in points]

    assert points[0]["time"] == pytest.approx(SAMPLE_PERIOD_SECONDS, abs=1e-6)
    assert points[-1]["time"] == pytest.approx(
        SAMPLE_COUNT * SAMPLE_PERIOD_SECONDS, abs=1e-6
    )
    assert values[0] == pytest.approx(expected["initial"], abs=1e-6)
    assert all(current >= 0 for current in values)
    assert all(
        current >= next_current
        for current, next_current in zip(values, values[1:])
    )

    first_zero = next(point for point in points if point["value"] == 0)
    assert first_zero["time"] == pytest.approx(expected["first_zero_time"], abs=1e-6)


def test_aggregate_charging_metrics(series_by_key):
    current_series = [series_by_key[key] for key in EXPECTED_CURRENT_PROFILES]
    voltage_keys = [
        key.replace("Battery", "Charger").replace("current", "voltage")
        for key in EXPECTED_CURRENT_PROFILES
    ]
    voltages = [EXPECTED_VOLTAGES[key] for key in voltage_keys]

    power_watts = [
        sum(
            points[index]["value"] * voltage
            for points, voltage in zip(current_series, voltages)
        )
        for index in range(SAMPLE_COUNT)
    ]
    energy_kwh = sum(power_watts) * SAMPLE_PERIOD_SECONDS / 3_600_000

    assert max(power_watts) == pytest.approx(9038.92461, rel=1e-6)
    assert energy_kwh == pytest.approx(143.279376593, rel=1e-6)
