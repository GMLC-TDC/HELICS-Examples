# -*- coding: utf-8 -*-
"""
Created on 8/31/2020

This is a simple battery value federate that models the physics of an EV
battery as it is being charged. The federate receives a voltage signal
representing the voltage applied to the charging terminals of the battery
and based on its internally modeled SOC, calculates the current draw of
the battery and sends it back to the EV federate. Note that this SOC should
be considered the true SOC of the battery which may be different than the
SOC modeled by the charger.

@author: Trevor Hardy
trevor.hardy@pnnl.gov
"""

import argparse
import matplotlib.pyplot as plt
import helics as h
import logging
import numpy as np


logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.DEBUG)


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


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Demo HELICS Federate")
    parser.add_argument(
        "--config",
        help="Name of JSON config file",
        type=str,
        default="Battery1Config.json",
    )
    parser.add_argument("-r", "--random_seed", nargs="?", default=2622)
    parser.add_argument("-d", "--days", nargs="?", default=1)
    parser.add_argument("-p", "--show_plots", nargs="?", default=True)
    args = parser.parse_args()

    np.random.seed(int(args.random_seed))

    ##########  Registering  federate and configuring from JSON################
    fed = h.helicsCreateValueFederateFromConfig(args.config)
    federate_name = h.helicsFederateGetName(fed)
    logger.info(f"Created federate {federate_name}")

    sub_count = h.helicsFederateGetInputCount(fed)
    logger.debug(f"\tNumber of subscriptions: {sub_count}")
    pub_count = h.helicsFederateGetPublicationCount(fed)
    logger.debug(f"\tNumber of publications: {pub_count}")

    # Diagnostics to confirm JSON config correctly added the required
    #   publications and subscriptions
    subid = h.helicsFederateGetInputByIndex(fed, 0)
    sub_name = h.helicsInputGetTarget(subid)
    logger.debug(f"\tRegistered subscription---> {sub_name}")

    pubid = h.helicsFederateGetPublicationByIndex(fed, 0)
    pub_name = h.helicsPublicationGetName(pubid)
    logger.debug(f"\tRegistered publication---> {pub_name}")

    ##############  Entering Execution Mode  ##################################
    h.helicsFederateEnterExecutingMode(fed)
    logger.info("Entered HELICS execution mode")

    hours = 24 * float(args.days)
    total_interval = int(60 * 60 * hours)
    update_interval = int(
        h.helicsFederateGetTimeProperty(fed, h.HELICS_PROPERTY_TIME_PERIOD)
    )
    grantedtime = 0

    # Define battery physics as empirical values
    socs = np.array([0, 1])

    # 8 ohms to 150 ohms
    effective_R = np.array([8, 150])

    batt_size = get_new_battery(1)[0]

    current_soc = (np.random.randint(0, 60)) / 100

    # log initialized battery conditions
    logger.info("Initialized Battery State:")
    logger.info(f"\t{federate_name}: soc = {current_soc:.4f}, Rating = {batt_size} kWh")

    # Data collection lists
    time_sim = []
    soc_list = []

    # As long as granted time is in the time range to be simulated...
    while grantedtime < total_interval:

        # Time request for the next physical interval to be simulated
        requested_time = grantedtime + update_interval
        logger.debug(f"Requesting time {requested_time}")
        grantedtime = h.helicsFederateRequestTime(fed, requested_time)
        logger.debug(f"Granted time {grantedtime}")

        # Get the applied charging voltage from the EV
        charging_voltage = h.helicsInputGetDouble((subid))
        logger.debug(
            f"\tReceived voltage {charging_voltage:.2f} from input "
            f"{h.helicsInputGetTarget(subid)}"
        )

        # EV is fully charged and a new EV is moving in
        # This is indicated by the charging removing voltage when it
        #    thinks the EV is full
        if charging_voltage == 0:
            new_batt = get_new_battery(1)[0]
            batt_size = new_batt
            current_soc = (np.random.randint(0, 80)) / 100
            charging_current = 0

        # Calculate charging current and update SOC
        R = np.interp(current_soc, socs, effective_R)
        logger.debug(f"\tEffective R (ohms): {R:.2f}")
        charging_current = charging_voltage / R
        logger.debug(f"\tCharging current (A): {charging_current:.2f}")
        added_energy = (
            charging_current * charging_voltage * update_interval / 3600
        ) / 1000
        logger.debug(f"\tAdded energy (kWh): {added_energy:.4f}")
        current_soc = current_soc + added_energy / batt_size
        logger.debug(f"\tSOC: {current_soc:.4f}")

        # Publish out charging current
        h.helicsPublicationPublishDouble(pubid, charging_current)
        logger.debug(f"\tPublished {pub_name} with value " f"{charging_current:.2f}")

        # Store SOC for later analysis/graphing
        soc_list.append(float(current_soc))

        # Data collection vectors
        time_sim.append(grantedtime)

    # Cleaning up HELICS stuff once we've finished the co-simulation.
    fed.disconnect()
    # Printing out final results graphs for comparison/diagnostic purposes.
    xaxis = np.array(time_sim) / 3600
    y = []
    y.append(np.array(soc_list))

    fig, axs = plt.subplots(1, sharex=True, sharey=True)
    fig.suptitle(f"SOC of {federate_name}")

    axs.plot(xaxis, y[0], color="tab:blue", linestyle="-")
    axs.set_yticks(np.arange(0, 1.25, 0.5))
    axs.set(ylabel="SOC")
    plt.xlabel("time (hr)")
    # Saving graph to file
    plt.savefig(f"{federate_name}_SOC.png", format="png")
    if args.show_plots:
        plt.show()
