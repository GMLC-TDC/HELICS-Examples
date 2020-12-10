# -*- coding: utf-8 -*-
"""
Created on 12/08/2020

This is a simple EV charge controller federate that manages the charging at
a set of charging terminals in a hypothetical EV garage. It receives periodic
SOC messages from each EV (associated with a particular charging terminal)
and sends back a message indicating whether the EV should continue charging
or not (based on whether it is full).

@author: Allison M. Campbell
allison.m.campbell@pnnl.gov
"""

import helics as h
import logging
import numpy as np
import matplotlib.pyplot as plt


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
    status = h.helicsFederateFinalize(fed)
    h.helicsFederateFree(fed)
    h.helicsCloseLibrary()
    logger.info('Federate finalized')


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




if __name__ == "__main__":
    np.random.seed(1490)

    ##############  Registering  federate from json  ##########################
    fed = h.helicsCreateMessageFederateFromConfig("ChargerConfig.json")
    federate_name = h.helicsFederateGetName(fed)
    logger.info(f'Created federate {federate_name}')
    print(f'Created federate {federate_name}')
    end_count = h.helicsFederateGetEndpointCount(fed)
    logging.debug(f'\tNumber of endpoints: {end_count}')

    # Diagnostics to confirm JSON config correctly added the required
    #   endpoints
    endid = {}
    for i in range(0, end_count):
        endid[i] = h.helicsFederateGetEndpointByIndex(fed, i)
        end_name = h.helicsEndpointGetName(endid[i])
        logger.debug(f'\tRegistered Endpoint ---> {end_name}')



    ##############  Entering Execution Mode  ##################################
    h.helicsFederateEnterExecutingMode(fed)
    logger.info('Entered HELICS execution mode')

    # Definition of charging power level (in kW) for level 1, 2, 3 chargers
    charge_rate = [1.8,7.2,50]

    # Generate an initial fleet of EVs, one for each previously defined
    #   handle. This gives each EV a unique link to the EV controller
    #   federate.
    numLvl1,numLvl2,numLvl3,EVlist = get_new_EV(end_count)
    charging_voltage = calc_charging_voltage(EVlist)
    currentsoc = {}


    hours = 24 * 7
    total_interval = int(60 * 60 * hours)
    update_interval = int(h.helicsFederateGetTimeProperty(
                            fed,
                            h.helics_property_time_period))
    grantedtime = 0

    # Data collection lists
    time_sim = []
    power = []
    charging_current = {}

    # Blocking call for a time request at simulation time 0
    initial_time = 60
    logger.debug(f'Requesting initial time {initial_time}')
    grantedtime = h.helicsFederateRequestTime(fed, initial_time )
    logger.debug(f'Granted time {grantedtime}')


    # Apply initial charging voltage
    for j in range(0, end_count):
        #destination = str(h.helicsEndpointGetDefaultDestination(endid[j]))
        message = str(charging_voltage[j])
        h.helicsEndpointSendBytesTo(endid[j], "", message.encode()) #
        logger.debug(f'\tSending charging voltage of {message} '
                     #f' to {destination}'
                     f' from {endid[j]}'
                     f' at time {grantedtime}')


    ########## Main co-simulation loop ########################################
    # As long as granted time is in the time range to be simulated...
    while grantedtime < total_interval:

        # Time request for the next physical interval to be simulated
        requested_time = (grantedtime + update_interval)
        logger.debug(f'Requesting time {requested_time}')
        grantedtime = h.helicsFederateRequestTime (fed, requested_time)
        logger.debug(f'Granted time {grantedtime}')


        for j in range(0,end_count):
            logger.debug(f'EV {j + 1} time {grantedtime}')
            # Model the physics of the battery charging. This happens
            #   every time step whether a message comes in or not and always
            #   uses the latest value provided by the battery model.
            # Check for messages from Battery
            endpoint_name = h.helicsEndpointGetName(endid[j])
            if h.helicsEndpointHasMessage(endid[j]):
                msg = h.helicsEndpointGetMessage(endid[j])
                charging_current[j] = float(h.helicsMessageGetString(msg))
                logger.debug(f'\tCharging current: {charging_current[j]:.2f} from '
                             f' endpoint {endpoint_name}'
                             f' at time {grantedtime}')
            # Send message of voltage to Battery federate
                destination_name = str(
                    h.helicsEndpointGetDefaultDestination(endid[j]))
                h.helicsEndpointSendBytesTo(endid[j], "",
                                           f'{charging_voltage[j]:4f}'.encode())  #
                logger.debug(f'Sent message from endpoint {endpoint_name}'
                         f' at time {grantedtime}'
                         f' with voltage {charging_voltage[j]:4f}')

            else:
                logger.debug(f'\tNo messages at endpoint {endpoint_name} '
                             f'recieved at '
                             f'time {grantedtime}')




        # Calculate the total power required by all chargers. This is the
        #   primary metric of interest, to understand the power profile
        #   and capacity requirements required for this charging garage.
        total_power = 0
        for j in range(0, end_count):
            if charging_current[j] > 0: # EV is still charging
                total_power += charge_rate[(EVlist[j] - 1)]

        # Data collection vectors
        time_sim.append(grantedtime)
        power.append(total_power)



    # Cleaning up HELICS stuff once we've finished the co-simulation.
    destroy_federate(fed)

    # Output graph showing the charging profile for each of the charging
    #   terminals
    xaxis = np.array(time_sim)/3600
    yaxis = np.array(power)
    plt.figure()
    plt.plot(xaxis, yaxis, color='tab:blue', linestyle='-')
    plt.yticks(np.arange(0,100,10))
    plt.ylabel('kW')
    plt.grid(True)
    plt.xlabel('time (hr)')
    plt.title('Instantaneous Power Draw from 5 EVs')
    plt.savefig('fundamental_default_charger_power.png', format='png')

    plt.show()
