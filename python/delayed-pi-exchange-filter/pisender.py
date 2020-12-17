# -*- coding: utf-8 -*-
import time
import helics as h
from math import pi
import pprint

initstring = "-f 3 --name=mainbroker"
fedinitstring = "--broker=mainbroker --federates=1"
deltat = 0.01
# Setting up pretty printing, mostly for debugging.
pp = pprint.PrettyPrinter(indent=2)



def eval_data_flow_graph(fed):
    query = h.helicsCreateQuery("broker", "data_flow_graph")
    graph = h.helicsQueryExecute(query, fed)
    print(f'PI SENDER: Data flow graph:\n {pp.pformat(graph)}')
    return graph



def eval_dependency_graph(fed):
    query = h.helicsCreateQuery("broker", "dependencies")
    graph = h.helicsQueryExecute(query, fed)
    print(f'PI SENDER: Dependency graph: \n {pp.pformat(graph)}')




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
fedinfo = h.helicsCreateFederateInfo()

# Set Federate name #
h.helicsFederateInfoSetCoreName(fedinfo, "pisender")

# Set core type from string #
h.helicsFederateInfoSetCoreTypeFromString(fedinfo, "zmq")

# Federate init string #
h.helicsFederateInfoSetCoreInitString(fedinfo, fedinitstring)

# Set the message interval (timedelta) for federate. Note th#
# HELICS minimum message time interval is 1 ns and by default
# it uses a time delta of 1 second. What is provided to the
# setTimedelta routine is a multiplier for the default timedelta.

# Set one second message interval #
h.helicsFederateInfoSetTimeProperty(fedinfo, h.helics_property_time_delta, deltat)

# Create value federate #
vfed = h.helicsCreateCombinationFederate("pisender", fedinfo)
print("PI SENDER: Combo federate created")

epid = h.helicsFederateRegisterGlobalEndpoint(vfed, "pisender_ep", "")
print("PI SENDER: Endpoint registered")

# Evaluating data-flow and dependency graphs 
# Manually pausing to ensure all other federates have configured as well
time.sleep(5)
eval_data_flow_graph(vfed)
eval_dependency_graph(vfed)

# Enter execution mode #
h.helicsFederateEnterExecutingMode(vfed)
print("PI SENDER: Entering execution mode")

# This federate will be publishing deltat*pi for numsteps steps #
this_time = 0.0
value = pi

for t in range(5, 10):
    val = value

    currenttime = h.helicsFederateRequestTime(vfed, t)

    #h.helicsPublicationPublishDouble(pub, val)
    print(
        "PI SENDER: Sending value pi = {} at time {} to PI RECEIVER".format(
            val, currenttime
        )
    )

    h.helicsEndpointSendEventRaw(epid, "pireceiver_ep", str(val), t)
    time.sleep(1)

h.helicsFederateFinalize(vfed)
print("PI SENDER: Federate finalized")

while h.helicsBrokerIsConnected(broker):
    time.sleep(1)

h.helicsFederateFree(vfed)
h.helicsCloseLibrary()

print("PI SENDER: Broker disconnected")
