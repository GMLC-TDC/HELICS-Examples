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

import matplotlib.pyplot as plt
import helics as h
import logging
import numpy as np


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
    fed_name = h.helicsFederateGetName(fed)
    status = h.helicsFederateDisconnect(fed)
    h.helicsFederateDestroy(fed)
    logger.info(f'Federate {fed_name} finalized')


def create_battery_federate(core_name, fed_name, num_EVs):
    # Creating federate on common core
    fedinfo = h.helicsCreateFederateInfo()
    h.helicsFederateInfoSetCoreName(fedinfo, core_name)
    h.helicsFederateInfoSetIntegerProperty(fedinfo, h.helics_property_int_log_level, 11)
    h.helicsFederateInfoSetTimeProperty(fedinfo, h.helics_property_time_period, 60)
    h.helicsFederateInfoSetFlagOption(fedinfo, h.helics_flag_uninterruptible, False)
    h.helicsFederateInfoSetFlagOption(fedinfo, h.HELICS_FLAG_TERMINATE_ON_ERROR, True)
    h.helicsFederateInfoSetFlagOption(fedinfo, h.helics_flag_wait_for_current_time_update, True)
    battery_fed = h.helicsCreateValueFederate(fed_name, fedinfo)
    logger.info(f'Created federate {fed_name}')
    
    # Setting up message passing for federate
    pub_count = num_EVs
    pubid = {}
    pub_name = {}
    for i in range(0,pub_count):
        # "key":"Battery/EV1_current",
        pub_name[i] = f'Battery/EV{i+1}_current'
        pubid[i] = h.helicsFederateRegisterGlobalTypePublication(
                    battery_fed, pub_name[i], 'double', 'A')
        logger.debug(f'\tRegistered publication---> {pub_name[i]}')

    sub_count = num_EVs
    subid = {}
    for i in range(0,sub_count):
        sub_name = f'Charger/EV{i+1}_voltage'
        subid[i] = h.helicsFederateRegisterSubscription(
                    battery_fed, sub_name, 'V')
        logger.debug(f'\tRegistered subscription---> {sub_name}')

    sub_count = h.helicsFederateGetInputCount(battery_fed)
    logger.debug(f'\tNumber of subscriptions: {sub_count}')
    pub_count = h.helicsFederateGetPublicationCount(battery_fed)
    logger.debug(f'\tNumber of publications: {pub_count}')
    return battery_fed, pubid, pub_name, subid

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


def create_charger_federate(core_name, fed_name, num_EVs):
    # Creating federate on common core
    fedinfo = h.helicsCreateFederateInfo()
    h.helicsFederateInfoSetCoreName(fedinfo, core_name)
    h.helicsFederateInfoSetIntegerProperty(fedinfo, h.helics_property_int_log_level, 11)
    h.helicsFederateInfoSetTimeProperty(fedinfo, h.helics_property_time_period, 60)
    h.helicsFederateInfoSetFlagOption(fedinfo, h.helics_flag_uninterruptible, False)
    h.helicsFederateInfoSetFlagOption(fedinfo, h.HELICS_FLAG_TERMINATE_ON_ERROR, True)
    h.helicsFederateInfoSetFlagOption(fedinfo, h.helics_flag_wait_for_current_time_update, False)
    charger_fed = h.helicsCreateValueFederate(fed_name, fedinfo)
    logger.info(f'Created federate {fed_name}')
    
    pub_count = num_EVs
    pubid = {}
    charging_current = []
    for i in range(0, pub_count):
        # "key":"Charger/EV1_voltage",
        pub_name = f'Charger/EV{i+1}_voltage'
        pubid[i] = h.helicsFederateRegisterGlobalTypePublication(
                    charger_fed, pub_name, 'double', 'V')
        logger.debug(f'\tRegistered publication---> {pub_name}')

    sub_count = num_EVs
    subid = {}
    for i in range(0,sub_count):
        # "key":"Battery/EV1_current"
        sub_name = f'Battery/EV{i+1}_current'
        subid[i] = h.helicsFederateRegisterSubscription(charger_fed, sub_name, 'A')
        logger.debug(f'\tRegistered subscription---> {sub_name}')
        charging_current.append(0)

    sub_count = h.helicsFederateGetInputCount(charger_fed)
    logger.info(f'\tNumber of subscriptions: {sub_count}')
    pub_count = h.helicsFederateGetPublicationCount(charger_fed)
    logger.info(f'\tNumber of publications: {pub_count}')
    
    return charger_fed, pubid, charging_current, subid
    
def get_new_EV_charging_level(numEVs):
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
    listOfEVs = charger_rng.choice([1, 2, 3], numEVs, p=[lvl1, lvl2, lvl3]).tolist()
    numLvl1 = listOfEVs.count(1)
    numLvl2 = listOfEVs.count(2)
    numLvl3 = listOfEVs.count(3)

    return numLvl1, numLvl2, numLvl3, listOfEVs

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
    sm = 0.2
    med = 0.2
    lg = 0.6

    # Batteries have different sizes:
    # [25,62,100]
    listOfBatts = battery_rng.choice([25, 62, 100], numBattery, p=[sm, med, lg]).tolist()

    return listOfBatts


if __name__ == "__main__":
    battery_rng = np.random.RandomState(628)
    charger_rng = np.random.RandomState(1490)
    
    core_name = "common_core"
    common_core = h.helicsCreateCore("zmq", core_name , "--federates=2")
    
    num_EVs = 5
    

    ##########  Creating Federates on Common Core with API   ################
    battery_fed, battery_pub_id, battery_pub_name, battery_sub_id = \
    create_battery_federate(core_name, "battery", num_EVs)
    
    charger_fed, charger_pub_id, charging_charging_current, charger_sub_id = \
    create_charger_federate(core_name, "charger", num_EVs)

    


    ##############  Entering Execution Mode  ##################################
    battery_update_interval = int(h.helicsFederateGetTimeProperty(battery_fed, h.HELICS_PROPERTY_TIME_PERIOD))
    charger_update_interval = int(h.helicsFederateGetTimeProperty(charger_fed, h.HELICS_PROPERTY_TIME_PERIOD))
    battery_grantedtime = 0
    charger_grantedtime = 0
    
    # This mess in the time requests is there to handle the 
    # `wait_for_current_time_update` flag set in the battery federate. It 
    # requires that the charger have requested a time beyond the battery before
    # the battery will be granted time. In this case, the time grant is t=0 of 
    # entering executing mode.
    h.helicsFederateEnterExecutingModeAsync(charger_fed)
    logger.info('Charger entering HELICS executing mode asynchronously')
    h.helicsFederateEnterExecutingModeAsync(battery_fed)
    logger.info('Battery entering HELICS executing mode asynchronously')
    h.helicsFederateEnterExecutingModeComplete(charger_fed)
    logger.info('Charger completed entering executing mode')
    charger_requested_time = (charger_grantedtime + charger_update_interval)
    h.helicsFederateRequestTimeAsync(charger_fed, charger_requested_time)
    logger.debug(f'Charger requesting time {charger_requested_time} asynchronously')
    h.helicsFederateEnterExecutingModeComplete(battery_fed)
    logger.info('Battery completed entering executing mode')

    hours = 24*7 # one week
    total_interval = int(60 * 60 * hours)
    # Define battery physics as empirical values
    socs = np.array([0, 1])
    effective_R = np.array([8, 150])

    batt_list = get_new_battery(num_EVs)
    numLvl1, numLvl2, numLvl3, EVlist = get_new_EV_charging_level(num_EVs)
    charger_charging_voltage = calc_charging_voltage(EVlist)

    battery_current_soc = {}
    for i in range (0, num_EVs):
        battery_current_soc[i] = (battery_rng.randint(0,60))/100

    # log initialized battery conditions
    logger.info("Initialized Battery State:")
    for i in range(0, num_EVs):
        logger.info(f"\tBattery {i+1}: soc = {battery_current_soc[i]:.4f}, Rating = {batt_list[i]} kWh")


    # Data collection lists
    battery_time_sim = []
    battery_current = []
    battery_soc = {}
    charger_time_sim = []
    charger_power = []
    charger_charging_current = {}
    charger_current_soc = {}
    
    
    # As long as granted time is in the time range to be simulated...
    while charger_grantedtime < total_interval:
        battery_requested_time = (battery_grantedtime + battery_update_interval)
        logger.debug(f'Battery requesting time {battery_requested_time} asynchronously')
        h.helicsFederateRequestTimeAsync(battery_fed, battery_requested_time)
        
        charger_grantedtime = h.helicsFederateRequestTimeComplete(charger_fed)
        logger.debug(f'Charger granted time {charger_grantedtime}')
        # Update charger federate model
        for j in range(0, num_EVs):
            # Model the physics of the battery charging. This happens
            #   every time step whether a message comes in or not and always
            #   uses the latest value provided by the battery model.
            if charger_grantedtime > 60:
                # Don't look for published currents from battery on the first
                # time grant
                charger_charging_current[j] = h.helicsInputGetDouble((charger_sub_id[j]))
                logger.debug(f"\tCharging current: {charger_charging_current[j]:.2f} from"
                            f" input {h.helicsInputGetTarget(charger_sub_id[j])}")

            # Publish updated charging voltage
            h.helicsPublicationPublishDouble(charger_pub_id[j], charger_charging_voltage[j])
            logger.debug(f"\tPublishing {h.helicsPublicationGetName(charger_pub_id[j])}"
                         f" of {charger_charging_voltage[j]}"
                         f" at time {charger_grantedtime}")
        
        if charger_grantedtime > 60:
            total_power = 0
            for j in range(0, num_EVs):
                if charger_charging_current[j] > 0:  # EV is still charging
                    total_power += (charger_charging_voltage[j] * charger_charging_current[j])
        
            charger_time_sim.append(charger_grantedtime)
            charger_power.append(total_power)
            
        charger_requested_time = (charger_grantedtime + charger_update_interval)
        h.helicsFederateRequestTimeAsync(charger_fed, charger_requested_time)
        logger.debug(f'Charger requesting time {charger_requested_time} asynchronously')
        
        # Now that the charger federate has requested granted a time further  
        # ahead than the battery federates, the `wait_for_current_time_update`
        # flag can be respected by completing the time request for the battery
        # federate
        battery_grantedtime = h.helicsFederateRequestTimeComplete(battery_fed)
        logger.debug(f'Battery granted time {battery_grantedtime}')
        for j in range(0,num_EVs):
            # Update battery federate model
            # Get the applied charging voltage from the EV
            charging_voltage = h.helicsInputGetDouble((battery_sub_id[j]))
            logger.debug(f'\tReceived voltage {charging_voltage:.2f} from input'
                         f' {h.helicsInputGetTarget(battery_sub_id[j])}')


            # Calculate charging current and update SOC
            R =  np.interp(battery_current_soc[j], socs, effective_R)
            logger.debug(f'\tEffective R (ohms): {R:.2f}')
            # If battery is full assume its stops charging on its own
            #  and the charging current goes to zero.
            if battery_current_soc[j] >= 1:
                charging_current = 0
            else:
                charging_current = charging_voltage / R
            logger.debug(f"\tCharging current (A): {charging_current:.2f}")
            added_energy = (charging_current * charging_voltage * \
                           battery_update_interval/3600) / 1000
            logger.debug(f'\tAdded energy (kWh): {added_energy:.4f}')
            battery_current_soc[j] = battery_current_soc[j] + added_energy / batt_list[j]
            logger.debug(f'\tSOC: {battery_current_soc[j]:.4f}')

            # Publish out charging current
            h.helicsPublicationPublishDouble(battery_pub_id[j], charging_current)
            logger.debug(f'\tPublished {h.helicsPublicationGetName(battery_pub_id[j])} with value '
                         f'{charging_current:.2f}')

            # Store SOC for later analysis/graphing
            if battery_sub_id[j] not in battery_soc:
                battery_soc[battery_sub_id[j]] = []
            battery_soc[battery_sub_id[j]].append(float(battery_current_soc[j]))

        # Data collection vectors
        battery_time_sim.append(battery_grantedtime)
        battery_current.append(charging_current)
        
    # Cleaning up HELICS stuff once we've finished the co-simulation.
    logger.info("Destroying federates")
    battery_requested_time = (battery_grantedtime + battery_update_interval)
    logger.debug(f'Battery requesting time {battery_requested_time} asynchronously')
    h.helicsFederateRequestTimeAsync(battery_fed, battery_requested_time)
    charger_grantedtime = h.helicsFederateRequestTimeComplete(charger_fed)
    logger.debug(f'Charger granted time {charger_grantedtime}')
    destroy_federate(charger_fed)
    battery_grantedtime = h.helicsFederateRequestTimeComplete(battery_fed)
    logger.debug(f'Battery granted time {battery_grantedtime}')
    destroy_federate(battery_fed)
        

    # Battery graph
    # Printing out final results graphs for comparison/diagnostic purposes.
    xaxis = np.array(battery_time_sim)/3600
    y = []
    for key in battery_soc:
        y.append(np.array(battery_soc[key]))


    fig, axs = plt.subplots(5, sharex=True, sharey=True)
    fig.suptitle('SOC of each EV Battery')

    axs[0].plot(xaxis, y[0], color='tab:blue', linestyle='-')
    axs[0].set_yticks(np.arange(0,1.25,0.5))
    axs[0].set(ylabel='Batt at\nport 1')
    axs[0].grid(True)

    axs[1].plot(xaxis, y[1], color='tab:blue', linestyle='-')
    axs[1].set(ylabel='Batt a\nport 2')
    axs[1].grid(True)

    axs[2].plot(xaxis, y[2], color='tab:blue', linestyle='-')
    axs[2].set(ylabel='Batt at\nport 3')
    axs[2].grid(True)

    axs[3].plot(xaxis, y[3], color='tab:blue', linestyle='-')
    axs[3].set(ylabel='Batt at\nport 4')
    axs[3].grid(True)

    axs[4].plot(xaxis, y[4], color='tab:blue', linestyle='-')
    axs[4].set(ylabel='Batt at\nport 5')
    axs[4].grid(True)
    plt.xlabel('time (hr)')
    # Saving graph to file
    plt.savefig('fundamental_final_battery_SOCs.png', format='png')
    plt.show()
    
    # Charger graph
    # Output graph showing the charging profile for each of the charging
    #   terminals
    xaxis = np.array(charger_time_sim) / 3600
    yaxis = np.array(charger_power)

    plt.plot(xaxis, yaxis, color="tab:blue", linestyle="-")
    plt.yticks(np.arange(0, 11000, 1000))
    plt.ylabel("kW")
    plt.grid(True)
    plt.xlabel("time (hr)")
    plt.title("Instantaneous Power Draw from 5 EVs")
    plt.savefig("fundamental_default_charger_power.png", format="png")
    plt.show()
