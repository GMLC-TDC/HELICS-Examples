# -*- coding: utf-8 -*-
"""
Created on Mar 2023

Simple model of a single-cell lithium battery charger

@author: Trevor Hardy
trevor.hardy@pnnl.gov
"""

# Python library imports
import helics as h
import logging


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

def set_charging_constant_current(i, v):
    if i >= target_constant_current:
        logger.info(f'\tHIGH charging current ({i:.3f} >= {target_constant_current})')
        v = v * 0.85
    else:
        logger.info(f'\tLOW charging current ({i:0.3f} < {target_constant_current})')
        v = v * 1.15

    if v > v_max:
        v = v_max
    return v


# Simulator set-up
max_sim_time = 9999999999
sim_step_size = 60
period = 1
fed_name = "charger"
v_init = 5
fully_charged = False
target_constant_current = 0.3
terminal_charging_current = 0.05
v_max = 10

# Create federate
fedinfo = h.helicsCreateFederateInfo()
h.helicsFederateInfoSetCoreTypeFromString(fedinfo, "zmq")
h.helicsFederateInfoSetIntegerProperty(fedinfo, h.helics_property_int_log_level, 1)
h.helicsFederateInfoSetTimeProperty(fedinfo, h.helics_property_time_period, period)
h.helicsFederateInfoSetFlagOption(fedinfo, h.helics_flag_uninterruptible, True)
h.helicsFederateInfoSetFlagOption(fedinfo, h.HELICS_FLAG_TERMINATE_ON_ERROR, True)
h.helicsFederateInfoSetFlagOption(fedinfo, h.helics_flag_wait_for_current_time_update, True)
fed = h.helicsCreateValueFederate(fed_name, fedinfo)
logger.info(f'Created federate {fed_name}')

# Create federate interfaces
pub_v = h.helicsFederateRegisterPublication(fed, 'voltage', h.HELICS_DATA_TYPE_DOUBLE, 'V')
sub_i = h.helicsFederateRegisterSubscription(fed, 'battery/current', 'A')


# Enter initialization
h.helicsFederateEnterInitializingMode(fed)
h.helicsPublicationPublishDouble(pub_v, v_init)
logger.info(f'Initialized charger federates with published charging voltage of f{v_init}.')

# Enter execution
h.helicsFederateEnterExecutingMode(fed)
logger.info('Entered executing mode')
granted_time = h.helicsFederateGetCurrentTime(fed)
i = h.helicsInputGetDouble(sub_i)
v = set_charging_constant_current(i, v_init)
h.helicsPublicationPublishDouble(pub_v, v)
logger.info(f'Initial time: {granted_time}')
logger.info(f'\tReceived charging current: {i:.3f}')
logger.info(f'\tSent charging voltage: {v:.3f}')



# Main (co-)simulation loop
while (granted_time < max_sim_time) and not fully_charged:
    # Request time
    requested_time = granted_time + sim_step_size
    logger.info(f'Requesting time: {requested_time}')
    granted_time = h.helicsFederateRequestTime(fed, requested_time)
    logger.info(f'Granted time: {granted_time}')

    # Get inputs
    i = h.helicsInputGetDouble(sub_i)
    logger.info(f'\tReceived charging current (A): {i:.3f}')

    # Update internal model
    if i > terminal_charging_current:
        v = set_charging_constant_current(i, v)
        fully_charged = False
    else:
        v = 0 # Remove charging voltage to terminate charging
        fully_charged = True


    # Send outputs
    h.helicsPublicationPublishDouble(pub_v, v)
    logger.info(f'\tPublished charging voltage (V): {v:.3f}')


if fully_charged:
    logger.info(f'Fully charged (i = {i:.3f}), ending co-simulation')
    destroy_federate(fed)