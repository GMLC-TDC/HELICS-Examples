"""
Created on 8/27/2020

This is a simple EV charge controller federate that manages the charging at
a set of charging terminals in a hypothetical EV garage. It receives periodic
SOC messages from each EV (associated with a particular charging terminal)
and sends back a message indicating whether the EV should continue charging
or not (based on whether it is full).

@author: Allison M. Campbell
allison.m.campbell@pnnl.gov
"""

import matplotlib.pyplot as plt
import helics as h
import logging
import numpy as np
import sys
import time
import pandas as pd

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.DEBUG)


def destroy_federate(fed):
    '''
    As part of ending a HELICS co-simulation it is good housekeeping to
    formally destroy a federate. Doing so informs the rest of the
    federation that it is no longer a part of the co-simulation and they
    should proceed without it (if applicable). Generally this is done
    when the co-simulation is complete and all federates end execution
    at more or less the same wall-clock time.

    :param fed: Federate to be destroyed
    :return: (none)
    '''
    # Adding extra time request to clear out any pending messages to avoid
    #   annoying errors in the broker log. Any message are tacitly disregarded.
    grantedtime = h.helicsFederateRequestTime(fed, h.HELICS_TIME_MAXTIME - 1)
    status = h.helicsFederateDisconnect(fed)
    h.helicsFederateDestroy(fed)
    logger.info('Federate finalized')


if __name__ == "__main__":
    ##############  Registering  federate from json  ##########################
    fed = h.helicsCreateMessageFederateFromConfig("ControllerConfig_3.json")
    federate_name = h.helicsFederateGetName(fed)
    logger.info(f'Created federate {federate_name}')


    #### Register endpoint #####
    # Only one endpoint for the controller
    endid = h.helicsFederateGetEndpointByIndex(fed, 0)
    end_name = h.helicsEndpointGetName(endid)
    logger.info("Registered Endpoint ---> {}".format(end_name))

    ##############  Entering Execution Mode  ##################################
    h.helicsFederateEnterExecutingMode(fed)
    logger.info('Entered HELICS execution mode')

    hours = 24*7 # one week
    total_interval = int(60 * 60 * hours)
    grantedtime = 0

    # It is common in HELICS for controllers to have slightly weird timing
    #   Generally, controllers only need to produce new control values when
    #   their inputs change. Because of this, it is common to have them
    #   request a time very far in the future (helics_time_maxtime) and
    #   when a signal arrives, they will be granted a time earlier than
    #   that, recalculate the control output and request a very late time
    #   again.


 
    starttime = h.HELICS_TIME_MAXTIME
    logger.debug(f'Requesting initial time {starttime}')
    grantedtime = h.helicsFederateRequestTime (fed, starttime)
    logger.debug(f'Granted time {grantedtime}')


    time_sim = {}
    soc = {}

    while grantedtime < total_interval:

        # In HELICS, when multiple messages arrive at an endpoint they
        # queue up and are popped off one-by-one with the
        #   "helicsEndpointHasMessage" API call. When that API doesn't
        #   return a message, you've processed them all.
        while h.helicsEndpointHasMessage(endid):

            # Get the SOC from the EV/charging terminal in question
            msg = h.helicsEndpointGetMessage(endid)
            currentsoc = h.helicsMessageGetString(msg)
            source = h.helicsMessageGetOriginalSource(msg)
            logger.debug(f'\tReceived message from endpoint {source}'
                         f' at time {grantedtime}'
                         f' with SOC {currentsoc}')

            # Send back charging command based on current SOC
            #   Our very basic protocol:
            #       If the SOC is less than soc_full keep charging (send "1")
            #       Otherwise, stop charging (send "0")
            soc_full = 0.95
            if float(currentsoc) <= soc_full:
                instructions = 1
            else:
                instructions = 0
            message = str(instructions)
            h.helicsEndpointSendBytesTo(endid, message.encode(), source)
            logger.debug(f'\tSent message to endpoint {source}'
                         f' at time {grantedtime}'
                         f' with payload {instructions}')

            # Store SOC for later analysis/graphing
            if source not in soc:
                soc[source] = []
            soc[source].append(float(currentsoc))

            if source not in time_sim:
                time_sim[source] = []
            time_sim[source].append(float(grantedtime))

        # Since we've dealt with all the messages that are queued, there's
        #   nothing else for the federate to do until/unless another
        #   message comes in. Request a time very far into the future
        #   and take a break until/unless a new message arrives.
        logger.debug(f'Requesting time {h.HELICS_TIME_MAXTIME}')
        grantedtime = h.helicsFederateRequestTime (fed, h.HELICS_TIME_MAXTIME)
        logger.info(f'Granted time: {grantedtime}')

    # Close out co-simulation execution cleanly now that we're done.
    destroy_federate(fed)

    # Printing out final results graphs for comparison/diagnostic purposes.
    x = []
    for key in time_sim:
        x.append(np.array(time_sim[key])/3600)
    y = []
    for key in soc:
        y.append(np.array(soc[key]))


    fig, axs = plt.subplots(5, sharex=True, sharey=True)
    fig.suptitle('SOC at each charging port')

    axs[0].plot(x[0], y[0], color='tab:blue', linestyle='-')
    axs[0].set_yticks(np.arange(0,1.25,0.5))
    axs[0].set(ylabel='Port 1')
    axs[0].grid(True)

    axs[1].plot(x[1], y[1], color='tab:blue', linestyle='-')
    axs[1].set(ylabel='Port 2')
    axs[1].grid(True)

    axs[2].plot(x[2], y[2], color='tab:blue', linestyle='-')
    axs[2].set(ylabel='Port 3')
    axs[2].grid(True)

    axs[3].plot(x[3], y[3], color='tab:blue', linestyle='-')
    axs[3].set(ylabel='Port 4')
    axs[3].grid(True)

    axs[4].plot(x[4], y[4], color='tab:blue', linestyle='-')
    axs[4].set(ylabel='Port 5')
    axs[4].grid(True)
    plt.xlabel('time (hr)')
    #for ax in axs():
#        ax.label_outer()
    # Saving graph to file
    plt.savefig('advanced_default_estimated_SOCs.png', format='png')
    plt.show()
