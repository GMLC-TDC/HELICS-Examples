# HELICS User Guide Advanced Topics - Translator Example
Currently, this example does not function properly in a variety of ways.

## Translators not translating
When running the example federation (Battery, Charger, Controller) using "translator_running_next_time.json", the received translated value by the Controller is a very large negative number (-9999999999999999464902769475481793196872414789632.00). This is not the number being sent by the Charger as a message which is supposed to be translated into a value; that for EV1 is 0.065843. 

## HELICS not handling HELICS_TIME_MAXTIME properly
When using "translator_running_next_time.json", a "max_time" command line flag is used to have Controller not request HELICS_TIME_MAXTIME but rather request an incremental time. It also changes the final time request in the "destroy_federate()" function to request a very large time rather than HELICS_TIME_MAXTIME. By removing all use of HELICS_TIME_MAXTIME, this version of the example runs successfully to completion. 

When using "translator_running_max_time.json", the federation hangs on the first time request as the Controller initially requests HELICS_TIME_MAXTIME.

## Test federation
To aid in debugging the above problems, a simpler test federation has been created using "sender_fed.py" and "receiver_fed.py". Both are configured via APIs and implement a translator with two runners: one advancing time one second at a time and the other using the controller-style HELICS_TIME_MAXTIME requests. Both examples are able to run successfully. 

# What this README will look like once we get this example working
This example cover the use of the HELICS translator which can be defined to allow value interfaces to receive data from endpoints and vice versa. The example implements an EV charging co-simulation with value, message, and combination federates. A full description of the example can be found in the [HELICS User Guide](https://docs.helics.org/en/latest/user-guide/examples/advanced_examples/advanced_default.html).