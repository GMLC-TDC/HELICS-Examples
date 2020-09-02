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
effective_R = np.array([10, 150])


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



if __name__ == "__main__":
    np.random.seed(1)

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

    batt_size = 62  # kWh
    batt_cell_series = 96
    batt_cell_parallel = 3

    current_soc = {}
    for i in range (0, pub_count):
        current_soc[i] = (np.random.randint(0,80))/100



    # Data collection lists
    time_sim = []
    current = []

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
            # EV is fully charged and a new EV is moving in:
            if charging_voltage == 0:
                current_soc[j] = (np.random.randint(0,80))/100

            # Calculate charging current and update SOC
            R = (batt_cell_series / batt_cell_parallel) * np.interp(
                    current_soc[j],
                    socs,
                    effective_R)
            logger.debug(f'\t Effective R (ohms): {R:.2f}')
            charging_current = charging_voltage / R
            logger.debug(f'\t Charging current (A): {charging_current:.2f}')
            added_energy = (charging_current * charging_voltage * \
                           update_interval/3600) / 1000
            logger.debug(f'\t Added energy (kWh): {added_energy:.2f}')
            current_soc[j] = current_soc[j] + added_energy / batt_size
            logger.debug(f'\t SOC: {current_soc[j]:.4f}')



            # Publish out charging current
            h.helicsPublicationPublishDouble(pubid[j], charging_current)
            logger.debug(f'\tPublished {pub_name[j]} with value '
                         f'{charging_current:.2f}')

        # Data collection vectors
        time_sim.append(t)
        current.append(charging_current)



    # Cleaning up HELICS stuff once we've finished the co-simulation.
    destroy_federate(fed)
