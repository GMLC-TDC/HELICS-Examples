# -*- coding: utf-8 -*-
"""
Created on <date>

<Description of federate>

@author: <author name>
<author email>
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


# Simulator set-up
max_sim_time = 0
sim_step_size = 0
period = 0
fed_name = ""


# Create federate
fedinfo = h.helicsCreateFederateInfo()
h.helicsFederateInfoSetCoreTypeFromString(fedinfo, "zmq")
# Set federate options
h.helicsFederateInfoSetFlagOption(fedinfo, h.HELICS_FLAG_TERMINATE_ON_ERROR, True)
h.helicsFederateInfoSetTimeProperty(fedinfo, h.helics_property_time_period, period)
h.helicsFederateInfoSetIntegerProperty(fedinfo, h.helics_property_int_log_level, 1)
h.helicsFederateInfoSetFlagOption(fedinfo, h.helics_flag_uninterruptible, True)
h.helicsFederateInfoSetFlagOption(fedinfo, h.helics_flag_wait_for_current_time_update, True)
fed = h.helicsCreateValueFederate(fed_name, fedinfo)
logger.info(f'Created federate {fed_name}')

# Create federate interfaces
pub = h.helicsFederateRegisterPublication()
sub = h.helicsFederateRegisterSubscription()
ep = h.helicsFederateRegisterEndpoint()

# Enter initialization
h.helicsFederateEnterInitializingMode(fed)
h.helicsPublicationPublishDouble()

# Enter execution
h.helicsFederateEnterExecutingMode(fed)
logger.info('Entered executing mode')
granted_time = h.helicsFederateGetCurrentTime(fed)
logger.info(f'Initial time: {granted_time}')

# Get initial subscription values and publish new values
i = h.helicsInputGetDouble()
h.helicsPublicationPublishDouble()

# Main (co-)simulation loop
while (granted_time < max_sim_time):
    # Request time
    requested_time = granted_time + sim_step_size
    logger.info(f'Requesting time: {requested_time}')
    granted_time = h.helicsFederateRequestTime(fed, requested_time)
    logger.info(f'Granted time: {granted_time}')

    # Get inputs
    i = h.helicsInputGetDouble()

    # Update internal model

    # Send outputs
    h.helicsPublicationPublishDouble()


# Terminate and clean-up
destroy_federate()