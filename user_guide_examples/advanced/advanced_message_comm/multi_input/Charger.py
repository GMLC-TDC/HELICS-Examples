# -*- coding: utf-8 -*-
"""
Created on 9/28/2020

This is a simple EV charging federate that models the parallel charging
of a number of EVs via a single charging point at constant voltage. Unlike
other similar examples in this suite of examples, the batteries self-
terminate their charging when they reach full SOC. This charger has no
intelligence and simply applies a constant charging voltage.

This charging federate was modified to demonstrate multi-source inputs
in HELICS. Rather than subscribing to a published charging current for
each battery, all battery charging currents are sent to a single multi-
source input. These values are aggregated using the "sum" function as
defined in ChargerConfig.json. Constructing the signals in this manner
models a single charging point/meter that is downstream connected to
five batteries in parallel. (The original model would represent five
distinct charging points each with their own meter.)

@author: Trevor Hardy
trevor.hardy@pnnl.gov
"""

import matplotlib.pyplot as plt
import helics as h
import logging
import numpy as np


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
    grantedtime = h.helicsFederateRequestTime(fed, h.HELICS_TIME_MAXTIME)
    status = h.helicsFederateDisconnect(fed)
    h.helicsFederateDestroy(fed)
    logger.info('Federate finalized')


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
    lvl1 = 0.05
    lvl2 = 0.6
    lvl3 = 0.35
    listOfEVs = np.random.choice([1,2,3],numEVs,p=[lvl1,lvl2,lvl3]).tolist()
    numLvl1 = listOfEVs.count(1)
    numLvl2 = listOfEVs.count(2)
    numLvl3 = listOfEVs.count(3)

    return numLvl1,numLvl2,numLvl3,listOfEVs




if __name__ == "__main__":
    np.random.seed(1490)

    ##############  Registering  federate from json  ##########################
    fed = h.helicsCreateCombinationFederateFromConfig("ChargerConfig.json")
    federate_name = h.helicsFederateGetName(fed)
    logger.info(f'Created federate {federate_name}')
    end_count = h.helicsFederateGetEndpointCount(fed)
    logger.info(f'\tNumber of endpoints: {end_count}')
    sub_count = h.helicsFederateGetInputCount(fed)
    logger.info(f'\tNumber of subscriptions: {sub_count}')
    pub_count = h.helicsFederateGetPublicationCount(fed)
    logger.info(f'\tNumber of publications: {pub_count}')
    print(f'Created federate {federate_name}')
    print(f'\tNumber of endpoints: {end_count}')
    print(f'\tNumber of subscriptions: {sub_count}')
    print(f'\tNumber of publications: {pub_count}')

    # Diagnostics to confirm JSON config correctly added the required
    #   endpoints, publications, and subscriptions.
    endid = {}
    for i in range(0, end_count):
        endid[i] = h.helicsFederateGetEndpointByIndex(fed, i)
        end_name = h.helicsEndpointGetName(endid[i])
        logger.debug(f'\tRegistered Endpoint ---> {end_name}')
    subid = {}
    for i in range(0, sub_count):
        subid[i] = h.helicsFederateGetInputByIndex(fed, i)
        sub_name = h.helicsSubscriptionGetKey(subid[i])
        logger.debug(f'\tRegistered subscription---> {sub_name}')

    pubid = {}
    for i in range(0, pub_count):
        pubid[i] = h.helicsFederateGetPublicationByIndex(fed, i)
        pub_name = h.helicsPublicationGetName(pubid[i])
        logger.debug(f'\tRegistered publication---> {pub_name}')


    ##############  Entering Execution Mode  ##################################
    h.helicsFederateEnterExecutingMode(fed)
    logger.info('Entered HELICS execution mode')

    # Definition of charging power level (in kW) for level 1, 2, 3 chargers
    charge_rate = [1.8,7.2,50]



    hours = 24 * 7
    total_interval = int(60 * 60 * hours)
    update_interval = int(h.helicsFederateGetTimeProperty(
                            fed,
                            h.HELICS_PROPERTY_TIME_PERIOD))
    grantedtime = 0

    # Hard-coded for this example; all EVs will be charged with the same
    #   voltage and connected in parallel.
    charging_voltage = 240
    currentsoc = {}

    # Data collection lists
    time_sim = []
    power = []

    # Blocking call for a time request at simulation time 0
    initial_time = 60
    logger.debug(f'Requesting initial time {initial_time}')
    grantedtime = h.helicsFederateRequestTime(fed, initial_time )
    logger.debug(f'Granted time {grantedtime}')


    # Apply initial charging voltage
    for j in range(0, pub_count):
        h.helicsPublicationPublishDouble(pubid[j], charging_voltage)
        logger.debug(f'\tPublishing charging voltage of {charging_voltage} '
                     f' at time {grantedtime}')


    ########## Main co-simulation loop ########################################
    # As long as granted time is in the time range to be simulated...
    while grantedtime < total_interval:

        # Time request for the next physical interval to be simulated
        requested_time = (grantedtime + update_interval)
        logger.debug(f'Requesting time {requested_time}')
        grantedtime = h.helicsFederateRequestTime (fed, requested_time)
        logger.debug(f'Granted time {grantedtime}')

        # Only one (multi-source) input defined so we just grab that
        #   single value. All the individual published values are
        #   aggregated by the method defined in the config file for this
        #   input.
        charging_current = h.helicsInputGetDouble((subid[0]))


        # Calculate the total power required by all chargers. This is the
        #   primary metric of interest, to understand the power profile
        #   and capacity requirements required for this charging garage.
        total_power = charging_voltage * charging_current

        # Data collection vectors
        time_sim.append(grantedtime)
        power.append(total_power)



    # Cleaning up HELICS stuff once we've finished the co-simulation.
    destroy_federate(fed)

    # Output graph showing the charging profile for each of the charging
    #   terminals
    xaxis = np.array(time_sim)/3600
    yaxis = np.array(power)
    plt.plot(xaxis, yaxis, color='tab:blue', linestyle='-')
    plt.yticks(np.arange(0,8000,500))
    plt.ylabel('kW')
    plt.grid(True)
    plt.xlabel('time (hr)')
    plt.title('Instantaneous Power Draw from 5 EVs')
    # Saving graph to file
    #plt.savefig('advanced_multi_input_power.png', format='png')
    plt.show()
