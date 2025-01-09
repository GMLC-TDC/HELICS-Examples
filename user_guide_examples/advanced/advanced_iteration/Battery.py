# -*- coding: utf-8 -*-
"""
Created on 9/28/2020

This is a simple battery value federate that models the physics of an EV
battery as it is being charged. The federate receives a voltage signal
representing the voltage applied to the charging terminals of the battery
and based on its internally modeled SOC, calculates the current draw of
the battery and sends it back to the EV federate. Note that this SOC should
be considered the true SOC of the battery which may be different than the
SOC modeled by the charger. Each battery ceases charging when its SOC reaches 100%.

@author: Trevor Hardy
trevor.hardy@pnnl.gov
"""

import matplotlib.pyplot as plt
import helics as h
import logging
import numpy as np
import sys
from iterutils import *

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.DEBUG)


feditr = FedItr(logger)

def destroy_federate(fed):
    """
    As part of ending a HELICS co-simulation it is good housekeeping to
    formally destroy a federate. Doing so informs the rest of the
    federation that it is no longer a part of the co-simulation and they
    should proceed without it (if applicable). Generally this is done
    when the co-simulation is complete and all federates end execution
    at more or less the same wall-clock time.

    :param fed: Federate to be destroyed
    :return: (none)
    """
    
    # Adding extra time request to clear out any pending messages to avoid
    #   annoying errors in the broker log. Any message are tacitly disregarded.
    logger.info("Finalizing Federate")
    grantedtime = h.helicsFederateRequestTime(fed, h.HELICS_TIME_MAXTIME - 1)
    status = h.helicsFederateDisconnect(fed)
    h.helicsFederateDestroy(fed)
    logger.info("Federate finalized")


def get_new_battery(numBattery):
    """
    Using hard-coded probabilities, a distribution of batteries of
    fixed battery sizes are generated. The number of batteries is a user
    provided parameter.

    :param numBattery: Number of batteries to generate
    :return
        listOfBatts: List of generated batteries

    """

    # Probabilities of a new EV battery having small capacity (sm),
    # medium capacity (med), and large capacity (lg).
    sm = 0.2
    med = 0.2
    lg = 0.6

    # Batteries have different sizes:
    # [25,62,100]
    listOfBatts = np.random.choice([25, 62, 100], numBattery, p=[sm, med, lg]).tolist()

    return listOfBatts

def effective_R(soc):
    if soc >= 0.6:
        return 650 * soc - 383
    else:
        return 10.83 * soc + 0.5

def current_update(charging_voltage, soc):
    # Calculate charging current and update SOC
    R = effective_R(soc)
    # If battery is full assume its stops charging on its own
    #  and the charging current goes to zero.
    if soc >= 1:
        return 0
    else:
        return max(0, charging_voltage / R)

if __name__ == "__main__":
    np.random.seed(2622)

    ##########  Registering  federate and configuring from JSON################
    fed = h.helicsCreateValueFederateFromConfig("BatteryConfig.json")
    federate_name = h.helicsFederateGetName(fed)
    logger.info(f"Created federate {federate_name}")
    logger.debug(f"Using Helics Version: {h.helicsGetVersion()}")

    sub_count = h.helicsFederateGetInputCount(fed)
    logger.debug(f"\tNumber of subscriptions: {sub_count}")
    pub_count = h.helicsFederateGetPublicationCount(fed)
    logger.debug(f"\tNumber of publications: {pub_count}")

    # Diagnostics to confirm JSON config correctly added the required
    #   publications and subscriptions
    subid = {}
    for i in range(0, sub_count):
        subid[i] = h.helicsFederateGetInputByIndex(fed, i)
        sub_name = h.helicsInputGetTarget(subid[i])
        logger.debug(f"\tRegistered subscription---> {sub_name}")

    pubid = {}
    for i in range(0, pub_count):
        pubid[i] = h.helicsFederateGetPublicationByIndex(fed, i)
        pub_name = h.helicsPublicationGetName(pubid[i])
        logger.debug(f"\tRegistered publication---> {pub_name}")

    ############## Some Setup #################################################
    epsilon = 1e-4
    iterative_mode = True
    batt_list = get_new_battery(pub_count)

    # initialize battery soc
    current_soc = {}
    for i in range(0, pub_count):
        current_soc[i] = (np.random.randint(0, 60)) / 100

    # initialize state
    vinit = 0
    charging_current = [current_update(vinit, current_soc[j]) for j in range(0, pub_count)] # initial state
    charging_voltage = {}

    hours = 24 * 5
    total_interval = int(60 * 60 * hours)
    update_interval = int(h.helicsFederateGetTimeProperty(fed, h.HELICS_PROPERTY_TIME_PERIOD))
    grantedtime = 0

    # Data collection lists
    time_sim = []
    soc = {}
    current_out = {j: [] for j in range(0, pub_count)}
    iinit = {j: [] for j in range(0, pub_count)}

    ##############  INITIALIZATION  ##################################
    # initialize published currents
    feditr.set_pub(fed, pubid, charging_current, "Battery", init=True)

    logger.info("=== Entering HELICS execution mode (Initialization)")
    itr = 0
    itr_flag = h.helics_iteration_request_iterate_if_needed
    while True:  
        itr_status = h.helicsFederateEnterExecutingModeIterative(
            fed, 
            itr_flag)
        logger.debug(f"--- Iter {itr}: Iteration Status = {ires(itr_status)}, Passed Iteration Requestion = {ireq(itr_flag)}")
        if itr_status == h.helics_iteration_result_next_step:
            break
        
        # Get Subscriptions (the charging voltages)
        feditr.get_sub(fed, subid, itr, charging_voltage, vinit, "Battery", "voltage")
        
        error = feditr.check_error(charging_voltage)
        logger.debug(f"\tError = {error}")
        if (error < epsilon) and (itr > 0):
            # no further iteration necessary
            continue
        else:
            pass
        
        # calculate new currents based on received voltage
        logger.debug("\tCalculation Update:")
        for j in range(0, pub_count):
            # ----- update calculation --------
            # Calculate charging current
            charging_current[j] = current_update(charging_voltage[j][0], current_soc[j])
            logger.debug(f"\t\tBattery {j+1} charging current (A): {charging_current[j]:.2f}")
            try:
                iinit[j][itr] = charging_current[j]
            except IndexError:
                iinit[j].append(charging_current[j])

        # Publish updated current values (Publishing forces re-iteration!)
        feditr.set_pub(fed, pubid, charging_current)
        itr += 1
    
    state_plot(iinit, "advanced_iteration_current_init.png", 
            xlabel="Iteration", ykey= "Batt", title="Battery Charging Current [A]")

    logger.info("=== Entering HELICS Main Loop")
    h.helicsFederateEnterExecutingMode(fed)
    ########## Main co-simulation loop ########################################
    # As long as granted time is in the time range to be simulated...
    while grantedtime < total_interval:
        # Publication needed so we can actually iterate
        feditr.set_pub(fed, pubid, charging_current)
        
        # Time request for the next physical interval to be simulated
        requested_time = grantedtime + update_interval

        itr = 0
        itr_flag = h.helics_iteration_request_iterate_if_needed
        while True:
            grantedtime, itr_state = feditr.request_time(fed, requested_time, itr, itr_flag, iterative_mode=iterative_mode)
            if ((itr_state == h.helics_iteration_result_next_step) and iterative_mode):
                logger.debug("\tIteration complete!")
                break
            else:
                if iterative_mode:
                    logger.debug("\tIterating")
            
            # Get Subscriptions (the charging voltages)
            feditr.get_sub(fed, subid, itr, charging_voltage, vinit, "Battery", "voltage")
            
            if iterative_mode:
                # Check convergence
                error = feditr.check_error(charging_voltage)
                logger.debug(f"\tError = {error}")
                if (error < epsilon) and (itr > 0):
                    # no further iteration necessary
                    continue
                else:
                    # itr_flag = h.helics_iteration_request_force_iteration
                    pass
            
            logger.debug(f"\tCalculation update:")
            for j in range(0, pub_count):
                charging_current[j] = current_update(charging_voltage[j][0], current_soc[j])
                logger.debug(f"\t\tBattery {j+1} Charging current (A): {charging_current[j]:.2f}")
            
            if iterative_mode:
                # Publish updated current values (Publishing forces re-iteration!)
                feditr.set_pub(fed, pubid, charging_current)
                
                itr += 1
            else:
                break

        # update state following convergence
        logger.debug(f"SOC Update time {grantedtime}")
        for j in range(0, pub_count):
            # Update SOC
            added_energy = (charging_current[j] * charging_voltage[j][0] * update_interval / 3600) / 1000
            current_soc[j] = current_soc[j] + added_energy / batt_list[j]
            logger.debug(f"\tBattery {j+1} - Added energy (kWh): {added_energy:.4f} - SOC: {current_soc[j]:.4f}")
            
            # Store SOC for later analysis/graphing
            if pubid[j] not in soc:
                soc[pubid[j]] = []
            soc[pubid[j]].append(float(current_soc[j]))
            current_out[j].append(charging_current[j])
        # Data collection vectors
        time_sim.append(grantedtime)

    # Cleaning up HELICS stuff once we've finished the co-simulation.
    destroy_federate(fed)
    # Printing out final results graphs for comparison/diagnostic purposes.
    xaxis = np.array(time_sim) / 3600
    y = []
    for key in soc:
        y.append(np.array(soc[key]))


    fig, axs = plt.subplots(5, sharex=True, sharey=True)
    fig.suptitle("SOC of each EV Battery")
    for j in range(0,pub_count):
        axs[j].plot(xaxis, soc[pubid[j]], color="tab:blue", linestyle="-")
        # axs[j].set_yticks(np.arange(0, 1.25, 0.5))
        axs[j].set(ylabel=f"Batt{j+1}")
        axs[j].grid(True)
    plt.xlabel("time (hr)")
    plt.savefig("advanced_iteration_battery_SOCs.png", format="png")
    plt.close()

    fig, axs = plt.subplots(5, sharex=True, sharey=False)
    fig.suptitle("Charging Current of each Battery [A]")
    for j in range(0,pub_count):
        axs[j].plot(xaxis, current_out[j], color="tab:blue", linestyle="-")
        axs[j].set(ylabel=f"Batt {j+1}")
        axs[j].grid(True)
    
    plt.xlabel("time (hr)")

    plt.savefig("advanced_iteration_battery_current.png", format="png")
    plt.show()
