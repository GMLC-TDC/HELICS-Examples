# HELICS User Guide Fundamental Topics - Cloning Filter Example

To demonstrate the HELICS\_TIME\_MAXTIME bug there are two runner files where
Controller and Logger use different time request strategies:

- clone\_runner\_next\_time.json - Uses `fed.request_next_step()` to advance
time even if a message is not received.
- clone\_runner\_max\_time.json - Requests `HELICS_TIME_MAXTIME` and counts on
HELICS to wake up the federate to do something.

The later demonstrates the bug while the former works as intended.


This example demonstrates the use of native HELICS filters to replicate simple communication system effects. A full description of the example can be found in the [HELICS User Guide](https://docs.helics.org/en/latest/user-guide/examples/fundamental_examples/fundamental_native_filter.html).