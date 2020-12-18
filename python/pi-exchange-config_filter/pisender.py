# -*- coding: utf-8 -*-
import helics as h
import time
import struct
import math

#initstring = "-f 2 --name=mainbroker"
initstring = "--federates=2 --name=mainbroker"
broker = h.helicsCreateBroker("zmq", "", initstring)
isconnected = h.helicsBrokerIsConnected(broker)
if isconnected == 1:
    print('Broker Created with {} federates'.format(2))
    pass

fed = h.helicsCreateCombinationFederateFromConfig("sender.json")
#fed = h.helicsCreateCombinationFederateFromConfig("sender_filter.json")

pub = h.helicsFederateGetPublicationByIndex(fed, 0)

h.helicsFederateEnterExecutingMode(fed)

#data = open('flexible_building_data.txt', 'r').read()
data1 = str(math.pi)

for request_time in range(1, 10):
    time_request = request_time+3
    granted_time = -1
    while granted_time < time_request:
        granted_time = h.helicsFederateRequestTime(fed, time_request)
        print("Requesting: {}, Granted {}".format(time_request, granted_time))

    data = data1 + '__' + str(granted_time)
    #h.helicsPublicationPublishDouble(pub, str(math.pi))
    h.helicsPublicationPublishString(pub, data)
    print(granted_time, time_request, data)


h.helicsFederateFinalize(fed)
h.helicsFederateFree(fed)
h.helicsCloseLibrary()
