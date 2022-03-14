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

import helics as h
import logging
import numpy as np
import matplotlib.pyplot as plt


logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.DEBUG)


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
    grantedtime = h.helicsFederateRequestTime(fed, h.HELICS_TIME_MAXTIME)
    status = h.helicsFederateDisconnect(fed)
    h.helicsFederateFree(fed)
    h.helicsCloseLibrary()
    logger.info("Federate finalized")


def calc_charging_voltage(EV_list):
    """
    This function uses the pre-defined charging powers and maps them to
    standard (more or less) charging voltages. This allows the charger
    to apply an appropriately modeled voltage to the EV based on the
    charging power level

    :param EV_list: Value of "1", "2", or "3" to indicate charging level
    :return: charging_voltage: List of charging voltages corresponding
            to the charging power.
    """
    charging_voltage = []
    # Ignoring the difference between AC and DC voltages for this application
    charge_voltages = [120, 240, 630]
    for EV in EV_list:
        if EV == 1:
            charging_voltage.append(charge_voltages[0])
        elif EV == 2:
            charging_voltage.append(charge_voltages[1])
        elif EV == 3:
            charging_voltage.append(charge_voltages[2])
        else:
            charging_voltage.append(0)

    return charging_voltage


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


if __name__ == "__main__":
    np.random.seed(1490)

    ##############  Registering  federate from json  ##########################
    fed = h.helicsCreateValueFederateFromConfig("ChargerConfig.json")
    federate_name = h.helicsFederateGetName(fed)
    logger.info(f"Created federate {federate_name}")

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

    ##############  Entering Execution Mode  ##################################
    h.helicsFederateEnterExecutingMode(fed)
    logger.info("Entered HELICS execution mode")

    # Definition of charging power level (in kW) for level 1, 2, 3 chargers
    charge_rate = [1.8, 7.2, 50]

    # Generate an initial fleet of EVs, one for each previously defined
    #   handle. This gives each EV a unique link to the EV controller
    #   federate.
    numLvl1, numLvl2, numLvl3, EVlist = get_new_EV(pub_count)
    charging_voltage = calc_charging_voltage(EVlist)
    currentsoc = {}

    hours = 24 * 7
    total_interval = int(60 * 60 * hours)
    update_interval = int(h.helicsFederateGetTimeProperty(fed, h.HELICS_PROPERTY_TIME_PERIOD))
    grantedtime = 0

    # Data collection lists
    time_sim = []
    power = []
    charging_current = {}

    # Blocking call for a time request at simulation time 0
    initial_time = 60
    logger.debug(f"Requesting initial time {initial_time}")
    grantedtime = h.helicsFederateRequestTime(fed, initial_time)
    logger.debug(f"Granted time {grantedtime}")

    # Apply initial charging voltage
    for j in range(0, pub_count):
        h.helicsPublicationPublishDouble(pubid[j], charging_voltage[j])
        logger.debug(f"\tPublishing charging voltage of {charging_voltage[j]}"
                    f" at time {grantedtime}")

    ########## Main co-simulation loop ########################################
    # As long as granted time is in the time range to be simulated...
    while grantedtime < total_interval:

        # Time request for the next physical interval to be simulated
        requested_time = grantedtime + update_interval
        logger.debug(f"Requesting time {requested_time}")
        grantedtime = h.helicsFederateRequestTime(fed, requested_time)
        logger.debug(f"Granted time {grantedtime}")

        for j in range(0, pub_count):
            logger.debug(f"EV {j + 1} time {grantedtime}")
            # Model the physics of the battery charging. This happens
            #   every time step whether a message comes in or not and always
            #   uses the latest value provided by the battery model.
            charging_current[j] = h.helicsInputGetDouble((subid[j]))
            logger.debug(f"\tCharging current: {charging_current[j]:.2f} from"
                        f" input {h.helicsSubscriptionGetTarget(subid[j])}")

            # Publish updated charging voltage
            h.helicsPublicationPublishDouble(pubid[j], charging_voltage[j])
            logger.debug(f"\tPublishing charging voltage of {charging_voltage[j]}"
                         f" at time {grantedtime}")

        # Calculate the total power required by all chargers. This is the
        #   primary metric of interest, to understand the power profile
        #   and capacity requirements required for this charging garage.
        total_power = 0
        for j in range(0, pub_count):
            if charging_current[j] > 0:  # EV is still charging
                total_power += (charging_voltage[j] * charging_current[j])

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
    plt.yticks(np.arange(0, 11000, 1000))
    plt.ylabel("kW")
    plt.grid(True)
    plt.xlabel("time (hr)")
    plt.title("Instantaneous Power Draw from 5 EVs")
    plt.savefig("fundamental_default_charger_power.png", format="png")

    plt.show()
