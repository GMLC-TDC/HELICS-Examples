# -*- coding: utf-8 -*-
import helics as h

fedinitstring = "--federates=1"  # " --broker_address=tcp://72.6.20.34"
deltat = 0.01

helicsversion = h.helicsGetVersion()

print("RECEIVER: Helics version = {}".format(helicsversion))

# Create Federate Info object that describes the federate properties */
print("RECEIVER: Creating Federate Info")
fedinfo = h.helicsCreateFederateInfo()

# Set Federate name
print("RECEIVER: Setting Federate Info Name")
h.helicsFederateInfoSetCoreName(fedinfo, "TestB Federate")

# Set core type from string
print("RECEIVER: Setting Federate Info Core Type")
h.helicsFederateInfoSetCoreTypeFromString(fedinfo, "zmq")

# Federate init string
print("RECEIVER: Setting Federate Info Init String")
h.helicsFederateInfoSetCoreInitString(fedinfo, fedinitstring)

# Set the message interval (timedelta) for federate. Note that
# HELICS minimum message time interval is 1 ns and by default
# it uses a time delta of 1 second. What is provided to the
# setTimedelta routine is a multiplier for the default timedelta.

# Set one second message interval
print("RECEIVER: Setting Federate Info Time Delta")
h.helicsFederateInfoSetTimeProperty(fedinfo, h.helics_property_time_delta, deltat)

# Create value federate
print("RECEIVER: Creating Value Federate")
vfed = h.helicsCreateValueFederate("TestB Federate", fedinfo)
print("RECEIVER: Value federate created")

# Subscribe to SENDER's publication
sub = h.helicsFederateRegisterSubscription(vfed, "testA", "")
print("RECEIVER: Subscription registered")

h.helicsFederateEnterExecutingMode(vfed)
print("RECEIVER: Entering execution mode")

value = 0.0
prevtime = 0

currenttime = -1

while currenttime <= 100:

    currenttime = h.helicsFederateRequestTime(vfed, 100)

    value = h.helicsInputGetString(sub)
    print("RECEIVER: Received value={} at time={} from SENDER".format(value, currenttime))

h.helicsFederateFinalize(vfed)

h.helicsFederateFree(vfed)
h.helicsCloseLibrary()
print("RECEIVER: Federate finalized")
