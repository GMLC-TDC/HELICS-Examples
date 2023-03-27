# -*- coding: utf-8 -*-
"""
Created on Mar 2023

Simple model of a constant current battery charger

@author: Trevor Hardy
trevor.hardy@pnnl.gov
"""

# Python library imports
import helics as h
import logging
import numpy as np


# Default logging
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
    #   annoying errors in the broker log. Any messages are tacitly disregarded.
    grantedtime = h.helicsFederateRequestTime(fed, h.HELICS_TIME_MAXTIME)
    status = h.helicsFederateDisconnect(fed)
    h.helicsFederateFree(fed)
    h.helicsCloseLibrary()
    logger.info("Federate finalized")


# Simulator set-up
max_sim_time = 9999999999
sim_step_size = 60
t_init = 0
soc_init = 0 # Ah
battery_capacity = 5 #Ah
# Define battery physics as empirical values
socs = np.array([0, 1])
effective_R = np.array([0.1, 200]) # ohms
period = 1
fed_name = "battery"

# Create federate
fedinfo = h.helicsCreateFederateInfo()
h.helicsFederateInfoSetCoreTypeFromString(fedinfo, "zmq")
h.helicsFederateInfoSetIntegerProperty(fedinfo, h.helics_property_int_log_level, 1)
h.helicsFederateInfoSetTimeProperty(fedinfo, h.helics_property_time_period, period)
h.helicsFederateInfoSetFlagOption(fedinfo, h.helics_flag_uninterruptible, False)
h.helicsFederateInfoSetFlagOption(fedinfo, h.HELICS_FLAG_TERMINATE_ON_ERROR, True)
h.helicsFederateInfoSetFlagOption(fedinfo, h.helics_flag_wait_for_current_time_update, False)
fed = h.helicsCreateValueFederate(fed_name, fedinfo)
logger.info(f'Created federate {fed_name}')

# Create federate interfaces
pub_i = h.helicsFederateRegisterPublication(fed, 'current', h.HELICS_DATA_TYPE_DOUBLE, 'A')
sub_v = h.helicsFederateRegisterSubscription(fed, 'charger/voltage', 'V')

# Enter initialization
init_current = 0
h.helicsFederateEnterInitializingMode(fed)
h.helicsPublicationPublishDouble(pub_i, init_current)
logger.info(f'Initialized charger federates with published current of f{init_current}.')

# Enter execution
h.helicsFederateEnterExecutingMode(fed)
logger.info('Entered executing mode')
granted_time = h.helicsFederateGetCurrentTime(fed)
v = h.helicsInputGetDouble(sub_v)
soc = soc_init
last_time = 0

# Main (co-)simulation loop
while (granted_time < max_sim_time) and (v > 0):
    # Request time
    requested_time = granted_time + sim_step_size
    logger.info(f'Requesting time: {requested_time}')
    granted_time = h.helicsFederateRequestTime(fed, requested_time)
    logger.info(f'Granted time: {granted_time}')

    # Get inputs
    v = h.helicsInputGetDouble(sub_v)
    logger.info(f'Received charging voltage (V): {v:.3f}')

    if v > 0:
        # Update internal model
        R = np.interp(soc, socs, effective_R)
        i = v / R
        added_charge = i * (granted_time - last_time)/3600
        soc = soc + added_charge
        last_time = granted_time
        logger.info(f'\tAdded charge (Ah): {added_charge:.5f}')
        logger.info(f'\tSOC (Ah): {soc:.5f}')

        # Send outputs
        h.helicsPublicationPublishDouble(pub_i, i)
        logger.info(f'\tPublished charging current (A): {i:.5f}')
    else:
        # Don't need to do anything, simulation will terminate on next pass
        #    through while loop
        pass

destroy_federate(fed)
logger.info(f'Fully charged (Vcharge = {v:.3f}), ending co-simulation')