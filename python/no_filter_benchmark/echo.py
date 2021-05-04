# -*- coding: utf-8 -*-
"""
Created on 5/3/2021

Test federate for evaluating performance of HELICS filter timing.

@author: Trevor Hardy
trevor.hardy@pnnl.gov
"""

import helics as h
import logging
import time

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



if __name__ == "__main__":


    ##############  Registering  federate from json  ##########################
    fed = h.helicsCreateCombinationFederateFromConfig("echo_config.json")
    federate_name = h.helicsFederateGetName(fed)
    endid = h.helicsFederateGetEndpointByIndex(fed, 0)
    endid_name = h.helicsEndpointGetName(endid)


    ##############  Entering Execution Mode  ##################################
    h.helicsFederateEnterExecutingMode(fed)
    logger.info('Entered HELICS execution mode')

    hours = 24
    total_interval = int(60 * 60 * hours)
    update_interval = int(h.helicsFederateGetTimeProperty(
                            fed,
                            h.HELICS_PROPERTY_TIME_PERIOD))
    grantedtime = 0


    # Blocking call for a time request at simulation time 0
    initial_time = total_interval 
    logger.debug(f'Requesting initial time {initial_time}')
    grantedtime = h.helicsFederateRequestTime(fed, initial_time )
    logger.debug(f'Granted time {grantedtime}')


    default_dest = h.helicsEndpointGetDefaultDestination(endid)
    logger.debug(f'Default destination: {default_dest}')

    ########## Main co-simulation loop ########################################
    # As long as granted time is in the time range to be simulated...
    while grantedtime < total_interval:

        # Time request for the next physical interval to be simulated
        #logger.debug(f'Requesting time {requested_time}\n')
        grantedtime = h.helicsFederateRequestTime (fed, total_interval )
        #logger.debug(f'Granted time {grantedtime}')

        if h.helicsEndpointHasMessage(endid):
        # for the reroute filter to work properly, it is necessary to change the
        # original destination and source. Just changing the destination and 
        # source as in the commented out API calls doesn't work. The reroute 
        # filter appears to operate on the "original" fields.
            msg = h.helicsEndpointGetMessage(endid)
            # h.helicsMessageSetDestination(msg, default_dest)
            h.helicsMessageSetOriginalDestination(msg, default_dest)
            # h.helicsMessageSetSource(msg, endid_name)
            h.helicsMessageSetOriginalSource(msg, endid_name)
            h.helicsEndpointSendMessage(endid, msg)
            logger.debug(f'Echoing message at time {grantedtime}')
            
#             payload = h.helicsMessageGetString(msg)
#             h.helicsEndpointSendBytesTo(endid, payload.encode(), "")




    # Cleaning up HELICS stuff once we've finished the co-simulation.
    destroy_federate(fed)

