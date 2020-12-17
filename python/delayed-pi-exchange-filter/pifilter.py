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
h.helicsFederateInfoSetCoreName(fedinfo, "pifilter")

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
vfed = h.helicsCreateCombinationFederate("pifilter", fedinfo)
print("PI FILTER: Combo federate created")

epid = h.helicsFederateRegisterGlobalEndpoint(vfed, "pifilter_ep", "")
print("PI FILTER: Endpoint registered")

# fid = h.helicsFederateRegisterFilter(vfed, h.helics_filter_type_delay, "filter1")
fid = h.helicsFederateRegisterFilter(vfed, h.helics_filter_type_reroute, "filter1")
h.helicsFilterAddSourceTarget(fid, "pisender_ep")

h.helicsFilterSetString(fid, "newdestination", "pifilter_ep")


# Enter execution mode #
h.helicsFederateEnterExecutingMode(vfed)
print("PI FILTER: Entering execution mode")

# This federate will be publishing deltat*pi for numsteps steps #
this_time = 0.0
value = pi

for t in range(5, 10):
    val = value

    #t_request = t
    t_request = 10000
    currenttime = h.helicsFederateRequestTime(vfed, t_request)
    print(f"PI FILTER: Granted time {currenttime}")

    if h.helicsEndpointHasMessage(epid):
        print("PI FILTER: Intercepted rerouted message")
        msg = h.helicsEndpointGetMessage(epid)
        msg_str = h.helicsMessageGetString(msg)
        source = h.helicsMessageGetOriginalSource(msg)
        dest = h.helicsMessageGetOriginalDestination(msg)
        send_time =  h.helicsMessageGetTime(msg)
        print(f'PI FILTER: Received message from endpoint "{source}""'
                     f' to endpoint "{dest}"'
                     f' at time {send_time}'
                     f' with message {msg_str}')
        h.helicsEndpointSendEventRaw(epid, dest, msg_str, t)
        print(f'PI FILTER: Sent message'
                     f' to endpoint "{dest}"'
                     f' at time {t}'
                     f' with message {msg_str}')
    time.sleep(1)

h.helicsFederateFinalize(vfed)
print("PI FILTER: Federate finalized")

h.helicsFederateFree(vfed)
h.helicsCloseLibrary()

print("PI FILTER: Broker disconnected")
