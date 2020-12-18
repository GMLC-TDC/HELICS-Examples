# -*- coding: utf-8 -*-
import helics as h
import time
import struct


fed = h.helicsCreateCombinationFederateFromConfig("receiver.json")
#fed = h.helicsCreateValueFederateFromConfig("receiver.json")
#sub = h.helicsFederateGetSubscription(fed, "data")
sub = h.helicsFederateGetInputByIndex(fed, 0)
h.helicsInputSetDefaultString(sub, 'default')

h.helicsFederateEnterExecutingMode(fed)


for request_time in range(1, 10):
    grantedtime = -1
    time_request = request_time + 2
    while grantedtime < time_request:
        grantedtime = h.helicsFederateRequestTime(fed, time_request)
        print("Requesting: {}, Granted {}".format(time_request, grantedtime))

    time.sleep(2.5)

    #granted_time = h.helicsFederateRequestTime(fed, request_time)
    #print(grantedtime, time_request)
    #data = h.helicsInputGetDouble(sub)
    data = h.helicsInputGetString(sub)
    print("Message : {}, Time : {}".format(data, grantedtime))

h.helicsFederateFinalize(fed)
h.helicsFederateFree(fed)
h.helicsCloseLibrary()
