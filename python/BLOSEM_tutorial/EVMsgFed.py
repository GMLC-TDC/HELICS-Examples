# -*- coding: utf-8 -*-
"""
Created on 8/27/2020

This is a simple EV federate that models a set of EV terminals in an
EV charging garage. Each terminal can support charging at levels 1, 2,
and 3 but the EVs that come to charge have a randomly assigned charging
level.

Managing these terminals is a centralized EV Controller that receives from
the EV the current SOC and sends a command back to the terminal to continue
charging or stop charging (once the EV is full). Once an EV is full, a new
EV is moved into the charging terminal (with a randomly assigned charging
level) and begins charging.

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
    status = h.helicsFederateFinalize(fed)
    h.helicsFederateFree(fed)
    h.helicsCloseLibrary()
    print("EV: Federate finalized")


def get_new_EV(numEVs):
    '''
    Using hard-coded probabilities, a distribution of EVs with support
    for specific charging levels are generated. The number of EVs
    generated is defined by the user.

    :param numEVs: Number of EVs
    :return
        numLvL1: Number of new EVs that will charge at level 1
        numLvL2: Number of new EVs that will charge at level 2
        numLvL3: Number of new EVs that will charge at level 3
        listOfEVs: List of all EVs (and their charging levels) generated

    '''

    # Probabilities of a new EV charging at the specified level.
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

    ##############  Registering  federate from json  ##########################
    name = "EV_federate"
    fed = h.helicsCreateMessageFederateFromConfig("EVconfig.json")
    federate_name = h.helicsFederateGetName(fed)
    logging.info(f'Created federate {federate_name}')    
    end_count = h.helicsFederateGetEndpointCount(fed)
    logging.info(f'\tNumber of endpoints: {end_count}')

    # Diagnostics to confirm JSON config correctly added the required
    #   endpoints
    endid = {}
    for i in range(0, end_count):
        endid[i] = h.helicsFederateGetEndpointByIndex(fed, i)
        end_name = h.helicsEndpointGetName(endid[i])
        logger.info(f'\tRegistered Endpoint ---> {end_name}')


    ##############  Entering Execution Mode  ##################################
    h.helicsFederateEnterExecutingMode(fed)
    logger.info('Entered HELICS execution mode')

    # Definition of charging power level (in kW) for level 1, 2, 3 chargers
    charge_rate = [1.8,7.2,50]

    # All EVs are assumed to have the same size batteries (approx. the
    #   size of a Nissan Leaf
    batt_size = 62 # kWh

    hours = 24*7 # one week
    total_interval = int(60 * 60 * hours)
    update_interval = 60 # updates every minute
    grantedtime = -1

    # Generate an initial fleet of EVs, one for each previously defined
    #   endpoint. This gives each EV a unique link to the EV controller
    #   federate.
    numLvl1,numLvl2,numLvl3,EVlist = get_new_EV(end_count)

    # Set the SOCs of the initial EV fleet to arbitrary values
    currentsoc = np.linspace(0.1,0.5,num=end_count)

    # Data collection lists
    time_sim = []
    power = []

    # Blocking call for a time request at simulation time 0
    initial_time = 60
    logger.debug(f'Requesting initial time {initial_time}')
    t = h.helicsFederateRequestTime(fed, initial_time )
    logger.debug(f'Granted time {t}')

    # Once granted an initial time, send the initial SOCs to the EV
    #   Controller
    for j in range(0,end_count):
        destination_name = str(h.helicsEndpointGetDefaultDestination(endid[j]))
        h.helicsEndpointSendMessageRaw(endid[j], "", str(currentsoc[j]).encode()) #

    # As long as granted time is in the time range to be simulated...
    while t < total_interval:

        # Time request for the next physical interval to be simulated
        requested_time = (t+update_interval)
        logger.debug(f'Requesting time {requested_time}')
        grantedtime = h.helicsFederateRequestTime (fed, requested_time)
        logger.debug(f'Granted time {grantedtime}')

        t = grantedtime

        for j in range(0,end_count):

            # Model the physics of the battery charging. This happens
            #   every time step whether a message comes in or not
            addenergy = charge_rate[(EVlist[j] - 1)] * (update_interval / 3600)
            currentsoc[j] = currentsoc[j] + addenergy / batt_size
            logger.debug(f'Added energy {addenergy} to EV at terminal {j}'
                         f' bringing it to SOC {currentsoc[j]}')

            # Check for messages from EV Controller
            endpoint_name = h.helicsEndpointGetName(endid[j])
            if h.helicsEndpointHasMessage(endid[j]):
                msg = h.helicsEndpointGetMessageObject(endid[j])
                instructions = h.helicsMessageGetString(msg)
                logger.debug(f'Received message at endpoint {endpoint_name}'
                             f' at time {t}'
                             f' with command {instructions}')

                # Update charging state based on message from controller
                # The protocol used by the EV and the EV Controller is simple:
                #       EV Controller sends "1" - keep charging
                #       EV Controller sends andything else: stop charging
                # The default state is charging (1) so we only need to
                #   do something if the controller says to stop
                if int(instructions) == 0:
                    # Stop charing this EV and move another one into the
                    #   charging station
                    _,_,_,newEVtype = get_new_EV(1)
                    EVlist[j] = newEVtype[0]
                    currentsoc[j] = 0.05
                    logger.info(f'EV full; moving in new EV charging at '
                                 f'level {newEVtype[0]}')
            else:
                logger.debug(f'No messages at endpoint {endpoint_name} '
                             f'recieved at '
                             f'time {t}')

            # Send message to Controller with SOC every 15 minutes
            if t % 900 == 0:
                destination_name = str(
                    h.helicsEndpointGetDefaultDestination(endid[j]))
                h.helicsEndpointSendMessageRaw(endid[j], "",
                                               str(currentsoc[j]))  #
                logger.debug(f'Sent message from endpoint {endpoint_name}'
                             f' at time {t}'
                             f' with payload SOC {currentsoc[j]}')

        # Calculate the total power required by all chargers. This is the
        #   primary metric of interest, to understand the power profile
        #   and capacity requirements required for this charging garage.
        total_power = 0
        for j in range(0,end_count):
            total_power += charge_rate[(EVlist[j]-1)]

        # Data collection vectors
        time_sim.append(t)
        power.append(total_power)



    # Cleaning up HELICS stuff once we've finished the co-simulation.
    destroy_federate(fed)

    # Output graph showing the charging profile for each of the charging
    #   terminals
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


