# -*- coding: utf-8 -*-
import helics as h
import time
import struct

fed = h.helicsCreateCombinationFederateFromConfig("receiver.json")
sub = h.helicsFederateGetSubscription(fed, "data")
h.helicsFederateEnterExecutingMode(fed)

for request_time in range(1, 10):
    granted_time = h.helicsFederateRequestTime(fed, request_time)
    data = h.helicsInputGetDouble(sub)
    print("Message : {}".format(data))

h.helicsFederateFinalize(fed)
h.helicsFederateFree(fed)
h.helicsCloseLibrary()
