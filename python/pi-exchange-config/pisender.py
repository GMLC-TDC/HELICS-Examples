# -*- coding: utf-8 -*-
import helics as h
import time
import struct
import math

initstring = "-f 2 --name=mainbroker"
broker = h.helicsCreateBroker("zmq", "", initstring)

fed = h.helicsCreateCombinationFederateFromConfig("sender.json")
pub = h.helicsFederateGetPublication(fed, "data")

h.helicsFederateEnterExecutingMode(fed)

for request_time in range(1, 10):
    h.helicsFederateRequestTime(fed, request_time)
    h.helicsPublicationPublishDouble(pub, math.pi)

h.helicsFederateFinalize(fed)
h.helicsFederateFree(fed)
h.helicsCloseLibrary()
