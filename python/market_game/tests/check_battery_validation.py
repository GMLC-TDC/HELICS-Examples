"""Checks for market-game battery validation helpers."""

from __future__ import annotations

from pathlib import Path
import sys


MARKET_GAME_DIR = Path(__file__).resolve().parents[1]
if str(MARKET_GAME_DIR) not in sys.path:
    sys.path.insert(0, str(MARKET_GAME_DIR))

from battery import Battery, check_valid, ensure_valid


def penalty_cost(proposed: float, valid: float) -> float:
    return 20.0 * abs(proposed - valid)


def run_check() -> None:
    battery = Battery(0.0)
    assert ensure_valid(100.0, 2.0, battery) == 7.0
    assert check_valid(100.0, 2.0, battery) == (
        "listed battery charge rate exceeds maximum charge rate"
    )
    assert penalty_cost(100.0, ensure_valid(100.0, 2.0, battery)) == 1860.0
    battery.change(ensure_valid(100.0, 2.0, battery) - 2.0)
    assert battery.energy == 5.0

    battery = Battery(19.0)
    assert ensure_valid(100.0, 2.0, battery) == 3.0
    assert check_valid(100.0, 2.0, battery) == (
        "listed battery charge rate exceeds available battery storage capacity"
    )
    assert penalty_cost(100.0, ensure_valid(100.0, 2.0, battery)) == 1940.0
    battery.change(ensure_valid(100.0, 2.0, battery) - 2.0)
    assert battery.energy == 20.0

    battery = Battery(0.0)
    assert ensure_valid(-100.0, 2.0, battery) == 2.0
    assert check_valid(-100.0, 2.0, battery) == (
        "listed consumption exceeds available battery energy"
    )
    assert penalty_cost(-100.0, ensure_valid(-100.0, 2.0, battery)) == 2040.0
    battery.change(ensure_valid(-100.0, 2.0, battery) - 2.0)
    assert battery.energy == 0.0

    battery = Battery(20.0)
    assert ensure_valid(-100.0, 12.0, battery) == 2.0
    assert check_valid(-100.0, 12.0, battery) == (
        "listed consumption exceeds max battery discharge rate"
    )
    assert penalty_cost(-100.0, ensure_valid(-100.0, 12.0, battery)) == 2040.0
    battery.change(ensure_valid(-100.0, 12.0, battery) - 12.0)
    assert battery.energy == 10.0

    battery = Battery(0.0)
    assert ensure_valid(7.0, 2.0, battery) == 7.0
    assert check_valid(7.0, 2.0, battery) == ""
    assert penalty_cost(7.0, ensure_valid(7.0, 2.0, battery)) == 0.0

    battery = Battery(20.0)
    assert ensure_valid(2.0, 12.0, battery) == 2.0
    assert check_valid(2.0, 12.0, battery) == ""


if __name__ == "__main__":
    run_check()
    print("battery validation: ok")
