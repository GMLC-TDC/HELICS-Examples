# -*- coding: utf-8 -*-
"""
Created on 8/27/2020

@author: Allison M. Campbell
allison.m.campbell@pnnl.gov
"""

import helics as h
import random
import string
import time
from datetime import datetime, timedelta
import json
import logging
import numpy as np
import sys
import matplotlib.pyplot as plt


logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.DEBUG)

def destroy_federate(fed):
    status = h.helicsFederateFinalize(fed)

    h.helicsFederateFree(fed)
    h.helicsCloseLibrary()


def get_new_EV(numEVs):
    # numEVs is the number of EVs to return to the main program

    lvl1 = 0.1
    lvl2 = 0.6
    lvl3 = 0.3
    listOfEVs = np.random.choice([1,2,3],numEVs,p=[lvl1,lvl2,lvl3]).tolist()
    numLvl1 = listOfEVs.count(1)
    numLvl2 = listOfEVs.count(2)
    numLvl3 = listOfEVs.count(3)

    return numLvl1,numLvl2,numLvl3,listOfEVs


if __name__ == "__main__":
    np.random.seed(1)

    #################################  Registering  federate from json  ########################################
    fed = h.helicsCreateMessageFederateFromConfig("EVconfig.json")
    federate_name = h.helicsFederateGetName(fed)
    print(federate_name)
    end_count = h.helicsFederateGetEndpointCount(fed)
    print(end_count)

    #### Register endpoints #####
    endid = {}
    for i in range(0, end_count):
        endid[i] = h.helicsFederateGetEndpointByIndex(fed, i)
        end_name = h.helicsEndpointGetName(endid[i])
        logger.info("Registered Endpoint ---> {}".format(end_name))


    ######################   Entering Execution Mode  ##########################################################

    h.helicsFederateEnterExecutingMode(fed)
    charge_rate = [1.8,7.2,50]
    batt_size = 62 # leaf capacity is 62 kWh
    hours = 24*7 # one week
    total_interval = int(60 * 60 * hours)
    update_interval = 30*60 # updates every hour
    grantedtime = -1

    numLvl1,numLvl2,numLvl3,EVlist = get_new_EV(end_count)

    time_sim = []; currentsoc = np.linspace(0.1,0.5,num=end_count)


    t = h.helicsFederateRequestTime (fed, 0)
    for j in range(0,end_count):
        destination_name = str(h.helicsEndpointGetDefaultDestination(endid[j]))
        h.helicsEndpointSendMessageRaw(endid[j], "", str(currentsoc[j]).encode()) #


    grantedtime = h.helicsFederateRequestTime (fed, (t+update_interval))
    t = grantedtime
    time_sim = []
    power = []
    print('time power')
    while t < total_interval:

        for j in range(0,end_count):
            # 1. Receive instructions
            if h.helicsEndpointHasMessage(endid[j]):
                msg = h.helicsEndpointGetMessageObject(endid[j])
                instructions = h.helicsMessageGetString(msg)
            # 2. Change SOC based on instructions
                if int(instructions) == 1:
                    addenergy = charge_rate[(EVlist[j]-1)]*(update_interval/3600)
                    currentsoc[j] = currentsoc[j] + addenergy/batt_size
                else:
                    _,_,_,newEVtype = get_new_EV(1)
                    EVlist[j] = newEVtype[0]
                    currentsoc[j] = 0.05
                # 3. Send SOC
                destination_name = str(h.helicsEndpointGetDefaultDestination(endid[j]))
                h.helicsEndpointSendMessageRaw(endid[j], "", str(currentsoc[j])) #
            else:
                print('error AT TIME ',t,' with endpoint ',str(h.helicsEndpointGetDefaultDestination(endid[j])))

        total_power = 0
        for j in range(0,end_count):
            total_power += charge_rate[(EVlist[j]-1)]
        print(t/3600,total_power)

        time_sim.append(t)
        power.append(total_power)

        grantedtime = h.helicsFederateRequestTime (fed, (t+update_interval))

        t = grantedtime

    xaxis = np.array(time_sim)/3600
    yaxis = np.array(power)
    plt.figure()
    plt.plot(xaxis, yaxis, color='tab:blue', linestyle='-')
    plt.yticks(np.arange(0,120,5))
    plt.ylabel('kW')
    plt.grid(True)
    plt.xlabel('time (hr)')
    plt.title('Instantaneous Power Draw from 5 EVs')
    plt.show()

    destroy_federate(fed)
