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
    
    # Adding extra time request to clear out any pending messages to avoid
    #   annoying errors in the broker log. Any message are tacitly disregarded.
    grantedtime = fed.request_time(h.helics_time_maxtime)
    fed.disconnect()
    h.helicsFederateFree(fed)
    h.helicsCloseLibrary()
    logger.info('Federate finalized')


def get_new_EV(numEVs):
    '''
    Using hard-coded probabilities, a distribution of EVs with support
    for specific charging levels are generated. The number of EVs
    generated is defined by the user.

    :param numEVs: Number of EVs
    :return
        numLvL1: Number of new EVs that will charge at level 1
        numLvL2: Number of new EVs that will charge at level 2
        numLvL3: Number of new EVs that will charge at level 3
        listOfEVs: List of all EVs (and their charging levels) generated

    '''

    # Probabilities of a new EV charging at the specified level.
    lvl1 = 0.05
    lvl2 = 0.6
    lvl3 = 0.35
    listOfEVs = np.random.choice([1,2,3],numEVs,p=[lvl1,lvl2,lvl3]).tolist()
    numLvl1 = listOfEVs.count(1)
    numLvl2 = listOfEVs.count(2)
    numLvl3 = listOfEVs.count(3)

    return numLvl1,numLvl2,numLvl3,listOfEVs




def calc_charging_voltage(EV_list):
    '''
    This function uses the pre-defined charging powers and maps them to
    standard (more or less) charging voltages. This allows the charger
    to apply an appropriately modeled voltage to the EV based on the
    charging power level

    :param EV_list: Value of "1", "2", or "3" to indicate charging level
    :return: charging_voltage: List of charging voltages corresponding
            to the charging power.
    '''

    charging_voltage = []
    # Ignoring the difference between AC and DC voltages for this application
    charge_voltages = [120, 240, 630]
    for EV in EV_list:
        if EV == 1:
            charging_voltage.append(charge_voltages[0])
        elif EV==2:
            charging_voltage.append(charge_voltages[1])
        elif EV==3:
            charging_voltage.append(charge_voltages[2])
        else:
            charging_voltage.append(0)

    return charging_voltage


def estimate_SOC(charging_V, charging_A):
    '''
    The charger has no direct knowledge of the SOC of the EV battery it
    is charging but instead must estimate it based on the effective resistance
    of the battery which is calculated from the applied charging voltage and
    measured charging current. The effective resistance model is used here is
    identical to that of the actual battery; if both the charging voltage
    and current were measured perfectly the SOC estimate here would exactly
    match the true SOC modeled by the battery. For fun, though, a small
    amount of Gaussian noise is added to the current value. This noise
    creates larger errors as the charging current goes down (EV battery
    reaching full SOC).

    :param charging_V: Applied charging voltage
    :param charging_A: Charging current as passed back by the battery federate
    :return: SOC estimate
    '''
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
    np.random.seed(1490)

    ##############  Registering  federate from json  ##########################
    fed = h.helicsCreateCombinationFederateFromConfig("ChargerConfig.json")
    federate_name = fed.name
    logger.info(f'Created federate {federate_name}')
    end_count = fed.n_endpoints
    logger.info(f'\tNumber of endpoints: {end_count}')
    sub_count = fed.n_inputs
    logger.info(f'\tNumber of subscriptions: {sub_count}')
    pub_count = fed.n_publications
    logger.info(f'\tNumber of publications: {pub_count}')
    print(f'Created federate {federate_name}')
    print(f'\tNumber of endpoints: {end_count}')
    print(f'\tNumber of subscriptions: {sub_count}')
    print(f'\tNumber of publications: {pub_count}')

    # Diagnostics to confirm JSON config correctly added the required
    #   endpoints, publications, and subscriptions.
    endid = {}
    for i in range(0, end_count):
        endid[i] = fed.get_endpoint_by_index(i)
        end_name = endid[i].name
        logger.debug(f'\tRegistered Endpoint ---> {end_name}')
    subid = {}
    for i in range(0, sub_count):
        subid[i] = fed.get_subscription_by_index(i)
        sub_name = subid[i].target
        logger.debug(f'\tRegistered subscription---> {sub_name}')

    pubid = {}
    for i in range(0, pub_count):
        pubid[i] = fed.get_publication_by_index(i)
        pub_name = pubid[i].name
        logger.debug(f'\tRegistered publication---> {pub_name}')


    ##############  Entering Execution Mode  ##################################
    fed.enter_executing_mode()
    logger.info('Entered HELICS execution mode')

    # Definition of charging power level (in kW) for level 1, 2, 3 chargers
    charge_rate = [1.8,7.2,50]



    hours = 24*7 # one week
    total_interval = int(60 * 60 * hours)
    update_interval = int(h.helicsFederateGetTimeProperty(
                            fed,
                            h.helics_property_time_period))
    grantedtime = 0

    # Generate an initial fleet of EVs, one for each previously defined
    #   endpoint. This gives each EV a unique link to the EV controller
    #   federate.
    numLvl1,numLvl2,numLvl3,EVlist = get_new_EV(end_count)
    charging_voltage = calc_charging_voltage(EVlist)
    currentsoc = {}

    # Data collection lists
    time_sim = []
    power = []
    charging_current = {}

    # Blocking call for a time request at simulation time 0
    initial_time = 60
    logger.debug(f'Requesting initial time {initial_time}')
    grantedtime = fed.request_time(initial_time)
    logger.debug(f'Granted time {grantedtime}')


    # Apply initial charging voltage
    for j in range(0, pub_count):
        pubid[j].publish(charging_voltage[j])
        logger.debug(f'\tPublishing charging voltage of {charging_voltage[j]} '
                     f' at time {grantedtime}')


    ########## Main co-simulation loop ########################################
    # As long as granted time is in the time range to be simulated...
    while grantedtime < total_interval:

        # Time request for the next physical interval to be simulated
        requested_time = (grantedtime + update_interval)
        logger.debug(f'Requesting time {requested_time}')
        grantedtime = fed.request_time(requested_time)
        logger.debug(f'Granted time {grantedtime}')

        for j in range(0,end_count):

            logger.debug(f'EV {j+1} time {grantedtime}')
            # Model the physics of the battery charging. This happens
            #   every time step whether a message comes in or not and always
            #   uses the latest value provided by the battery model.
            charging_current[j] = subid[j].value
            logger.debug(f'\tCharging current: {charging_current[j]:.2f} from '
                         f'input {subid[j].target}')

            # New EV is in place after removing charge from old EV,
            # as indicated by the zero current draw.
            if charging_current[j] == 0:
                _, _, _, newEVtype = get_new_EV(1)
                EVlist[j] = newEVtype[0]
                charge_V = calc_charging_voltage(newEVtype)
                charging_voltage[j] = charge_V[0]

                currentsoc[j] = 0 # Initial SOC estimate
                logger.debug(f'\t New EV, SOC estimate: {currentsoc[j]:.4f}')
                logger.debug(f'\t New EV, charging voltage:'
                             f' {charging_voltage[j]}')
            else:
                # SOC estimation
                currentsoc[j] = estimate_SOC(charging_voltage[j], charging_current[j])
                logger.debug(f'\t EV SOC estimate: {currentsoc[j]:.4f}')



        # Check for messages from EV Controller
            endpoint_name = endid[j].name
            if endid[j].has_message():
                msg = endid[j].get_message()
                instructions = msg.data
                source = msg.original_source
                logger.debug(f'\tReceived message at endpoint {endpoint_name}'
                             f' from source {source}'
                             f' at time {grantedtime}'
                             f' with command {instructions}')

                # Update charging state based on message from controller
                # The protocol used by the EV and the EV Controller is simple:
                #       EV Controller sends "1" - keep charging
                #       EV Controller sends anything else: stop charging
                # The default state is charging (1) so we only need to
                #   do something if the controller says to stop
                if int(instructions) == 0:
                    # Stop charing this EV
                    charging_voltage[j] = 0
                    logger.info(f'\tEV full; removing charging voltage')
            else:
                logger.debug(f'\tNo messages at endpoint {endpoint_name} '
                             f'recieved at '
                             f'time {grantedtime}')

            # Publish updated charging voltage
            pubid[j].publish(charging_voltage[j])
            logger.debug(f'\tPublishing charging voltage of {charging_voltage[j]} '
                         f' at time {grantedtime}')

            # Send message to Controller with SOC every 15 minutes
            if grantedtime % 900 == 0:
                destination_name = endid[j].default_destination
                message = f'{currentsoc[j]:4f}'
                endid[j].send_data(message, destination_name)  #
                logger.debug(f'Sent message from endpoint {endpoint_name}'
                             f' to destination {destination_name}'
                             f' at time {grantedtime}'
                             f' with payload SOC {message}')

        # Calculate the total power required by all chargers. This is the
        #   primary metric of interest, to understand the power profile
        #   and capacity requirements required for this charging garage.
        total_power = 0
        #logger.debug(f'Calculating charging power')
        for j in range(0,pub_count):
            charging_power = charge_rate[(EVlist[j]-1)]
            total_power += charging_voltage[j] * charging_current[j]
            #logger.debug(f'\tCharging power in kW for EV{j+1}: {charging_power}')

        # Data collection vectors
        time_sim.append(grantedtime)
        power.append(total_power)



    # Cleaning up HELICS stuff once we've finished the co-simulation.
    destroy_federate(fed)

    # Output graph showing the charging profile for each of the charging
    #   terminals
    xaxis = np.array(time_sim)/3600
    yaxis = np.array(power)
    plt.plot(xaxis, yaxis, color='tab:blue', linestyle='-')
    plt.yticks(np.arange(0,25000,1000))
    plt.ylabel('kW')
    plt.grid(True)
    plt.xlabel('time (hr)')
    plt.title('Instantaneous Power Draw from 5 EVs')
    # Saving graph to file
    plt.savefig('advanced_default_charging_power.png', format='png')
    plt.show()
