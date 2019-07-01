# Manager Worker Example

A manager federate sends some values to the worker federates. The workers update the values and sends back the updated values to the manager. The manager doesn't move forward untill all the federates have sent back the value.

## Running

1. In a terminal run, ```helics_broker -f6``` runs with 5 workers and 1 manager by default.
2. In another terminal, run, ```python manager.py```
3. In another terminal, run, ```python worker.py```

To modify the number of worker.
Change n in manager.py and worker.py.
use -f (n+1) (+1 is the manager federate) federates with helics_broker.
