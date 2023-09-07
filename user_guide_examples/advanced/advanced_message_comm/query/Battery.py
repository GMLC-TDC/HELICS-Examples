# -*- coding: utf-8 -*-
"""
Created on 9/29/2020

This is a simple battery value federate that models the physics of an EV
battery as it is being charged. The federate receives a voltage signal
representing the votlage applied to the charging terminals of the battery
and based on its internally modeled SOC, calculates the current draw of
the battery and sends it back to the EV federate. Note that this SOC should
be considered the true SOC of the battery which may be different than the
SOC modeled by the charger

This example has queries added for demonstration and diagnostic purposes.

@author: Trevor Hardy
trevor.hardy@pnnl.gov
"""

import matplotlib.pyplot as plt
import helics as h
import logging
import numpy as np
import json
import pprint
import time

# Setting up pretty printing, mostly for debugging.
pp = pprint.PrettyPrinter(indent=4)


logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
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
    
        # Adding extra time request to clear out any pending messages to avoid
    #   annoying errors in the broker log. Any message are tacitly disregarded.
    grantedtime = h.helicsFederateRequestTime(fed, h.HELICS_TIME_MAXTIME)
    status = h.helicsFederateDisconnect(fed)
    h.helicsFederateDestroy(fed)
    logger.info('Federate finalized')


def get_new_battery(numBattery):
    '''
    Using hard-coded probabilities, a distribution of battery of
    fixed battery sizes are generated. The number of batteries is a user
    provided parameter.

    :param numBattery: Number of batteries to generate
    :return
        listOfBatts: List of generated batteries

    '''

    # Probabilities of a new EV having a battery at a given capacity. 
    #   The three random values (25,62, 100) are the kWh of the randomly
    #   selected battery.
    size_1 = 0.2
    size_2 = 0.2
    size_3 = 0.6
    listOfBatts = np.random.choice([25,62,100],numBattery,p=[size_1,size_2,
                                                       size_3]).tolist()

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
        federates_lut[core['federates'][0]['id']] = core['federates'][0][
            'name']

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
            logger.debug(f'Federate {core["federates"][0]["name"]}'
                         f' (with id {core["federates"][0]["id"]})'
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
    np.random.seed(2608)

    ##########  Registering  federate and configuring from JSON################
    fed = h.helicsCreateValueFederateFromConfig("BatteryConfig.json")
    federate_name = h.helicsFederateGetName(fed)
    logger.info(f'Created federate {federate_name}')
    print(f'Created federate {federate_name}')

    sub_count = h.helicsFederateGetInputCount(fed)
    logger.debug(f'\tNumber of subscriptions: {sub_count}')
    pub_count = h.helicsFederateGetPublicationCount(fed)
    logger.debug(f'\tNumber of publications: {pub_count}')

    # Diagnostics to confirm JSON config correctly added the required
    #   publications and subscriptions
    subid = {}
    sub_name = {}
    for i in range(0, sub_count):
        subid[i] = h.helicsFederateGetInputByIndex(fed, i)
        sub_name[i] = h.helicsSubscriptionGetTarget(subid[i])
        logger.debug(f'\tRegistered subscription---> {sub_name[i]}')

    pubid = {}
    pub_name = {}
    for i in range(0, pub_count):
        pubid[i] = h.helicsFederateGetPublicationByIndex(fed, i)
        pub_name[i] = h.helicsPublicationGetName(pubid[i])
        logger.debug(f'\tRegistered publication---> {pub_name[i]}')

    # Setting up for dynamic configuration
    # Pausing to ensure the other federates have registered so that we
    #   can look at the available publications and subscribe to the
    #   correct ones
    sleep_time = 5
    logger.debug(f'Sleeping for {sleep_time} seconds')
    time.sleep(sleep_time)
    logger.debug('Pre-configure data-flow graph query.')
    graph, federates_lut, handle_lut = eval_data_flow_graph(fed)

    #logger.debug(pp.pformat(graph))

    # Looking at the graph to find the publications to which we need to
    #   subscribe
    for core in graph['cores']:
        if core['federates'][0]['name'] == 'Charger':
            for pub in core['federates'][0]['publications']:
                key = pub['key']
                sub = h.helicsFederateRegisterSubscription(fed, key)
                logger.debug(f'Added subscription {key}')

    ##############  Entering Init Mode  ##################################
    h.helicsFederateEnterInitializingMode(fed)

    # This is a convenient point at which to run queries on the structure
    #  of the federation as execution of the co-simulation has not begun.

    # The data flow graph can be a time-intensive query for large
    #   federations
    # Verifying dynamic configuration worked.
    logger.debug('Post-configure data-flow graph query.')
    graph, federates_lut, handle_lut = eval_data_flow_graph(fed)
    # logger.debug(pp.pformat(graph))
    sub_count = h.helicsFederateGetInputCount(fed)
    logger.debug(f'Number of subscriptions: {sub_count}')
    subid = {}
    sub_name = {}
    for i in range(0, sub_count):
        subid[i] = h.helicsFederateGetInputByIndex(fed, i)
        sub_name[i] = h.helicsSubscriptionGetTarget(subid[i])
        logger.debug(f'\tRegistered subscription---> {sub_name[i]}')




    ##############  Entering Execution Mode  ##################################
    h.helicsFederateEnterExecutingMode(fed)
    logger.info('Entered HELICS execution mode')

    hours = 24*7 # one week
    total_interval = int(60 * 60 * hours)
    update_interval = int(h.helicsFederateGetTimeProperty(
                                fed,
                                h.HELICS_PROPERTY_TIME_PERIOD))
    grantedtime = 0

    # Define battery physics as empirical values
    socs = np.array([0, 1])
    effective_R = np.array([8, 150])

    batt_list = get_new_battery(pub_count)

    current_soc = {}
    for i in range (0, pub_count):
        current_soc[i] = (np.random.randint(0,60))/100



    # Data collection lists
    time_sim = []
    current = []
    soc = {}

    # As long as granted time is in the time range to be simulated...
    while grantedtime < total_interval:

        # Checking time status of federation at an arbitrary time
        # if grantedtime == (60 * 60 * 36):
        #     h.helicsQuerySetQueryString(query, "global_time")
        #     global_time = h.helicsQueryExecute(query, fed)
        #     logger.debug(f'Federate time status: {global_time}')

        # Time request for the next physical interval to be simulated
        requested_time = (grantedtime+update_interval)
        logger.debug(f'Requesting time {requested_time}')
        grantedtime = h.helicsFederateRequestTime (fed, requested_time)
        logger.debug(f'Granted time {grantedtime}')

        for j in range(0,sub_count):
            logger.debug(f'Battery {j+1} time {grantedtime}')

            # Get the applied charging voltage from the EV
            charging_voltage = h.helicsInputGetDouble((subid[j]))
            logger.debug(f'\tReceived voltage {charging_voltage:.2f} from input'
                         f' {h.helicsSubscriptionGetTarget(subid[j])}')

            # EV is fully charged and a new EV is moving in
            # This is indicated by the charging removing voltage when it
            #    thinks the EV is full
            if charging_voltage == 0:
                new_batt = get_new_battery(1)
                batt_list[j] = new_batt[0]
                current_soc[j] = (np.random.randint(0,80))/100
                charging_current = 0

            # Calculate charging current and update SOC
            R =  np.interp(current_soc[j], socs, effective_R)
            logger.debug(f'\tEffective R (ohms): {R:.2f}')
            charging_current = charging_voltage / R
            logger.debug(f'\tCharging current (A): {charging_current:.2f}')
            added_energy = (charging_current * charging_voltage * \
                           update_interval/3600) / 1000
            logger.debug(f'\tAdded energy (kWh): {added_energy:.4f}')
            current_soc[j] = current_soc[j] + added_energy / batt_list[j]
            logger.debug(f'\tSOC: {current_soc[j]:.4f}')



            # Publish out charging current
            h.helicsPublicationPublishDouble(pubid[j], charging_current)
            logger.debug(f'\tPublished {pub_name[j]} with value '
                         f'{charging_current:.2f}')

            # Store SOC for later analysis/graphing
            if subid[j] not in soc:
                soc[subid[j]] = []
            soc[subid[j]].append(float(current_soc[j]))

        # Data collection vectors
        time_sim.append(grantedtime)
        current.append(charging_current)



    # Cleaning up HELICS stuff once we've finished the co-simulation.
    destroy_federate(fed)
    # Printing out final results graphs for comparison/diagnostic purposes.
    xaxis = np.array(time_sim)/3600
    y = []
    for key in soc:
        y.append(np.array(soc[key]))


    fig, axs = plt.subplots(5, sharex=True, sharey=True)
    fig.suptitle('SOC of each EV Battery')

    axs[0].plot(xaxis, y[0], color='tab:blue', linestyle='-')
    axs[0].set_yticks(np.arange(0,1.25,0.5))
    axs[0].set(ylabel='Batt1')
    axs[0].grid(True)

    axs[1].plot(xaxis, y[1], color='tab:blue', linestyle='-')
    axs[1].set(ylabel='Batt2')
    axs[1].grid(True)

    axs[2].plot(xaxis, y[2], color='tab:blue', linestyle='-')
    axs[2].set(ylabel='Batt3')
    axs[2].grid(True)

    axs[3].plot(xaxis, y[3], color='tab:blue', linestyle='-')
    axs[3].set(ylabel='Batt4')
    axs[3].grid(True)

    axs[4].plot(xaxis, y[4], color='tab:blue', linestyle='-')
    axs[4].set(ylabel='Batt5')
    axs[4].grid(True)
    plt.xlabel('time (hr)')
    #for ax in axs():
#        ax.label_outer()
    # Saving graph to file
    #plt.savefig('advanced_query_battery_SOCs.png', format='png')
    plt.show()
