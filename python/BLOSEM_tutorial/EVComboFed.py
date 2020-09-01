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
    fed = h.helicsCreateCombinationFederateFromConfig("EVconfig.json")
    federate_name = h.helicsFederateGetName(fed)
    logging.info(f'Created federate {federate_name}')
    end_count = h.helicsFederateGetEndpointCount(fed)
    logging.info(f'\tNumber of endpoints: {end_count}')
    sub_count = h.helicsFederateGetInputCount(fed)
    logging.info(f'\tNumber of subscriptions: {sub_count}')
    pub_count = h.helicsFederateGetPublicationCount(fed)
    logging.info(f'\tNumber of publications: {pub_count}')
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
        logger.info(f'\tRegistered Endpoint ---> {end_name}')
    subid = {}
    for i in range(0, sub_count):
        subid[i] = h.helicsFederateGetInputByIndex(fed, i)
        sub_name = h.helicsSubscriptionGetKey(subid[i])
        logger.info(f'\tRegistered subscription---> {sub_name}')

    pubid = {}
    for i in range(0, pub_count):
        pubid[i] = h.helicsFederateGetPublicationByIndex(fed, i)
        pub_name = h.helicsPublicationGetKey(pubid[i])
        logger.info(f'\tRegistered publication---> {pub_name}')


    ##############  Entering Execution Mode  ##################################
    h.helicsFederateEnterExecutingMode(fed)
    logger.info('Entered HELICS execution mode')

    # Definition of charging power level (in kW) for level 1, 2, 3 chargers
    charge_rate = [1.8,7.2,50]



    # All EVs are assumed to have the same size batteries (approx. the
    #   size of a Nissan Leaf
    batt_size = 62 # kWh

    # Charging current at this value indicates the EV is charging in constant
    # current mode. We're going to assume this value is invariant with
    # charging level and it is the charging voltage that changes.
    # TODO: Define this value for reals
    critical_charging_current = 1

    # SOC at which the charging mode changes from constant current to
    # constant voltage
    critical_soc = 0.75

    hours = 24*7 # one week
    total_interval = int(60 * 60 * hours)
    update_interval = 60 # updates every minute
    grantedtime = -1

    # Generate an initial fleet of EVs, one for each previously defined
    #   endpoint. This gives each EV a unique link to the EV controller
    #   federate.
    numLvl1,numLvl2,numLvl3,EVlist = get_new_EV(end_count)

    # This is the voltage that we'll charge at when we reach the critical
    # charging current and switch to constant voltage charging mode.
    constant_voltage = {}
    for j, EV in enumerate(EVlist):
        constant_voltage[j] = charge_rate[EV-1] / critical_charging_current
        logger.info(f'voltage: {constant_voltage[j]}')

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


    # Defining the intial charging current by assuming we're starting
    #   in the constant_voltage charging range. If we're still in the
    #   constant current range the battery model will come back with the
    #   current that is too high and we'll drop the charging voltage down.
    charging_voltage = {}
    new_EV = {}
    for j in range(0, end_count):
        charging_voltage[j] = constant_voltage[j]
        new_EV[j] = False

    # Once granted an initial time, send the initial SOCs to the EV
    #   Controller
    for j in range(0,end_count):
        destination_name = str(h.helicsEndpointGetDefaultDestination(endid[j]))
        h.helicsEndpointSendMessageRaw(endid[j], "", str(currentsoc[j]).encode()) #


    ########## Main co-simulation loop ########################################
    # As long as granted time is in the time range to be simulated...
    while t < total_interval:

        # Time request for the next physical interval to be simulated
        requested_time = (t+update_interval)
        logger.debug(f'Requesting time {requested_time}')
        grantedtime = h.helicsFederateRequestTime (fed, requested_time)
        logger.debug(f'Granted time {grantedtime}')

        t = grantedtime

        for j in range(0,end_count):

            logger.debug(f'EV {j}:')
            # Model the physics of the battery charging. This happens
            #   every time step whether a message comes in or not and always
            #   uses the latest value provided by the battery model.
            charging_current = h.helicsInputGetDouble((subid[j]))
            logger.debug(f'\tCharging current: {charging_current}')
            logger.debug(f'\tfrom input {h.helicsSubscriptionGetKey(subid[j])}')

            if new_EV[j]:
                charging_voltage[j] = 0
                logger.debug(f'New EV; setting charging voltage to 0')
                new_EV[j] = False
            else:
                ############### SOC estimation ###################################
                # Estimate SOC based on charging current and voltage
                if charging_current == 0:
                    # Just connected a new EV so going to charge at a
                    #   nominal level and see what happens.
                    # Making up the SOC level just so the controller doesn't
                    #   disconnect the EV prematurely.
                    charging_voltage[j] = constant_voltage[j]
                    currentsoc[j] = 0

                elif charging_current >= critical_charging_current:
                    # SOC is estimated by some function of charging voltage
                    # SOC in this range below the critical_soc. When the charging
                    #   voltage reaches the constant_voltage value we are,
                    #   by definition, assumed to be at the critical SOC value
                    voltage_diff = constant_voltage[j] - charging_voltage[j]
                    voltage_factor = 1 - (voltage_diff / constant_voltage[j])
                    # TODO: Still need to implement the function that maps
                    #  charging voltage to SOC. Need to ensure we don't exceed
                    #  the voltage rating for the level of charger.
                    #  implement json for value federate
                    #

                else:
                    # SOC estimated based on charging current
                    #   As charging continues beyong the critical SOC, the voltage
                    #   will remain constant but the charging current will decrease
                    current_diff = critical_charging_current - charging_current
                    # The charging current is highest when the SOC is lowest
                    #   (in the constant voltage charging regime) Small
                    #   differences translate into low SOCs above 0.75
                    current_factor = current_diff / critical_charging_current
                    logger.debug(f'\t Current factor: {current_factor}')
                    currentsoc[j] = critical_soc + (current_factor / (1 -
                                                                      critical_soc) )
                logger.debug(f'\t EV SOC estimate: {currentsoc[j]}')



                ######## Charging algorithm - Update charging voltage #############
                # Model a charging algorithm with constant current during low
                #   SOC periods and constant voltage during high SOC periods
                #   We won't know the SOC when we start charging so need to
                #   estimate it from the current
                if charging_current != 0:
                    # Don't need to do this if we just connected a new EV.
                    #   Once the battery is providing real charging currents
                    #   we'll estimate the new charging voltage.
                    if charging_current > critical_charging_current:
                        # Constant current charging
                        # Stupid algorithm
                        # TODO: implement a good-enough contant current charging
                        #  algorithm
                        logger.debug(f'\t Constant current charging')
                        current_difference = charging_current - critical_charging_current
                        current_factor_diff = current_difference / critical_charging_current
                        charging_voltage[j] = charging_voltage[j] * ( 1+
                                                                 current_factor_diff)
                        logger.debug(f'\t Current percentage difference:'
                                     f' {current_factor_diff}')
                        logger.debug((f'\t New charging voltage:'
                                     f' {charging_voltage[j]}'))
                    else:
                        # Constant voltage charging
                        logger.debug(f'\t Constant voltage charging')
                        logger.debug(f'\t New charging voltage: {charging_voltage[j]}')


            # Publish updated charging voltage
            h.helicsPublicationPublishDouble(pubid[j], charging_voltage[j])


            # Check for messages from EV Controller
            endpoint_name = h.helicsEndpointGetName(endid[j])
            if h.helicsEndpointHasMessage(endid[j]):
                msg = h.helicsEndpointGetMessageObject(endid[j])
                instructions = h.helicsMessageGetString(msg)
                logger.debug(f'\tReceived message at endpoint {endpoint_name}'
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
                    new_EV = True
                    #currentsoc[j] = 0.05
                    logger.info(f'\tEV full; moving in new EV charging at '
                                 f'level {newEVtype[0]}')
            else:
                logger.debug(f'\tNo messages at endpoint {endpoint_name} '
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
