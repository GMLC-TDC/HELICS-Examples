# -*- coding: utf-8 -*-
"""
Created on 9/28/2020

This is a simple battery message federate that models an EV
battery as it is being charged. The federate receives a voltage signal
representing the voltage applied to the charging terminals of the battery
and based on its internally modeled SOC, calculates the current draw of
the battery and sends it back to the EV federate. Note that this SOC should
be considered the true SOC of the battery which may be different than the
SOC modeled by the charger. Each battery ceases charging when its SOC reaches 100%.

@author: Allison M. Campbell
allison.m.campbell@pnnl.gov
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
    parser.add_argument("-r", "--random_seed", nargs="?", default=2622)
    parser.add_argument("-d", "--days", nargs="?", default=1)
    parser.add_argument("-p", "--show_plots", nargs="?", default=True)
    args = parser.parse_args()

    np.random.seed(args.random_seed)

    ##########  Registering  federate and configuring from JSON################
    fed = h.helicsCreateMessageFederateFromConfig("BatteryConfig.json")
    federate_name = h.helicsFederateGetName(fed)
    logger.info(f"Created federate {federate_name}")

    end_count = h.helicsFederateGetEndpointCount(fed)
    logger.debug(f"\tNumber of endpoints: {end_count}")

    # Diagnostics to confirm JSON config correctly added the required
    #   endpoints
    endid = {}
    for i in range(end_count):
        endid[i] = h.helicsFederateGetEndpointByIndex(fed, i)
        end_name = h.helicsEndpointGetName(endid[i])
        logger.debug(f"\tRegistered Endpoint ---> {end_name}")

    ##############  Entering Execution Mode  ##################################
    h.helicsFederateEnterExecutingMode(fed)
    logger.info("Entered HELICS execution mode")

    hours = 24 * float(args.days)
    total_interval = int(60 * 60 * hours)
    update_interval = int(
        h.helicsFederateGetTimeProperty(fed, h.HELICS_PROPERTY_TIME_PERIOD)
    )
    update_offset = int(
        h.helicsFederateGetTimeProperty(fed, h.HELICS_PROPERTY_TIME_PERIOD)
    )
    grantedtime = 0

    # Define battery physics as empirical values
    socs = np.array([0, 1])

    # 8 ohms to 150 ohms
    effective_R = np.array([8, 150])

    batt_list = get_new_battery(end_count)

    current_soc = {}
    for i in range(end_count):
        current_soc[i] = (np.random.randint(0, 60)) / 100

    # Data collection lists
    time_sim = []
    total_current = []
    soc = {}

    # As long as granted time is in the time range to be simulated...
    while grantedtime < total_interval:

        # Time request for the next interval to be simulated
        requested_time = grantedtime + update_interval + update_offset
        logger.debug(f"Requesting time {requested_time}")
        grantedtime = h.helicsFederateRequestTime(fed, requested_time)
        logger.debug(f"Granted time {grantedtime}")

        charging_current = 0
        # Iterating over endpoints in this case since this example
        #  uses only one charging voltage for all five batteries
        for j in range(end_count):
            logger.debug(f"Battery {j+1} time {grantedtime}")

            # Get the applied charging voltage from the EV
            # Check for messages from Charger
            endpoint_name = h.helicsEndpointGetName(endid[j])
            if h.helicsEndpointHasMessage(endid[j]):
                msg = h.helicsEndpointGetMessage(endid[j])
                charging_voltage = float(h.helicsMessageGetString(msg))
                source = h.helicsMessageGetOriginalSource(msg)
                logger.debug(
                    f"Received message voltage {charging_voltage:.2f}"
                    f" at endpoint {endpoint_name}"
                    f" from {source}"
                    f" at time {grantedtime}"
                )

                # Calculate charging current and update SOC
                R = np.interp(current_soc[j], socs, effective_R)
                logger.debug(f"\tEffective R (ohms): {R:.2f}")
                # If battery is full assume its stops charging on its own
                #  and the charging current goes to zero.
                if current_soc[j] >= 1:
                    charging_current = 0
                else:
                    charging_current = charging_voltage / R
                logger.debug(f"\tCharging current (A): {charging_current:.2f}")

                added_energy = (
                    charging_current * charging_voltage * update_interval / 3600
                ) / 1000
                logger.debug(f"\tAdded energy (kWh): {added_energy:.4f}")
                current_soc[j] = current_soc[j] + added_energy / batt_list[j]
                logger.debug(f"\tSOC: {current_soc[j]:.4f}")
            else:
                logger.debug(
                    f"\tNo messages at endpoint {endpoint_name} "
                    f"received at "
                    f"time {grantedtime}"
                )

            # send charging current message
            # to this endpoint's default destination, ""
            h.helicsEndpointSendBytes(endid[j], str(charging_current))  #
            logger.debug(
                f"Sent message {charging_current:.2f}"
                f" from endpoint {endpoint_name}"
                f" at time {grantedtime}"
            )

            # Store SOC for later analysis/graphing
            if endid[j] not in soc:
                soc[endid[j]] = []
            soc[endid[j]].append(float(current_soc[j]))

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
    plt.savefig("fundamental_endpoints_battery_SOCs.png", format="png")
    if args.show_plots:
        plt.show()
