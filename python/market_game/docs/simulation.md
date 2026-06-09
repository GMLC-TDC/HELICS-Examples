# Pure-Python Market Game Simulation

The `simulation/` package mirrors the market-game rules without starting HELICS
federates. It is useful for fast checks of pricing, battery validation, and
strategy behavior before running a full co-simulation.

This does not change the HELICS runtime behavior. The existing `market_maker.py`,
`battery.py`, and house federates still run the official game. The simulator is
an additional dependency-free path for tests, examples, and strategy checks.

## Policy Interface

Simulator policies use the same decision surface as house federates:

```python
compute_demand(price, hour, battery_charge, demand, price_history)
```

Arguments:

- `price`: current market price in `$/kWh`
- `hour`: current hour from `0` to `23`
- `battery_charge`: current stored battery energy
- `demand`: the full 24-hour base demand profile
- `price_history`: prices seen so far, including the current hour

The return value is the market-facing load for the current hour. Values above
`demand[hour]` charge the battery. Values below `demand[hour]` discharge it.

## Scope

The simulator covers:

- 24-hour episodes
- the default `profile1` demand profile
- generated `flat`, `random`, `spike`, `dspike`, and `profile_solar` profiles
- the market price curve from `market_maker.py`
- the one-hour price lag
- battery capacity, charge-rate, and discharge-rate limits
- invalid-demand clamping and penalty accounting

The simulator intentionally does not start HELICS, create brokers, plot results,
or load external strategy files.

## Running Checks

From the repository root:

```bash
python3 python/market_game/tests/check_simulation.py
```

The combined check runs the core and parity checks. You can also run them
individually:

```bash
python3 python/market_game/tests/check_simulation_core.py
python3 python/market_game/tests/check_simulation_parity.py
```

The core check validates rule helpers, demand profiles, battery clamping, price
calculation, invalid-demand penalties, and input validation.

The parity check runs the stock example policies through the pure-Python
simulator and verifies the expected 24-hour totals:

| House | Total market load | Total cost | Final battery |
|---|---:|---:|---:|
| `FlattenDemandHouse` | `127.0` | `$35.4467` | `7.0` |
| `FullCycleHouse` | `120.0` | `$47.7467` | `0.0` |
| `PriceAwareHouse` | `125.0` | `$21.9533` | `5.0` |

## Example

```python
from python.market_game.simulation.simulator import run_episode


class FollowDemandPolicy:
    name = "FollowDemandHouse"

    def reset(self):
        pass

    def compute_demand(self, price, hour, battery_charge, demand, price_history):
        return demand[hour]


result = run_episode([FollowDemandPolicy()])
print(result.total_costs())
```
