# -*- coding: utf-8 -*-
import socket
import sys
import time
from math import pi

import helics as h

# This doesn't actually make a connection (since it's UDP the connection
# isn't actually made until bytes are written to the socket). We use it
# here to setup the connection so we can figure out what local IP
# address will be used (ie. the IP address of the interface that
# provides the default route).
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.connect(("8.8.8.8", 80))
ipaddr = s.getsockname()[0]

# Get broker address from command args.
broker = sys.argv[1]

# Since we're running this in a different container than the receiver,
# and thus will have a different IP, the local port can be set to the
# same port the receiver uses. We can also just not specify it at all,
# in which case it will request an open port number from the broker to
# use before setting up the ZMQ PULL socket.
deltat = 0.01

fedinitstring = "--federates=1 --broker_address=tcp://{} --interface=tcp://{}".format(
    broker, ipaddr
)
deltat = 0.01

print(f"fedinitstring: {fedinitstring}")

helicsversion = h.helicsGetVersion()

print("PI SENDER: Helics version = {}".format(helicsversion))

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
print("PI SENDER: Value federate created")

# Register the publication #
pub = h.helicsFederateRegisterGlobalTypePublication(vfed, "testA", "double", "")
print("PI SENDER: Publication registered")

# Enter execution mode #
h.helicsFederateEnterExecutingMode(vfed)
print("PI SENDER: Entering execution mode")

# This federate will be publishing deltat*pi for numsteps steps #
this_time = 0.0
value = pi

for t in range(5, 10):
    val = value

    currenttime = h.helicsFederateRequestTime(vfed, t)

    h.helicsPublicationPublishDouble(pub, val)
    print(
        "PI SENDER: Sending value pi = {} at time {} to PI RECEIVER".format(
            val, currenttime
        )
    )

    time.sleep(1)

h.helicsFederateFinalize(vfed)
print("PI SENDER: Federate finalized")

h.helicsFederateFree(vfed)
h.helicsCloseLibrary()

print("PI SENDER: Broker disconnected")
