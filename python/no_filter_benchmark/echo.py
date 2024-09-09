# -*- coding: utf-8 -*-
"""
Created on 5/3/2021

Test federate for evaluating performance of HELICS filter timing. Takes
incoming messages and sends them back to their sender with an unaltered payload.

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

    hours = 1
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
        logger.debug(f'Requesting time {total_interval}\n')
        grantedtime = h.helicsFederateRequestTime (fed, total_interval )
        logger.debug(f'Granted time {grantedtime}')

        if h.helicsEndpointHasMessage(endid):
            msg = h.helicsEndpointGetMessage(endid)
            # This is where things can get tricky. The combination of the reroute 
            # filter and the echo federate make Setting the parameters of this 
            # message complex. The simplest solution for the echo federate is to 
            # make a copy of the payload from the original message and create a 
            # new message with that same payload.
            # payload = h.helicsMessageGetString(msg)
            # h.helicsEndpointSendBytesTo(endid, payload.encode(), "")
        
            # Alternatively, working with the same message object, changing the 
            # original source to this echo favorites and point in the original 
            # destination to the default destination for this federate's endpoint 
            # will also work.
            h.helicsMessageSetOriginalDestination(msg, default_dest)
            h.helicsMessageSetOriginalSource(msg, endid_name)
            
            
            # In the case of this Federation, changing just the destination and 
            # source does not work as expected. If you look at no_filter.py, 
            # you can see that D filter determines the correct destination of 
            # the message based on its original destination. Using the API calls
            # below, that parameter is not changed and thus when this message 
            # is intercepted by the filter federate, it will send it to its 
            # original destination, which is the echo federates endpoint. This 
            # results in the message looping continuously through the echo 
            # federate and the filter federate.
            # h.helicsMessageSetDestination(msg, default_dest)
            # h.helicsMessageSetSource(msg, endid_name)
            h.helicsEndpointSendMessage(endid, msg)
            logger.debug(f'Echoing message at time {grantedtime}')
            





    # Cleaning up HELICS stuff once we've finished the co-simulation.
    destroy_federate(fed)

