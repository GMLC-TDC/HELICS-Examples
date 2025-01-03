# -*- coding: utf-8 -*-
"""
Created on 8/31/2020

This is a simple battery value federate that models the physics of an EV
battery as it is being charged. The federate receives a voltage signal
representing the voltage applied to the charging terminals of the battery
and based on its internally modeled SOC, calculates the current draw of
the battery and sends it back to the EV federate. Note that this SOC should
be considered the true SOC of the battery which may be different than the
SOC modeled by the charger

This model differs from the Combo Example in that it creates federates and
registers them with the HELICS API.

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


def create_value_federate(fedinitstring, name, period):
    fedinfo = h.helicsCreateFederateInfo()
    # "coreType": "zmq",
    h.helicsFederateInfoSetCoreTypeFromString(fedinfo, "zmq")
    h.helicsFederateInfoSetCoreInitString(fedinfo, fedinitstring)
    # "loglevel": 1,
    h.helicsFederateInfoSetIntegerProperty(fedinfo, h.helics_property_int_log_level, 1)
    # "period": 60,
    h.helicsFederateInfoSetTimeProperty(fedinfo, h.helics_property_time_period, period)
    # "uninterruptible": false,
    h.helicsFederateInfoSetFlagOption(fedinfo, h.helics_flag_uninterruptible, False)
    # "terminate_on_error": true,
    h.helicsFederateInfoSetFlagOption(fedinfo, h.HELICS_FLAG_TERMINATE_ON_ERROR, True)
    # "wait_for_current_time_update": true,
    h.helicsFederateInfoSetFlagOption(
        fedinfo, h.helics_flag_wait_for_current_time_update, True
    )
    # "name": "Battery",
    fed = h.helicsCreateValueFederate(name, fedinfo)
    return fed


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
    parser.add_argument("-r", "--random_seed", nargs="?", default=628)
    parser.add_argument("-d", "--days", nargs="?", default=1)
    parser.add_argument("-p", "--show_plots", nargs="?", default=True)
    args = parser.parse_args()

    np.random.seed(args.random_seed)

    ##########  Registering  federate and configuring with API################
    fedinitstring = " --federates=1"
    name = "Battery"
    period = 60
    fed = create_value_federate(fedinitstring, name, period)
    logger.info(f"Created federate {name}")

    num_EVs = 5

    sub_count = num_EVs
    subid = {}
    for i in range(sub_count):
        sub_name = f"Charger/EV{i+1}_voltage"
        subid[i] = h.helicsFederateRegisterSubscription(fed, sub_name, "V")
        logger.debug(f"\tRegistered subscription---> {sub_name}")

    pub_count = num_EVs
    pubid = {}
    pub_name = {}
    for i in range(pub_count):
        # "key":"Battery/EV1_current",
        pub_name[i] = f"Battery/EV{i+1}_current"
        pubid[i] = h.helicsFederateRegisterGlobalTypePublication(
            fed, pub_name[i], "double", "A"
        )
        logger.debug(f"\tRegistered publication---> {pub_name[i]}")

    sub_count = h.helicsFederateGetInputCount(fed)
    logger.debug(f"\tNumber of subscriptions: {sub_count}")
    pub_count = h.helicsFederateGetPublicationCount(fed)
    logger.debug(f"\tNumber of publications: {pub_count}")

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

    batt_list = get_new_battery(pub_count)

    current_soc = {}
    for i in range(pub_count):
        current_soc[i] = (np.random.randint(0, 60)) / 100

    # log initialized battery conditions
    logger.info("Initialized Battery State:")
    for i in range(pub_count):
        logger.info(
            f"\tBattery {i+1}: soc = {current_soc[i]:.4f}, Rating = {batt_list[i]} kWh"
        )

    # Data collection lists
    time_sim = []
    soc = {}

    # As long as granted time is in the time range to be simulated...
    while grantedtime < total_interval:

        # Time request for the next physical interval to be simulated
        requested_time = grantedtime + update_interval
        logger.debug(f"Requesting time {requested_time}")
        grantedtime = h.helicsFederateRequestTime(fed, requested_time)
        logger.debug(f"Granted time {grantedtime}")

        for j in range(sub_count):
            logger.debug(f"Battery {j+1} time {grantedtime}")

            # Get the applied charging voltage from the EV
            charging_voltage = h.helicsInputGetDouble((subid[j]))
            logger.debug(
                f"\tReceived voltage {charging_voltage:.2f} from input "
                f"{h.helicsInputGetTarget(subid[j])}"
            )

            # EV is fully charged and a new EV is moving in
            # This is indicated by the charging removing voltage when it
            #    thinks the EV is full
            if charging_voltage == 0:
                new_batt = get_new_battery(1)
                batt_list[j] = new_batt[0]
                current_soc[j] = (np.random.randint(0, 80)) / 100
                charging_current = 0

            # Calculate charging current and update SOC
            R = np.interp(current_soc[j], socs, effective_R)
            logger.debug(f"\tEffective R (ohms): {R:.2f}")
            charging_current = charging_voltage / R
            logger.debug(f"\tCharging current (A): {charging_current:.2f}")
            added_energy = (
                charging_current * charging_voltage * update_interval / 3600
            ) / 1000
            logger.debug(f"\tAdded energy (kWh): {added_energy:.4f}")
            current_soc[j] = current_soc[j] + added_energy / batt_list[j]
            logger.debug(f"\tSOC: {current_soc[j]:.4f}")

            # Publish out charging current
            h.helicsPublicationPublishDouble(pubid[j], charging_current)
            logger.debug(
                f"\tPublished {pub_name[j]} with value " f"{charging_current:.2f}"
            )

            # Store SOC for later analysis/graphing
            if subid[j] not in soc:
                soc[subid[j]] = []
            soc[subid[j]].append(float(current_soc[j]))

        # Data collection vectors
        time_sim.append(grantedtime)

    # Cleaning up HELICS stuff once we've finished the co-simulation.
    fed.disconnect()
    # Printing out final results graphs for comparison/diagnostic purposes.
    xaxis = np.array(time_sim) / 3600
    y = []
    for key in soc:
        y.append(np.array(soc[key]))

    fig, axs = plt.subplots(5, sharex=True, sharey=True)
    fig.suptitle("SOC of each EV Battery")

    axs[0].plot(xaxis, y[0], color="tab:blue", linestyle="-")
    axs[0].set_yticks(np.arange(0, 1.25, 0.5))
    axs[0].set(ylabel="Batt at\nport 1")
    axs[0].grid(True)

    axs[1].plot(xaxis, y[1], color="tab:blue", linestyle="-")
    axs[1].set(ylabel="Batt at\nport 2")
    axs[1].grid(True)

    axs[2].plot(xaxis, y[2], color="tab:blue", linestyle="-")
    axs[2].set(ylabel="Batt at\nport 3")
    axs[2].grid(True)

    axs[3].plot(xaxis, y[3], color="tab:blue", linestyle="-")
    axs[3].set(ylabel="Batt at\nport 4")
    axs[3].grid(True)

    axs[4].plot(xaxis, y[4], color="tab:blue", linestyle="-")
    axs[4].set(ylabel="Batt at\nport 5")
    axs[4].grid(True)
    plt.xlabel("time (hr)")
    # Saving graph to file
    plt.savefig("fundamental_final_battery_SOCs.png", format="png")

    if args.show_plots:
        plt.show()
