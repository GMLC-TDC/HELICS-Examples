# -*- coding: utf-8 -*-
"""
Created on 9/15/2020

This is a simple EV federate that models a set of EV terminals in an
EV charging garage. Each terminal can support charging at levels 1, 2,
and 3 but the EVs that come to charge have a randomly assigned charging
level.

Managing these terminals is a centralized EV Controller that receives from
the EV the current SOC and sends a command back to the terminal to continue
charging or stop charging (once the EV is full). Once an EV is full, a new
EV is moved into the charging terminal (with a randomly assigned charging
level) and begins charging.

@author: Allison M. Campbell, Trevor Hardy
allison.m.campbell@pnnl.gov, trevor.hardy@pnnl.gov
"""

import argparse
import matplotlib.pyplot as plt
import helics as h
import logging
import numpy as np


logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.DEBUG)


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


def estimate_SOC(charging_V, charging_A):
    """
    The charger has no direct knowledge of the SOC of the EV battery it
    is charging but instead must estimate it based on the effective resistance
    of the battery which is calculated from the applied charging voltage and
    measured charging current. The effective resistance model used here is
    identical to that of the actual battery; if both the charging voltage
    and current were measured perfectly the SOC estimate here would exactly
    match the true SOC modeled by the battery. For fun, though, a small
    amount of Gaussian noise is added to the current value. This noise
    creates larger errors as the charging current goes down (EV battery
    reaching full SOC).

    :param charging_V: Applied charging voltage
    :param charging_A: Charging current as passed back by the battery federate
    :return: SOC estimate
    """
    socs = np.array([0, 1])
    effective_R = np.array([8, 150])
    mu = 0
    sigma = 0.2
    noise = np.random.normal(mu, sigma)
    measured_A = charging_A + noise
    measured_R = charging_V / measured_A
    SOC_estimate = np.interp(measured_R, effective_R, socs)

    return SOC_estimate


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Demo HELICS Federate")
    parser.add_argument(
        "--config",
        help="Name of JSON config file",
        type=str,
        default="Charger1Config.json",
    )
    parser.add_argument("-r", "--random_seed", nargs="?", default=268)
    parser.add_argument("-d", "--days", nargs="?", default=1)
    parser.add_argument("-p", "--show_plots", nargs="?", default=True)
    args = parser.parse_args()

    np.random.seed(int(args.random_seed))

    ##############  Registering  federate from json  ##########################
    fed = h.helicsCreateCombinationFederateFromConfig(args.config)
    federate_name = h.helicsFederateGetName(fed)
    logger.info(f"Created federate {federate_name}")
    end_count = h.helicsFederateGetEndpointCount(fed)
    logger.info(f"\tNumber of endpoints: {end_count}")
    sub_count = h.helicsFederateGetInputCount(fed)
    logger.info(f"\tNumber of subscriptions: {sub_count}")
    pub_count = h.helicsFederateGetPublicationCount(fed)
    logger.info(f"\tNumber of publications: {pub_count}")

    # Diagnostics to confirm JSON config correctly added the required
    #   endpoints, publications, and subscriptions.
    endid = h.helicsFederateGetEndpointByIndex(fed, 0)
    end_name = h.helicsEndpointGetName(endid)
    logger.debug(f"\tRegistered Endpoint ---> {end_name}")

    charging_current = []
    subid = h.helicsFederateGetInputByIndex(fed, 0)
    sub_name = h.helicsInputGetTarget(subid)
    logger.debug(f"\tRegistered subscription---> {sub_name}")
    charging_current.append(0)

    pubid = h.helicsFederateGetPublicationByIndex(fed, 0)
    pub_name = h.helicsPublicationGetName(pubid)
    logger.debug(f"\tRegistered publication---> {pub_name}")

    ##############  Entering Execution Mode  ##################################
    h.helicsFederateEnterExecutingMode(fed)
    logger.info("Entered HELICS execution mode")

    # Definition of charging power level (in kW) for level 1, 2, 3 chargers
    charge_rate = [1.8, 7.2, 50]

    # Generate an initial fleet of EVs, one for each previously defined
    #   endpoint. This gives each EV a unique link to the EV controller
    #   federate.
    numLvl1, numLvl2, numLvl3, EVlist = get_new_EV(1)
    charging_voltage = calc_charging_voltage(EVlist)[0]
    currentsoc = {}

    hours = 24 * float(args.days)
    total_interval = int(60 * 60 * hours)
    update_interval = int(
        h.helicsFederateGetTimeProperty(fed, h.HELICS_PROPERTY_TIME_PERIOD)
    )
    grantedtime = 0

    # Data collection lists
    time_sim = []
    power = []

    # Blocking call for a time request at simulation time 0
    initial_time = 60
    logger.debug(f"Requesting initial time {initial_time}")
    grantedtime = h.helicsFederateRequestTime(fed, initial_time)
    logger.debug(f"Granted time {grantedtime}")

    # Apply initial charging voltage
    h.helicsPublicationPublishDouble(pubid, charging_voltage)
    logger.debug(
        f"\tPublishing charging voltage of {charging_voltage} "
        f" at time {grantedtime}"
    )

    ########## Main co-simulation loop ########################################
    # As long as granted time is in the time range to be simulated...
    while grantedtime < total_interval:

        # Time request for the next physical interval to be simulated
        requested_time = grantedtime + update_interval
        logger.debug(f"Requesting time {requested_time}")
        grantedtime = h.helicsFederateRequestTime(fed, requested_time)
        logger.debug(f"Granted time {grantedtime}")
        # Model the physics of the battery charging. This happens
        #   every time step whether a message comes in or not and always
        #   uses the latest value provided by the battery model.
        charging_current = h.helicsInputGetDouble((subid))
        logger.debug(
            f"\tCharging current: {charging_current:.2f} from "
            f"input {h.helicsInputGetTarget(subid)}"
        )

        # New EV is in place after removing charge from old EV,
        # as indicated by the zero current draw.
        if charging_current == 0:
            _, _, _, newEVtype = get_new_EV(1)
            EVlist[0] = newEVtype[0]
            charge_V = calc_charging_voltage(newEVtype)[0]
            charging_voltage = charge_V

            currentsoc = 0  # Initial SOC estimate
            logger.debug(f"\tNew EV, SOC estimate: {currentsoc:.4f}")
            logger.debug(f"\tNew EV, charging voltage:" f" {charging_voltage}")
        else:
            # SOC estimation
            currentsoc = estimate_SOC(charging_voltage, charging_current)
            logger.debug(f"\tEV SOC estimate: {currentsoc:.4f}")

        # Check for messages from EV Controller
        endpoint_name = h.helicsEndpointGetName(endid)
        if h.helicsEndpointHasMessage(endid):
            msg = h.helicsEndpointGetMessage(endid)
            instructions = h.helicsMessageGetString(msg)
            logger.debug(
                f"\tReceived message at endpoint {endpoint_name}"
                f" at time {grantedtime}"
                f" with command {instructions}"
            )

            # Update charging state based on message from controller
            # The protocol used by the EV and the EV Controller is simple:
            #       EV Controller sends "1" - keep charging
            #       EV Controller sends anything else: stop charging
            # The default state is charging (1) so we only need to
            #   do something if the controller says to stop
            if int(instructions) == 0:
                # Stop charging this EV
                charging_voltage = 0
                logger.info(f"\tEV full; removing charging voltage")
        else:
            logger.debug(
                f"\tNo messages at endpoint {endpoint_name} "
                f"received at "
                f"time {grantedtime}"
            )

        # Publish updated charging voltage
        h.helicsPublicationPublishDouble(pubid, charging_voltage)
        logger.debug(
            f"\tPublishing charging voltage of {charging_voltage} "
            f" at time {grantedtime}"
        )

        # Send message to Controller with SOC every 15 minutes
        if grantedtime % 900 == 0:
            destination_name = str(h.helicsEndpointGetDefaultDestination(endid))
            message = f"{currentsoc:4f}"
            h.helicsEndpointSendBytes(endid, message.encode())
            logger.debug(
                f"Sent message from endpoint {endpoint_name}"
                f" to destination {destination_name}"
                f" at time {grantedtime}"
                f" with payload SOC {message}"
            )

        # Calculate the total power required by all chargers. This is the
        #   primary metric of interest, to understand the power profile
        #   and capacity requirements required for this charging garage.
        total_power = charging_voltage * charging_current

        # Data collection vectors
        time_sim.append(grantedtime)
        power.append(total_power)

    # Cleaning up HELICS stuff once we've finished the co-simulation.
    fed.disconnect()

    # Output graph showing the charging profile for each of the charging
    #   terminals
    xaxis = np.array(time_sim) / 3600
    yaxis = np.array(power)
    plt.plot(xaxis, yaxis, color="tab:blue", linestyle="-")
    plt.yticks(np.arange(0, 20000, 1000))
    plt.ylabel("kW")
    plt.grid(True)
    plt.xlabel("time (hr)")
    plt.title(f"Instantaneous Power Draw from {federate_name}")
    # Saving graph to file
    plt.savefig(f"{federate_name}_charging_power.png", format="png")
    if args.show_plots:
        plt.show()
