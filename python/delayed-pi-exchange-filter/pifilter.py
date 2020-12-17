# -*- coding: utf-8 -*-
import time
import helics as h
from math import pi

fedinitstring = "--federates=1"
deltat = 0.01

helicsversion = h.helicsGetVersion()

print("PI FILTER: Helics version = {}".format(helicsversion))


# Create Federate Info object that describes the federate properties #
fedinfo = h.helicsCreateFederateInfo()

# Set Federate name #
h.helicsFederateInfoSetCoreName(fedinfo, "TestC Federate")

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
vfed = h.helicsCreateCombinationFederate("TestC Federate", fedinfo)
print("PI FILTER: Combo federate created")

epid = h.helicsFederateRegisterGlobalEndpoint(vfed, "filter_ep", "")
print("PI FILTER: Endpoint registered")

# Enter execution mode #
h.helicsFederateEnterExecutingMode(vfed)
print("PI FILTER: Entering execution mode")

# This federate will be publishing deltat*pi for numsteps steps #
this_time = 0.0
value = pi

for t in range(5, 10):
    val = value

    currenttime = h.helicsFederateRequestTime(vfed, t)

    if h.helicsEndpointHasMessage(epid):
        print("PI FILTER: intercepted message and sending it on")
        h.helicsEndpointSendEventRaw(epid, "endpoint2", str(val), t)
        

    
    time.sleep(1)

h.helicsFederateFinalize(vfed)
print("PI FILTER: Federate finalized")

h.helicsFederateFree(vfed)
h.helicsCloseLibrary()

print("PI FILTER: Broker disconnected")
