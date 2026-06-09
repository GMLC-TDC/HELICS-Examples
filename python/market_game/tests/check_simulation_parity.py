"""Parity checks for the pure-Python market-game simulator."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sys


MARKET_GAME_DIR = Path(__file__).resolve().parents[1]
if str(MARKET_GAME_DIR) not in sys.path:
    sys.path.insert(0, str(MARKET_GAME_DIR))

from simulation.config import DEFAULT_CONFIG
from simulation.simulator import run_episode


BATTERY_CAPACITY = DEFAULT_CONFIG.battery_capacity
BATTERY_MAX_CHARGE = DEFAULT_CONFIG.max_charge
BATTERY_MAX_DISCHARGE = DEFAULT_CONFIG.max_discharge


@dataclass
class FlattenDemandPolicy:
    name: str = "FlattenDemandHouse"

    def reset(self) -> None:
        pass

    def compute_demand(
        self,
        price: float,
        hour: int,
        battery_charge: float,
        demand: list[float],
        price_history: list[float],
    ) -> float:
        del price, price_history
        base_demand = demand[hour]
        target_demand = sum(demand) / len(demand)
        desired_change = target_demand - base_demand
        if desired_change > 0.0:
            charge_amount = min(
                desired_change,
                BATTERY_MAX_CHARGE,
                BATTERY_CAPACITY - battery_charge,
            )
            return base_demand + charge_amount
        discharge_amount = min(abs(desired_change), BATTERY_MAX_DISCHARGE, battery_charge)
        return base_demand - discharge_amount


@dataclass
class FullCyclePolicy:
    name: str = "FullCycleHouse"
    charging: bool = True

    def reset(self) -> None:
        self.charging = True

    def compute_demand(
        self,
        price: float,
        hour: int,
        battery_charge: float,
        demand: list[float],
        price_history: list[float],
    ) -> float:
        del price, price_history
        if self.charging and battery_charge >= BATTERY_CAPACITY:
            self.charging = False
        elif (not self.charging) and battery_charge <= 0.0:
            self.charging = True
        if self.charging:
            charge_amount = min(BATTERY_MAX_CHARGE, BATTERY_CAPACITY - battery_charge)
            return demand[hour] + charge_amount
        discharge_amount = min(BATTERY_MAX_DISCHARGE, battery_charge)
        return demand[hour] - discharge_amount


@dataclass
class PriceAwarePolicy:
    name: str = "PriceAwareHouse"

    def reset(self) -> None:
        pass

    def reserve_target(self, hour: int) -> float:
        if hour < 12:
            return 4.0
        if hour < 18:
            return 8.0
        if hour < 21:
            return 3.0
        return 0.0

    def compute_demand(
        self,
        price: float,
        hour: int,
        battery_charge: float,
        demand: list[float],
        price_history: list[float],
    ) -> float:
        del price_history
        base_demand = demand[hour]
        remaining_capacity = BATTERY_CAPACITY - battery_charge
        reserve = self.reserve_target(hour)
        available_discharge = max(0.0, battery_charge - reserve)
        if price <= 0.12:
            charge_amount = min(BATTERY_MAX_CHARGE, remaining_capacity)
            return base_demand + charge_amount
        if price <= 0.19 and battery_charge < reserve:
            charge_amount = min(BATTERY_MAX_CHARGE, remaining_capacity, reserve - battery_charge)
            return base_demand + charge_amount
        if price >= 0.49:
            discharge_amount = min(BATTERY_MAX_DISCHARGE, battery_charge)
            return base_demand - discharge_amount
        if price >= 0.25 and available_discharge > 0.0:
            discharge_amount = min(BATTERY_MAX_DISCHARGE, available_discharge)
            return base_demand - discharge_amount
        if hour >= 21 and battery_charge > 0.0:
            discharge_amount = min(BATTERY_MAX_DISCHARGE, battery_charge)
            return base_demand - discharge_amount
        return base_demand


EXPECTED_STOCK = {
    "FlattenDemandHouse": (127.0, 35.446666666666665, 7.0),
    "FullCycleHouse": (120.0, 47.74666666666667, 0.0),
    "PriceAwareHouse": (125.0, 21.953333333333333, 5.0),
}


def run_check() -> None:
    result = run_episode([FlattenDemandPolicy(), FullCyclePolicy(), PriceAwarePolicy()])
    for house in result.houses:
        expected_load, expected_cost, expected_battery = EXPECTED_STOCK[house.policy.name]
        assert abs(house.total_load - expected_load) < 1e-9, house.policy.name
        assert abs(house.total_cost - expected_cost) < 1e-9, house.policy.name
        assert abs(house.battery.energy - expected_battery) < 1e-9, house.policy.name


if __name__ == "__main__":
    run_check()
    print("simulation parity: ok")
