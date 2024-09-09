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
import pprint

# Setting up pretty printing, mostly for debugging.
pp = pprint.PrettyPrinter(indent=4)


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

def eval_data_flow_graph(fed):
    query = h.helicsCreateQuery("broker", "data_flow_graph")
    graph = h.helicsQueryExecute(query, fed)
    #logger.debug(f'Data flow graph: {data_flow_graph}')

    # Processing data flow graph to confirm correct configuration
    handle_lut = {}
    federates_lut = {}
    for core in graph['cores']:
        # Build handle and federate look-up table
        #   The data flow graph that is produced identifies input sources
        #   by "handle" an index for all handles in a given federate. For
        #   human comprehension, I'm building a look-up table that matches
        #   handle ID and handle name. Because the handle index is federate
        #   specific I'm going to build a unique key for the look-up table
        #   Formatted <federate Id>-<handle ID>
        #
        #   I'll build a similar look-up table for federate IDs and names
        #   but the federate IDs are globally unique so it will be simpler

        # Assume only one federate per core, index "0". Since I built this
        #   federation I know this is true and in most federations it
        #   will also be true.
        pp.pprint(graph)
        federates_lut[core['federates'][0]['attributes']['id']] = core[
            'federates'][0]['attributes']['name']

        # Endpoints, inputs, and publications all are considered handles
        #   BUT only endpoints and publications contain the mapping
        #   between handle ID and handle name
        if 'endpoints' in core['federates'][0]:
            for ep in core['federates'][0]['endpoints']:
                key = f'{ep["federate"]}-{ep["handle"]}'
                handle_lut[key] = ep['key']
        if 'publications' in core['federates'][0]:
            for pub in core['federates'][0]['publications']:
                key = f'{pub["federate"]}-{pub["handle"]}'
                handle_lut[key] = pub['key']

    # logger.debug(f'handle_lut: \n{pp.pformat(handle_lut)}')

    # Now that I've got the look-up tables in place, re-traversing the
    #   graph to log out a simplified human-readable version
    for core in graph['cores']:
        if 'inputs' in core['federates'][0]:
            logger.debug(f'Federate {core["federates"][0]["attributes"]["name"]}'
                         f' (with id {core["federates"][0]["attributes"]["id"]})'
                         f' has the following subscriptions:')
            for input in core['federates'][0]['inputs']:
                # Assume only no more than one source per input, index "0"
                #   This is usually true but multi-source inputs are a thing.
                if "sources" in input:
                    source_key = f'{input["sources"][0]["federate"]}-' \
                                 f'{input["sources"][0]["handle"]}'
                    logger.debug(f'\t{handle_lut[source_key]} from federate'
                                 f' {federates_lut[input["sources"][0]["federate"]]}')
                else:
                    # Input has no defined source
                    logger.warning(f'\tSubscription found with no source '
                                   f'defined')

    return graph, federates_lut, handle_lut


if __name__ == "__main__":
    np.random.seed(628)

    ##########  Registering  federate and configuring from JSON################
    fed = h.helicsCreateValueFederateFromConfig("BatteryConfig.json")
    federate_name = h.helicsFederateGetName(fed)
    logger.info(f"Created federate {federate_name}")

    sub_count = h.helicsFederateGetInputCount(fed)
    logger.debug(f"\tNumber of subscriptions: {sub_count}")
    pub_count = h.helicsFederateGetPublicationCount(fed)
    logger.debug(f"\tNumber of publications: {pub_count}")

    # Diagnostics to confirm JSON config correctly added the required
    #   publications and subscriptions
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
    graph, federates_lut, handle_lut = eval_data_flow_graph(fed)

    # Define battery physics as empirical values
    socs = np.array([0, 1])

    # 8 ohms to 150 ohms
    effective_R = np.array([8, 150])

    batt_list = get_new_battery(pub_count)

    current_soc = {}
    for i in range(0, pub_count):
        current_soc[i] = (np.random.randint(0, 60)) / 100

    # log initialized battery conditions
    logger.info("Initialized Battery State:")
    for i in range(0, pub_count):
        logger.info(f"\tBattery {i+1}: soc = {current_soc[i]:.4f}, Rating = {batt_list[i]} kWh")

    hours = 24 * 7
    total_interval = int(60 * 60 * hours)
    update_interval = int(h.helicsFederateGetTimeProperty(fed, h.HELICS_PROPERTY_TIME_PERIOD))
    grantedtime = 0

    # Data collection lists
    time_sim = []
    total_current = []
    soc = {}

    # As long as granted time is in the time range to be simulated...
    while grantedtime < total_interval:

        # Time request for the next physical interval to be simulated
        requested_time = grantedtime + update_interval
        logger.debug(f"Requesting time {requested_time}")
        grantedtime = h.helicsFederateRequestTime(fed, requested_time)
        logger.debug(f"Granted time {grantedtime}")

        # Iterating over publications in this case since this example
        #  uses only one charging voltage for all five batteries

        for j in range(0, pub_count):
            logger.debug(f"Battery {j+1} time {grantedtime}")

            # Get the applied charging voltage from the EV
            charging_voltage = h.helicsInputGetDouble((subid[j]))
            logger.debug(f"\tReceived voltage {charging_voltage:.2f}" 
                        f" from input {h.helicsSubscriptionGetTarget(subid[j])}")

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

            added_energy = (charging_current * charging_voltage * update_interval / 3600) / 1000
            logger.debug(f"\tAdded energy (kWh): {added_energy:.4f}")
            current_soc[j] = current_soc[j] + added_energy / batt_list[j]
            logger.debug(f"\tSOC: {current_soc[j]:.4f}")

            # Publish out charging current
            h.helicsPublicationPublishDouble(pubid[j], charging_current)
            logger.debug(f"\tPublished {h.helicsPublicationGetName(pubid[j])} with value " f"{charging_current:.2f}")

            # Store SOC for later analysis/graphing
            if pubid[j] not in soc:
                soc[pubid[j]] = []
            soc[pubid[j]].append(float(current_soc[j]))

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

    axs[0].plot(xaxis, y[0], color="tab:blue", linestyle="-")
    axs[0].set_yticks(np.arange(0, 1.25, 0.5))
    axs[0].set(ylabel="Batt1")
    axs[0].grid(True)

    axs[1].plot(xaxis, y[1], color="tab:blue", linestyle="-")
    axs[1].set(ylabel="Batt2")
    axs[1].grid(True)

    axs[2].plot(xaxis, y[2], color="tab:blue", linestyle="-")
    axs[2].set(ylabel="Batt3")
    axs[2].grid(True)

    axs[3].plot(xaxis, y[3], color="tab:blue", linestyle="-")
    axs[3].set(ylabel="Batt4")
    axs[3].grid(True)

    axs[4].plot(xaxis, y[4], color="tab:blue", linestyle="-")
    axs[4].set(ylabel="Batt5")
    axs[4].grid(True)
    plt.xlabel("time (hr)")
    # for ax in axs():
    #        ax.label_outer()
    plt.savefig("fundamental_default_battery_SOCs.png", format="png")

    plt.show()
