# -*- coding: utf-8 -*-
"""
Created on 9/29/2020

This is a simple EV charging federate that models the parallel charging
of a number of EVs via a single charging point at constant voltage. Unlike
other similar examples in this suite of examples, the batteries self-
terminate their charging when they reach full SOC. This charger has no
intelligence and simply applies a constant charging voltage.

@author: Trevor Hardy
trevor.hardy@pnnl.gov
"""

import matplotlib.pyplot as plt
from multiprocessing.sharedctypes import Value
from tkinter import E
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
    grantedtime = h.helicsFederateRequestTime(fed, h.HELICS_TIME_MAXTIME)
    status = h.helicsFederateDisconnect(fed)
    h.helicsFederateDestroy(fed)
    logger.info("Federate finalized")


def get_charger_ratings(EV_list):
    """
    This function uses the pre-defined charging powers and maps them to
    standard (more or less) charging voltages. This allows the charger
    to apply an appropriately modeled voltage to the EV based on the
    charging power level

    :param EV_list: Value of "1", "2", or "3" to indicate charging level
    :return: charging_voltage: List of charging voltages corresponding
            to the charging power.
    """
    out = []
    # Ignoring the difference between AC and DC voltages for this application
    charge_voltages = [120, 240, 630]
    charge_currents = [15, 30, 104]
    for i, EV in enumerate(EV_list):
        if EV not in [1,2,3]:
            out.append({"Vr": 0 , "Ir": 0})
        else:
            out.append({"Vr": charge_voltages[EV - 1], "Ir": charge_currents[EV - 1]})
        logger.debug("EV {} ratings: Vr = {} Ir = {}".format(i+1, out[-1]["Vr"], out[-1]["Ir"]))
    return out


def get_new_EV(numEVs):
    """
    Using hard-coded probabilities, a distribution of EVs with support
    for specific charging levels are generated. The number of EVs
    generated is defined by the user.

    :param numEVs: Number of EVs
    :return
        numLvL1: Number of new EVs that will charge at level 1
        numLvL2: Number of new EVs that will charge at level 2
        numLvL3: Number of new EVs that will charge at level 3
        listOfEVs: List of all EVs (and their charging levels) generated

    """

    # Probabilities of a new EV charging at the specified level.
    lvl1 = 0.05
    lvl2 = 0.6
    lvl3 = 0.35
    listOfEVs = np.random.choice([1, 2, 3], numEVs, p=[lvl1, lvl2, lvl3]).tolist()
    numLvl1 = listOfEVs.count(1)
    numLvl2 = listOfEVs.count(2)
    numLvl3 = listOfEVs.count(3)

    return numLvl1, numLvl2, numLvl3, listOfEVs

def voltage_update(charger_rating, charging_current, charging_voltage=None, epsilon=1e-2, quiet=False):
    if charging_voltage is None:
        quiet or logger.debug("\t\t--voltage_update type: init")
        return {"V": charger_rating["Vr"], "Vmin": 0, "Vmax": charger_rating["Vr"]}
    if abs(charging_current - charger_rating["Ir"]) < epsilon:
        quiet or logger.debug("\t\t--voltage_update type: contant current")
        # Constant current charging: do nothing
        pass
    elif (charging_current < charger_rating["Ir"]) and (charging_voltage["V"] < charger_rating["Vr"]):
        quiet or logger.debug("\t\t--voltage_update type: voltage increase: V={:.2f} Vmax={:.2f}".format(charging_voltage["V"], charging_voltage["Vmax"]))
        # increase voltage
        charging_voltage= {"V": (charging_voltage["Vmax"] +  charging_voltage["V"])/2, 
                            "Vmin": charging_voltage["V"], 
                            "Vmax": charging_voltage["Vmax"]}
    elif (charging_current < charger_rating["Ir"]) and (abs(charging_voltage["V"] - charger_rating["Vr"]) < epsilon):
        quiet or logger.debug("\t--voltage_update type: contant voltage")
        # constant voltage charging: do nothing
        pass
    elif charging_current > charger_rating["Ir"]:
        quiet or logger.debug("\t\t--voltage_update type: voltage decrease: V={:.2f} Vmin={:.2f}".format(charging_voltage["V"], charging_voltage["Vmin"]))
        # decrease voltage
        charging_voltage = {"V": (charging_voltage["V"] + charging_voltage["Vmin"])/2,
                                "Vmin": charging_voltage["Vmin"],
                                "Vmax": charging_voltage["V"]}
    else:
        raise ValueError("voltage_update: inputs do not match any of the expected cases")
        
    return charging_voltage

if __name__ == "__main__":
    np.random.seed(1490)

    ##############  Registering  federate from json  ##########################
    fed = h.helicsCreateValueFederateFromConfig("ChargerConfig.json")
    federate_name = h.helicsFederateGetName(fed)
    logger.info(f"Created federate {federate_name}")
    logger.debug(f"Using Helics Version: {h.helicsGetVersion()}")

    sub_count = h.helicsFederateGetInputCount(fed)
    logger.debug(f"\tNumber of subscriptions: {sub_count}")
    pub_count = h.helicsFederateGetPublicationCount(fed)
    logger.debug(f"\tNumber of publications: {pub_count}")

    # Diagnostics to confirm JSON config correctly added the required
    #   publications, and subscriptions.
    subid = {}
    for i in range(0, sub_count):
        subid[i] = h.helicsFederateGetInputByIndex(fed, i)
        sub_name = h.helicsSubscriptionGetTarget(subid[i])
        logger.debug(f"\tRegistered subscription---> {sub_name}")

    pubid = {}
    for i in range(0, pub_count):
        pubid[i] = h.helicsFederateGetPublicationByIndex(fed, i)
        pub_name = h.helicsPublicationGetName(pubid[i])
        logger.debug(f"\tRegistered publication---> {pub_name}")

    ############## Some Setup #################################################
    # Generate an initial fleet of EVs, one for each previously defined
    #   handle. This gives each EV a unique link to the EV controller
    #   federate.
    numLvl1, numLvl2, numLvl3, EVlist = get_new_EV(pub_count)
    charger_ratings = get_charger_ratings(EVlist)

    epsilon = 1e-2
    iterative_mode = True

    hours = 24 * 5
    total_interval = int(60 * 60 * hours)
    update_interval = int(h.helicsFederateGetTimeProperty(fed, h.HELICS_PROPERTY_TIME_PERIOD))
    grantedtime = 0

    #initialize state
    iinit = 0
    charging_voltage = [voltage_update(charger_ratings[j], iinit, quiet=True) for j in range(0, pub_count)]
    charging_current = {}

    # Data collection lists
    time_sim = []
    power = []
    voltage_out = {j: [] for j in range(0, pub_count)}
    vinit = {j: [] for j in range(0, pub_count)}
    ##############  INITIALIZATION  ##################################
    # initialize published voltaged
    feditr.set_pub(fed, pubid, [x["V"] for x in charging_voltage], "EV", init=True)
    
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
        
        # Get Subscriptions (the charging currents)
        feditr.get_sub(fed, subid, itr, charging_current, iinit, "EV", "current")

        error = feditr.check_error(charging_current)
        logger.debug(f"\tError = {error}")
        if (error < epsilon) and (itr > 0):
            # no further iteration necessary
            continue
        else:
            pass
        
        # Calculate new voltages based on received currents
        logger.debug("\tCalculation Update:")
        for j in range(0, pub_count):
            # ----- update calculation --------
            # Calculate charging voltage
            charging_voltage[j] = voltage_update(charger_ratings[j], charging_current[j][0], charging_voltage[j])
            logger.debug(f"\t\tEV {j+1} charging voltage (V): " "{:.2f}".format(charging_voltage[j]["V"]))
            try:
                vinit[j][itr] = charging_voltage[j]["V"]
            except IndexError:
                vinit[j].append(charging_voltage[j]["V"])
        # Publish updated voltage values (Publishing forces re-iteration!)
        feditr.set_pub(fed, pubid, [x["V"] for x in charging_voltage])
        itr += 1
    
    state_plot(vinit, "advanced_iteration_voltage_init.png", 
            xlabel="Iteration", ykey="EV", title="EV Charging Voltage [V]")

    logger.info("=== Entering HELICS Main Loop")
    h.helicsFederateEnterExecutingMode(fed)
    ########## Main co-simulation loop ########################################
    # As long as granted time is in the time range to be simulated...
    while grantedtime < total_interval:
        # Publication needed so we can actually iterate
        feditr.set_pub(fed, pubid, [x["V"] for x in charging_voltage])

        # Time request for the next physical interval to be simulated
        requested_time = grantedtime + update_interval
        
        # reset Vmin and Vmax
        for j in range(0, pub_count):
            charging_voltage[j]["Vmin"] = 0
            charging_voltage[j]["Vmax"] = charger_ratings[j]["Vr"]

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
            
            # Get Subscriptions (the charging currents)
            feditr.get_sub(fed, subid, itr, charging_current, iinit, "EV", "current")
            
            if iterative_mode:
                # Check convergence
                error = feditr.check_error(charging_current)
                logger.debug(f"\tError = {error}")
                if (error < epsilon) and (itr > 0):
                    # no further iteration necessary
                    continue
                else:
                    pass
            
            logger.debug("\tCalculation Update:")
            for j in range(0, pub_count):
                # Calculate charging voltage
                charging_voltage[j] = voltage_update(charger_ratings[j], charging_current[j][0], charging_voltage[j])
                logger.debug(f"\t\tEV {j+1} charging voltage (V): " "{:.2f}".format(charging_voltage[j]["V"]))

            if iterative_mode:
                # Publish updated voltage values (Publishing forces re-iteration!)
                feditr.set_pub(fed, pubid, [x["V"] for x in charging_voltage])
                
                itr += 1
            else:
                break

        # Calculate the total power required by all chargers. This is the
        #   primary metric of interest, to understand the power profile
        #   and capacity requirements required for this charging garage.
        total_power = 0
        for j in range(0, pub_count):
            voltage_out[j].append(charging_voltage[j]["V"])
            total_power += charging_current[j][0]*charging_voltage[j]["V"]/1000
        logger.debug(f"\tTotal Power Draw {total_power:0.2f} kW")

        # Data collection vectors
        time_sim.append(grantedtime)
        power.append(total_power)

    # Cleaning up HELICS stuff once we've finished the co-simulation.
    destroy_federate(fed)

    # Output graph showing the charging profile for each of the charging
    #   terminals
    xaxis = np.array(time_sim) / 3600
    yaxis = np.array(power)

    plt.plot(xaxis, yaxis, color="tab:blue", linestyle="-")
    plt.yticks(np.arange(0, 100, 10))
    plt.ylabel("kW")
    plt.grid(True)
    plt.xlabel("time (hr)")
    plt.title("Instantaneous Power Draw from 5 EVs")
    plt.savefig("advanced_iteration_charger_power.png", format="png")
    plt.close()

    fig, axs = plt.subplots(5, sharex=True, sharey=False)
    fig.suptitle("Charging Voltage of each EV [V]")
    for j in range(0,pub_count):
        axs[j].plot(xaxis, voltage_out[j], color="tab:blue", linestyle="-")
        axs[j].set(ylabel=f"EV {j+1}")
        axs[j].grid(True)
    
    plt.xlabel("time (hr)")
    plt.savefig("advanced_iteration_charger_voltage.png", format="png")
    plt.show()
