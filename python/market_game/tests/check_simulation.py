"""Run all pure-Python market-game simulation checks."""

from __future__ import annotations

from pathlib import Path
import sys


TESTS_DIR = Path(__file__).resolve().parent
if str(TESTS_DIR) not in sys.path:
    sys.path.insert(0, str(TESTS_DIR))

from check_simulation_core import run_check as run_core_check
from check_simulation_parity import run_check as run_parity_check


def run_check() -> None:
    run_core_check()
    print("simulation core: ok")
    run_parity_check()
    print("simulation parity: ok")


if __name__ == "__main__":
    run_check()
