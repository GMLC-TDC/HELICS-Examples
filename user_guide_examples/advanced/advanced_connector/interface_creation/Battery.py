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
import json
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


def check_existing_interfaces(fed):
    input_count = h.helicsFederateGetInputCount(fed)
    logger.debug(f"\tNumber of subscriptions: {input_count}")
    pub_count = h.helicsFederateGetPublicationCount(fed)
    logger.debug(f"\tNumber of publications: {pub_count}")

    # Diagnostics to confirm JSON config correctly added the required
    #   publications and subscriptions
    inputid = {}
    if input_count == 0:
        logger.debug(f"\tNo subscriptions defined in config file.")
    for i in range(0, input_count):
        h_input = h.helicsFederateGetInputByIndex(fed, i)
        input_name = h.helicsInputGetName(h_input)
        str1, str2 = input_name.split("/") #  "Charger/EV3_input_current"
        idx = int(str2[2]) - 1
        inputid[idx] = h_input
        logger.debug(f"\tRegistered input {idx + 1} ---> {input_name}")

    pubid = {}
    if pub_count == 0:
        logger.debug(f"\tNo publications defined in config file.")
    for i in range(0, pub_count):
        h_pub = h.helicsFederateGetPublicationByIndex(fed, i)
        pub_name = h.helicsPublicationGetName(h_pub)
        str1, str2 = pub_name.split("/") #  "Charger/EV3_input_current"
        idx = int(str2[2]) -1
        pubid[idx] = h_pub
        logger.debug(f"\tRegistered publication {idx + 1} ---> {pub_name}")
        
    return input_count, inputid, pub_count, pubid
        

# Function that will be run in response to a pre-defined custom query
# used when the HELICS connector federate commands other federates to
# create interfaces and connect them to form the federation.
@h.ffi.callback("void query(const char *query, int querySize, HelicsQueryBuffer buffer, void *user_data)")
def query_callback(query_ptr, size:int, query_buffer_ptr, user_data):
    query_buffer = h.HelicsQueryBuffer(query_buffer_ptr)
    logger.debug("Query callback called")
    query_str = h.ffi.string(query_ptr,size).decode()
    logger.debug(f"Query is string {query_str}")
    num_EVS = h.ffi.from_handle(user_data).num_EVs
    logger.debug(f"Number of EVs is {num_EVs}")
    if query_str == "potential_interfaces":
        logger.debug("Query is 'potential_interfaces'")
        pubs = []
        inputs = []
        for EVnum in range(1, num_EVs + 1):
#             pubs.append({
#                 "global": True,
#                 "key": f"Battery/EV{EVnum}_output_current",
#             })
#             inputs.append({
#                 "global": True,
#                 "key": f"Battery/EV{EVnum}_input_voltage",
#             })
            pubs.append(f"Battery/EV{EVnum}_output_current")
            inputs.append(f"Battery/EV{EVnum}_input_voltage")
        response_dict = {
            "publications": pubs,
            "inputs": inputs,
            "endpoints": []
        }
        query_response = json.dumps(response_dict)
        logger.debug(f"Query response is JSON: {query_response} ")
        h.helicsQueryBufferFill(query_buffer, query_response)
    else:
        logger.debug(f"Query was not for 'potential_interfaces', was {query_str}")

# We'll use this to pass data into the query callback federate
class UserData(object):
    def __init__(self, num_EVs):
        self.num_EVs = num_EVs
        userdata = h.ffi.new_handle(self)
        self._userdata = userdata


def register_interfaces_from_command(fed, cmd):
    logger.debug(f"received command: {cmd}")
    if "command" not in cmd.keys():
        raise ValueError("Expecting 'command' object in command JSON")
    elif "publications" not in cmd.keys():
        raise ValueError("Expecting 'publications' object in command JSON")
    elif "inputs" not in cmd.keys():
        raise ValueError("Expecting 'inputs' object in command JSON")
    elif cmd["command"] != "register_interfaces":
        raise ValueError("Expecting 'register_interfaces' as value of 'command'")
    else:
        if isinstance(cmd["publications"], list):
            for pub in cmd["publications"]:
                # This example assumes all interfaces are floats and global
                h.helicsFederateRegisterGlobalPublication(fed, pub, 
                    h.HELICS_DATA_TYPE_DOUBLE)
        else:
            raise ValueError("Expecting publications to be stored in a list")
        if isinstance(cmd["inputs"], list):
            for inp in cmd["inputs"]:
                h.helicsFederateRegisterGlobalInput(fed, inp, 
                    h.HELICS_DATA_TYPE_DOUBLE)
        else:
            raise ValueError("Expecting inputs to be stored in a list")


if __name__ == "__main__":
    np.random.seed(628)
    num_EVs = 5

    ##########  Registering federate and configuring from JSON     ################
    fed = h.helicsCreateValueFederateFromConfig("BatteryConfig.json")
    federate_name = h.helicsFederateGetName(fed)
    logger.info(f"Created federate {federate_name}")
    
    # Get the callback registered as soon as possible in the federate lifecycle
    # so that we can respond appropriately.
    user_data = UserData(num_EVs)
    user_data_handle = h.ffi.new_handle(user_data)
    h.helicsFederateSetQueryCallback(fed, query_callback, user_data_handle)
    
    check_existing_interfaces(fed)


    ##########  Entering initialization for interface creation    ################
    logger.debug("Entering iterative initializing mode iterative")
    
    h.helicsFederateEnterInitializingModeIterative(fed)
    # Query is guaranteed to be available after this call but may be 
    # available earlier. Callback responds whenever the query comes in.
    h.helicsFederateEnterInitializingModeIterative(fed)
    command = h.helicsFederateGetCommand(fed)
    if len(command) == 0:
        raise TypeError("Empty command.")
    try: 
        logger.debug(f"command string: {command}")
        cmd = json.loads(command)
    except:
        raise TypeError("Not able to convert command string to JSON.")
    
    register_interfaces_from_command(fed, cmd)       
    sub_count, subid, pub_count, pubid = check_existing_interfaces(fed)

    ##############  Entering Execution Mode  ##################################
    h.helicsFederateEnterExecutingMode(fed)
    logger.info("Entered HELICS execution mode")

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
            logger.debug(f"Battery {j + 1} time {grantedtime}")

            # Get the applied charging voltage from the EV
            charging_voltage = h.helicsInputGetDouble((subid[j]))
            logger.debug(f"\tReceived voltage {charging_voltage:.2f}" 
                        f" from input {h.helicsInputGetTarget(subid[j])}")

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
