# -*- coding: utf-8 -*-
import helics as h
import time

initstring = "-f2 --ipv4 --loglevel=7"

print("Creating Broker")
broker = h.helicsCreateBroker("zmq", "", initstring)
print("Created Broker")

print("Checking if Broker is connected")
isconnected = h.helicsBrokerIsConnected(broker)
print("Checked if Broker is connected")

if isconnected == 1:
    print("Broker created and connected")

while h.helicsBrokerIsConnected(broker):
    time.sleep(1)

h.helicsCloseLibrary()

print("Broker disconnected")
