# -*- coding: utf-8 -*-
"""
Created on 8/31/2020

This is a simple battery value federate that models the physics of an EV
battery as it is being charged. The federate receives a voltage signal
representing the votlage applied to the charging terminals of the battery
and based on its internally modeled SOC, calculates the current draw of
the battery and sends it back to the EV federate. Note that this SOC should
be considered the true SOC of the battery which may be different than the
SOC modeled by the charger

@author: Trevor Hardy
trevor.hardy@pnnl.gov
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

# Define battery physics as empirical values
socs = np.array([0, 1])
effective_R = np.array([8, 150])


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


def get_new_battery(numBattery):
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
    lvl1 = 0.2
    lvl2 = 0.2
    lvl3 = 0.6
    listOfBatts = np.random.choice([25,62,100],numBattery,p=[lvl1,lvl2,
                                                       lvl3]).tolist()

    return listOfBatts


if __name__ == "__main__":
    np.random.seed(2608)

    ##############  Registering  federate from json  ##########################
    name = "Battery_federate"
    fed = h.helicsCreateValueFederateFromConfig("BatteryConfig.json")
    federate_name = h.helicsFederateGetName(fed)
    logging.info(f'Created federate {federate_name}')

    sub_count = h.helicsFederateGetInputCount(fed)
    logging.info(f'\tNumber of subscriptions: {sub_count}')
    pub_count = h.helicsFederateGetPublicationCount(fed)
    logging.info(f'\tNumber of publications: {pub_count}')
    print(f'\tNumber of subscriptions: {sub_count}')
    print(f'\tNumber of publications: {pub_count}')

    # Diagnostics to confirm JSON config correctly added the required
    #   publications and subscriptions
    subid = {}
    sub_name = {}
    for i in range(0, sub_count):
        subid[i] = h.helicsFederateGetInputByIndex(fed, i)
        sub_name[i] = h.helicsSubscriptionGetKey(subid[i])
        logger.info(f'\tRegistered subscription---> {sub_name[i]}')

    pubid = {}
    pub_name = {}
    for i in range(0, pub_count):
        pubid[i] = h.helicsFederateGetPublicationByIndex(fed, i)
        pub_name[i] = h.helicsPublicationGetKey(pubid[i])
        logger.info(f'\tRegistered publication---> {pub_name[i]}')


    ##############  Entering Execution Mode  ##################################
    h.helicsFederateEnterExecutingMode(fed)
    logger.info('Entered HELICS execution mode')


    hours = 24*7 # one week
    total_interval = int(60 * 60 * hours)
    update_interval = 60 # seconds
    grantedtime = -1

    batt_list = get_new_battery(pub_count)

    current_soc = {}
    for i in range (0, pub_count):
        current_soc[i] = (np.random.randint(0,60))/100



    # Data collection lists
    time_sim = []
    current = []
    soc = {}

    t = 0

    # As long as granted time is in the time range to be simulated...
    while t < total_interval:

        # Time request for the next physical interval to be simulated
        requested_time = (t+update_interval)
        logger.debug(f'Requesting time {requested_time}')
        grantedtime = h.helicsFederateRequestTime (fed, requested_time)
        logger.debug(f'Granted time {grantedtime}')

        t = grantedtime

        for j in range(0,sub_count):
            logger.debug(f'Battery {j+1} time {t}')

            # Get the applied charging voltage from the EV
            charging_voltage = h.helicsInputGetDouble((subid[j]))
            logger.debug(f'\tReceived voltage {charging_voltage:.2f} from input'
                         f' {h.helicsSubscriptionGetKey(subid[j])}')

            # EV is fully charged and a new EV is moving in
            # This is indicated by the charging removing voltage when it
            #    thinks the EV is full
            if charging_voltage == 0:
                new_batt = get_new_battery(1)
                batt_list[j] = new_batt[0]
                current_soc[j] = (np.random.randint(0,80))/100
                charging_current = 0

            # Calculate charging current and update SOC
            R =  np.interp(current_soc[j], socs, effective_R)
            logger.debug(f'\t Effective R (ohms): {R:.2f}')
            charging_current = charging_voltage / R
            logger.debug(f'\t Charging current (A): {charging_current:.2f}')
            added_energy = (charging_current * charging_voltage * \
                           update_interval/3600) / 1000
            logger.debug(f'\t Added energy (kWh): {added_energy:.2f}')
            current_soc[j] = current_soc[j] + added_energy / batt_list[j]
            logger.debug(f'\t SOC: {current_soc[j]:.4f}')



            # Publish out charging current
            h.helicsPublicationPublishDouble(pubid[j], charging_current)
            logger.debug(f'\tPublished {pub_name[j]} with value '
                         f'{charging_current:.2f}')

            # Store SOC for later analysis/graphing
            if subid[j] not in soc:
                soc[subid[j]] = []
            soc[subid[j]].append(float(current_soc[j]))

        # Data collection vectors
        time_sim.append(t)
        current.append(charging_current)



    # Cleaning up HELICS stuff once we've finished the co-simulation.
    destroy_federate(fed)
    # Printing out final results graphs for comparison/diagnostic purposes.
    xaxis = np.array(time_sim)/3600
    y = []
    for key in soc:
        y.append(np.array(soc[key]))

    plt.figure()

    fig, axs = plt.subplots(5, sharex=True, sharey=True)
    fig.suptitle('SOC of each EV Battery')

    axs[0].plot(xaxis, y[0], color='tab:blue', linestyle='-')
    axs[0].set_yticks(np.arange(0,1.25,0.5))
    axs[0].set(ylabel='Batt1')
    axs[0].grid(True)

    axs[1].plot(xaxis, y[1], color='tab:blue', linestyle='-')
    axs[1].set(ylabel='Batt2')
    axs[1].grid(True)

    axs[2].plot(xaxis, y[2], color='tab:blue', linestyle='-')
    axs[2].set(ylabel='Batt3')
    axs[2].grid(True)

    axs[3].plot(xaxis, y[3], color='tab:blue', linestyle='-')
    axs[3].set(ylabel='Batt4')
    axs[3].grid(True)

    axs[4].plot(xaxis, y[4], color='tab:blue', linestyle='-')
    axs[4].set(ylabel='Batt5')
    axs[4].grid(True)
    plt.xlabel('time (hr)')
    #for ax in axs():
#        ax.label_outer()
    plt.show()