# -*- coding: utf-8 -*-
import time
import helics as h

fedinitstring = "--federates=1"  # " --broker_address=tcp://72.6.20.34"
deltat = 0.01

helicsversion = h.helicsGetVersion()

print("SENDER: Helics version = {}".format(helicsversion))

# Create Federate Info object that describes the federate properties #
fedinfo = h.helicsCreateFederateInfo()

# Set Federate name #
h.helicsFederateInfoSetCoreName(fedinfo, "TestA Federate")

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
vfed = h.helicsCreateValueFederate("TestA Federate", fedinfo)
print("SENDER: Value federate created")

# Register the publication #
pub = h.helicsFederateRegisterGlobalTypePublication(vfed, "testA", "double", "")
print("SENDER: Publication registered")

# Enter execution mode #
h.helicsFederateEnterExecutingMode(vfed)
print("SENDER: Entering execution mode")

# This federate will be publishing t for numsteps steps #
this_time = 0.0
value = 0

for t in range(5, 10):
    val = value

    currenttime = h.helicsFederateRequestTime(vfed, t)

    t *= 10
    h.helicsPublicationPublishDouble(pub, t)
    print("SENDER: Sending value={} at time={} to RECEIVER".format(t, currenttime))

    time.sleep(1)

h.helicsFederateFinalize(vfed)
print("SENDER: Federate finalized")

h.helicsFederateFree(vfed)
