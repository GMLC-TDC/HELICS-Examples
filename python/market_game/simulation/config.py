"""Configuration objects and demand profiles for the market game."""

from __future__ import annotations

from dataclasses import dataclass, field
import math
import random


PROFILE1_DEMAND = [
    2,
    1,
    1,
    1,
    2,
    4,
    6,
    8,
    9,
    7,
    5,
    4,
    3,
    4,
    5,
    7,
    9,
    12,
    10,
    7,
    5,
    4,
    2,
    2,
]

SOLAR_DEMAND_BASE = [
    2,
    2,
    2,
    2,
    3,
    4,
    5,
    2,
    -4,
    -6,
    -7,
    -8,
    -7,
    -6,
    -3,
    1,
    4,
    8,
    10,
    11,
    10,
    7,
    5,
    3,
]

PROFILE_TYPES = (
    "profile1",
    "profile_solar",
    "flat",
    "random",
    "spike",
    "dspike",
)


@dataclass(frozen=True)
class MarketGameConfig:
    """Rules/configuration for one market-game episode."""

    episode_hours: int = 24
    initial_price: float = 0.5
    initial_battery: float = 0.0
    battery_capacity: float = 20.0
    max_charge: float = 5.0
    max_discharge: float = 10.0
    demand_profile: list[float] = field(default_factory=lambda: list(PROFILE1_DEMAND))
    allow_negative_load: bool = True

    def __post_init__(self) -> None:
        """Fail fast on invalid rule settings before simulation starts."""
        _validate_positive_int(self.episode_hours, "episode_hours")
        _validate_finite(self.initial_price, "initial_price")
        _validate_finite(self.initial_battery, "initial_battery")
        _validate_positive_number(self.battery_capacity, "battery_capacity")
        _validate_positive_number(self.max_charge, "max_charge")
        _validate_positive_number(self.max_discharge, "max_discharge")
        if not 0.0 <= self.initial_battery <= self.battery_capacity:
            raise ValueError("initial_battery must be between 0 and battery_capacity")
        if len(self.demand_profile) < self.episode_hours:
            raise ValueError("demand_profile must contain at least episode_hours values")
        for index, value in enumerate(self.demand_profile[: self.episode_hours]):
            _validate_finite(value, f"demand_profile[{index}]")


def demand_profile(profile_type: str, rng: random.Random | None = None) -> list[float]:
    """Return a 24-hour base demand profile matching the HELICS market maker."""
    rng = rng or random
    if profile_type == "profile1":
        return list(PROFILE1_DEMAND)
    if profile_type == "profile_solar":
        return [value * 3.0 for value in SOLAR_DEMAND_BASE]
    if profile_type == "flat":
        return [5] * 24
    if profile_type == "random":
        elements = [rng.random() for _ in range(24)]
        multiplier = 120.0 / sum(elements)
        return [value * multiplier for value in elements]
    if profile_type == "spike":
        profile = [4] * 24
        profile[rng.randint(0, 23)] = 28
        return profile
    if profile_type == "dspike":
        profile = [3] * 24
        profile[rng.randint(0, 23)] += 24
        profile[rng.randint(0, 23)] += 24
        return profile
    choices = ", ".join(PROFILE_TYPES)
    raise ValueError(f"unknown demand profile {profile_type!r}; choices: {choices}")


def _validate_positive_int(value: int, field_name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ValueError(f"{field_name} must be an integer >= 1")


def _validate_positive_number(value: float, field_name: str) -> None:
    _validate_finite(value, field_name)
    if value <= 0.0:
        raise ValueError(f"{field_name} must be > 0")


def _validate_finite(value: float, field_name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{field_name} must be numeric")
    if not math.isfinite(float(value)):
        raise ValueError(f"{field_name} must be finite")


DEFAULT_CONFIG = MarketGameConfig()
