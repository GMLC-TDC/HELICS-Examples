# -*- coding: utf-8 -*-
import helics as h

fedinitstring = "--federates=1"
deltat = 0.01

helicsversion = h.helicsGetVersion()

print("PI RECEIVER: Helics version = {}".format(helicsversion))

# Create Federate Info object that describes the federate properties */
print("PI RECEIVER: Creating Federate Info")
fedinfo = h.helicsCreateFederateInfo()

# Set Federate name
print("PI RECEIVER: Setting Federate Info Name")
h.helicsFederateInfoSetCoreName(fedinfo, "TestB Federate")

# Set core type from string
print("PI RECEIVER: Setting Federate Info Core Type")
h.helicsFederateInfoSetCoreTypeFromString(fedinfo, "zmq")

# Federate init string
print("PI RECEIVER: Setting Federate Info Init String")
h.helicsFederateInfoSetCoreInitString(fedinfo, fedinitstring)

# Set the message interval (timedelta) for federate. Note that
# HELICS minimum message time interval is 1 ns and by default
# it uses a time delta of 1 second. What is provided to the
# setTimedelta routine is a multiplier for the default timedelta.

# Set one second message interval
print("PI RECEIVER: Setting Federate Info Time Delta")
h.helicsFederateInfoSetTimeProperty(fedinfo, h.helics_property_time_delta, deltat)

# Create value federate
print("PI RECEIVER: Creating Combination Federate")
cfed = h.helicsCreateCombinationFederate("TestB Federate", fedinfo)
print("PI RECEIVER: Combination federate created")

# Subscribe to PI SENDER's publication
sub = h.helicsFederateRegisterSubscription(cfed, "testA", "")
print("PI RECEIVER: Subscription registered")

epid = h.helicsFederateRegisterGlobalEndpoint(cfed, "endpoint2", "")

h.helicsFederateEnterExecutingMode(cfed)
print("PI RECEIVER: Entering execution mode")

value = 0.0
prevtime = 0

currenttime = -1

while currenttime <= 100:

    currenttime = h.helicsFederateRequestTime(cfed, 100)

    value = h.helicsInputGetString(sub)
    print(
        "PI RECEIVER: Received value = {} at time {} from PI SENDER".format(
            value, currenttime
        )
    )
    while h.helicsEndpointHasMessage(epid):
        value = h.helicsEndpointGetMessage(epid)
        print(
            "PI RECEIVER: Received message '{}' at time {} from PI SENDER".format(
                value.data, value.time
            )
        )


h.helicsFederateDisconnect(cfed)

h.helicsFederateFree(cfed)
h.helicsCloseLibrary()
print("PI RECEIVER: Federate finalized")
