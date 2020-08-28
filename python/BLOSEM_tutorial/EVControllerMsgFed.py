"""
Created on 8/27/2020

@author: Allison M. Campbell
allison.m.campbell@pnnl.gov
"""

import helics as h
import logging
import numpy as np
import sys
import time
import matplotlib.pyplot as plt
import pandas as pd

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.DEBUG)

#


def destroy_federate(fed):
    status = h.helicsFederateFinalize(fed)
    h.helicsFederateFree(fed)
    h.helicsCloseLibrary()
    print("EVController: Federate finalized")


if __name__ == "__main__":


    #################################  Registering  federate from json  ########################################
    fed = h.helicsCreateMessageFederateFromConfig("EVControllerconfig.json")
    federate_name = h.helicsFederateGetName(fed)
    print(federate_name)


    #### Register endpoint #####
    # Only one endpoint for the controller
    endid = h.helicsFederateGetEndpointByIndex(fed, 0)
    end_name = h.helicsEndpointGetName(endid)
    logger.info("Registered Endpoint ---> {}".format(end_name))



    ######################   Entering Execution Mode  ##########################################################

    h.helicsFederateEnterExecutingMode(fed)


    hours = 24*7 # one week
    total_interval = int(60 * 60 * hours)
    update_interval = 30*60 # updates every 30 minutes
    grantedtime = -1
#

    instructions = []
    # the EV sent its first message at 15min
    # start the controller at 10min
    starttime = 10*60
    grantedtime = h.helicsFederateRequestTime (fed, starttime)


    t = grantedtime
    time_sim = []
    soc = {}

    while t < total_interval:
        new_message = False
        while h.helicsEndpointHasMessage(endid):
            new_message = True
            # 1. Receive SOC
            msg = h.helicsEndpointGetMessageObject(endid)
            currentsoc = h.helicsMessageGetString(msg)
            source = h.helicsMessageGetOriginalSource(msg)
            # 2. Send instructions
            print(t/3600,currentsoc)
            if float(currentsoc) <= 0.9:
                instructions = 1
            else:
                instructions = 0
            message = str(instructions)
            h.helicsEndpointSendMessageRaw(endid, source, message)

            # Store SOC for later use
            if source not in soc:
                soc[source] = []
                print(f'Keys in dictionary: {soc.keys()}')
            soc[source].append(float(currentsoc))
        if not new_message:
            print('NO MESSAGE RECEIVED AT TIME ',t/3600)

        time_sim.append(t)

        grantedtime = h.helicsFederateRequestTime (fed, (t+update_interval))

        t = grantedtime

    #print(np.array(time_sim))
    #print(np.array(time_sim)/60.0)
    xaxis = np.array(time_sim)/3600
    y = []
    for key in soc:
        y.append(np.array(soc[key]))

    plt.figure()

    fig, axs = plt.subplots(5, sharex=True, sharey=True)
    fig.suptitle('SOC at each charging port')

    axs[0].plot(xaxis, y[0], color='tab:blue', linestyle='-')
    axs[0].set_yticks(np.arange(0,1.25,0.5))
    axs[0].set(ylabel='EV1')
    axs[0].grid(True)

    axs[1].plot(xaxis, y[1], color='tab:blue', linestyle='-')
    axs[1].set(ylabel='EV2')
    axs[1].grid(True)

    axs[2].plot(xaxis, y[2], color='tab:blue', linestyle='-')
    axs[2].set(ylabel='EV3')
    axs[2].grid(True)

    axs[3].plot(xaxis, y[3], color='tab:blue', linestyle='-')
    axs[3].set(ylabel='EV4')
    axs[3].grid(True)

    axs[4].plot(xaxis, y[4], color='tab:blue', linestyle='-')
    axs[4].set(ylabel='EV5')
    axs[4].grid(True)
    plt.xlabel('time (hr)')
    #for ax in axs():
#        ax.label_outer()
    plt.show()


    destroy_federate(fed)
