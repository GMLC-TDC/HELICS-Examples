# -*- coding: utf-8 -*-

import helics as h
from math import pi

period = 1.0

helicsversion = h.helicsGetVersion()

print("MessageFed: Helics version = {}".format(helicsversion))

#default target to self

target = "fed"
source = "endpoint"
endpoint="endpoint"

# Create Federate Info object that describes the federate properties #
fedinfo = h.helicsCreateFederateInfo()

# Set the message interval (period) for federate. Note th#
# HELICS minimum message time interval is 1 ns and by default
# it uses a period of 1 second. What is provided to the

# Set one second message interval #
h.helicsFederateInfoSetTimeProperty(fedinfo, h.helics_property_time_period, period)

# Create value federate #
mfed = h.helicsCreateMessageFederate("fed", fedinfo)
fedName=h.helicsFederateGetName(mfed)

targetEndpoint=target+"/"+endpoint
# Register the endpoint 
ept = h.helicsFederateRegisterEndpoint(mfed, source, "")

print("messageFed: registering endpoint {} for {}".format(source,fedName))

print("entering init mode")
h.helicsFederateEnterInitializingMode(mfed)
print("entered init mode")
h.helicsFederateEnterExecutingMode(mfed)

# This federate will be sending messages at the time steps #
this_time = 0.0
value = pi

for t in range(1, 10):
    message="<message sent from {} to {} at time {}>".format(fedName,target,t-1)
    h.helicsEndpointSendMessageRaw(ept,targetEndpoint,message.encode())
    print("sent {} to {} at time {}".format(message,target,this_time))

    this_time = h.helicsFederateRequestTime(mfed, t)
    print("{} granted time {}".format(fedName,this_time))
    while (h.helicsEndpointHasMessage(ept)):
        nmessage=h.helicsEndpointGetMessageObject(ept)
        print("received message from {} time({}) at time {} ::{}".format(h.helicsMessageGetSource(nmessage),h.helicsMessageGetTime(nmessage),this_time,h.helicsMessageGetString(nmessage)))
    

h.helicsFederateFinalize(mfed)
print("messageFed: Federate finalized")

h.helicsFederateFree(mfed)
h.helicsCloseLibrary()
