# -*- coding: utf-8 -*-

import helics as h


@h.ffi.callback("void filter(helics_message_object, void* userData)")
def filterFunc1(mess, userData):
    m = h.HelicsMessage(mess)
    time = h.helicsMessageGetTime(m)
    if time >= 4.0 and time <= 8.0:
       h.helicsMessageSetTime(m, time + 2.5)
       

class UserData(object):
    def __init__(self, x):
        self.x = x
        
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
ffed = h.helicsCreateMessageFederate("ffed", fedinfo)
fedName=h.helicsFederateGetName(ffed)

targetEndpoint=target+"/"+endpoint
# Register the endpoint 
ept = h.helicsFederateRegisterEndpoint(ffed, source, "")

print("filterFed: registering endpoint {} for {}".format(source,fedName))

# create a delay filter
filt = h.helicsFederateRegisterFilter(ffed, h.HELICS_FILTER_TYPE_CUSTOM, "filter")
h.helicsFilterAddSourceTarget(filt, targetEndpoint)

userdata = UserData(5)

handle = h.ffi.new_handle(userdata)
h.helicsFilterSetCustomCallback(filt, filterFunc1, handle)

print("initial delay set to 0.5")
    
print("entering init mode")
h.helicsFederateEnterInitializingMode(ffed)
print("entered init mode")
h.helicsFederateEnterExecutingMode(ffed)

# This federate is filtering messages that changes over time
this_time = h.helicsFederateRequestTime(ffed, 4.0)

print("granted time {}".format(this_time))

this_time = h.helicsFederateRequestTime(ffed, 8.0)

print("granted time {}".format(this_time))

# request a big time to get past the default time period
h.helicsFederateRequestTime(ffed, 20.0)
    

h.helicsFederateFinalize(ffed)
print("messageFed: Federate finalized")

h.helicsFederateFree(ffed)
h.helicsCloseLibrary()
