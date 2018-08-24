# -*- coding: utf-8 -*-
import time
import helics as h
from math import pi

initstring = "2 --name=mainbroker"
fedinitstring = "--broker=mainbroker --federates=1"
timePeriod = 1

helicsversion = h.helicsGetVersion()

print("PI SENDER: Helics version = {}".format(helicsversion))

# Create broker #
print("Creating Broker")
broker = h.helicsCreateBroker("zmq", "", initstring)
print("Created Broker")

print("Checking if Broker is connected")
isconnected = h.helicsBrokerIsConnected(broker)
print("Checked if Broker is connected")

if isconnected == 1:
    print("Broker created and connected")

# Create Federate Info object that describes the federate properties #
fedinfo = h.helicsFederateInfoCreate()

# Set Federate name #
status = h.helicsFederateInfoSetFederateName(fedinfo, "TestA Federate")

# Set core type from string #
status = h.helicsFederateInfoSetCoreTypeFromString(fedinfo, "zmq")

# Federate init string #
status = h.helicsFederateInfoSetCoreInitString(fedinfo, fedinitstring)

# Set the message interval (timedelta) for federate. Note th#
# HELICS minimum message time interval is 1 ns and by default
# it uses a time delta of 1 second. What is provided to the
# setTimedelta routine is a multiplier for the default timedelta.

# Set one second message interval #
status = h.helicsFederateInfoSetPeriod(fedinfo, timePeriod)

status = h.helicsFederateInfoSetLoggingLevel(fedinfo, 1)

# Create value federate #
fed = h.helicsCreateCombinationFederate(fedinfo)
print("PI SENDER: Value federate created")

# Register the publication #
pub = h.helicsFederateRegisterGlobalPublication(fed, "testA", "double", "")
print("PI SENDER: Publication registered")

epid = h.helicsFederateRegisterGlobalEndpoint(fed, "endpoint1", "")

fid = h.helicsFederateRegisterSourceFilter(
    fed, h.helics_delay_filter, "endpoint1", "filter-name"
)

h.helicsFilterSet(fid, "delay", 2.0)

# Enter execution mode #
status = h.helicsFederateEnterExecutionMode(fed)
print("PI SENDER: Entering execution mode")

# This federate will be publishing deltat*pi for numsteps steps #
this_time = 0.0
value = pi

for t in range(5, 10):
    val = value

    currenttime = h.helicsFederateRequestTime(fed, t)

    status = h.helicsPublicationPublishDouble(pub, val)
    print(
        "PI SENDER: Sending value pi = {} at time {} to PI RECEIVER".format(
            val, currenttime[-1]
        )
    )

    status = h.helicsEndpointSendMessageRaw(epid, "endpoint2", str(t))

    time.sleep(1)

status = h.helicsFederateFinalize(fed)
print("PI SENDER: Federate finalized")

while h.helicsBrokerIsConnected(broker):
    time.sleep(1)

h.helicsFederateFree(fed)
h.helicsCloseLibrary()

print("PI SENDER: Broker disconnected")
