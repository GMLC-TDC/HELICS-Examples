"""
Created on 10/02/2024

This is a federate that creates a cloning filter that sends the cloned control
signals to itself and logs them. It is intended to  demonstrate the 
configuration and use of the cloning filter. 

@author: Trevor Hardy
trevor.hardy@pnnl.gov
"""

import helics as h
import logging
import numpy as np
import sys
import time
import argparse

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
    logger.info('Check log file for cloned messages.')


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    parser = argparse.ArgumentParser(description="")
    parser.add_argument('-m', '--max_time',
                        help="flag to only create a graph of the historic data"
                                "(no data collection)",
                        action=argparse.BooleanOptionalAction)
    args = parser.parse_args()




    ##############  Registering  federate from json  ##########################
    fed = h.helicsCreateMessageFederateFromConfig("LoggerConfig.json")
    federate_name = h.helicsFederateGetName(fed)
    logger.info(f'Created federate {federate_name}')


    #### Register endpoint #####
    # Only one endpoint for the controller
    endid = h.helicsFederateGetEndpointByIndex(fed, 0)
    end_name = h.helicsEndpointGetName(endid)
    logger.info("Registered Endpoint ---> {}".format(end_name))

    ##############  Entering Execution Mode  ##################################
    h.helicsFederateEnterExecutingMode(fed)
    logger.info('Entered HELICS execution mode')

    hours = 24*1 # one week
    total_interval = int(60 * 60 * hours)
    grantedtime = 0

    # It is common in HELICS for controllers to have slightly weird timing
    #   Generally, controllers only need to produce new control values when
    #   their inputs change. Because of this, it is common to have them
    #   request a time very far in the future (helics_time_maxtime) and
    #   when a signal arrives, they will be granted a time earlier than
    #   that, recalculate the control output and request a very late time
    #   again.

    # There appears to be a bug related to maxtime in HELICS 2.4 that can
    #   can be avoided by using a slightly smaller version of maxtime
    #   (helics_time_maxtime is the largest time that HELICS can internally
    #   represent and is an approximation for a point in time very far in
    #   in the future).
    if args.max_time:
        logger.debug('MAXTIME flag set')
        starttime = h.HELICS_TIME_MAXTIME
    else:
        starttime = 0
    logger.debug(f'Requesting initial time {starttime}')
    grantedtime = h.helicsFederateRequestTime (fed, starttime)
    logger.debug(f'Granted time {grantedtime}')

    while grantedtime < total_interval:


        # In HELICS, when multiple messages arrive at an endpoint they
        # queue up and are popped off one-by-one with the
        #   "helicsEndpointHasMessage" API call. When that API doesn't
        #   return a message, you've processed them all.
        while h.helicsEndpointHasMessage(endid):
        
            # Only log the time if we have a message
            logger.info(f'Granted time: {grantedtime}')

            # Get the SOC from the EV/charging terminal in question
            msg = h.helicsEndpointGetMessage(endid)
            currentsoc = h.helicsMessageGetString(msg)
            source = h.helicsMessageGetOriginalSource(msg)
            logger.debug(f'\tReceived message from endpoint {source}'
                         f' at time {grantedtime}'
                         f' with SOC {currentsoc}')


        # Since we've dealt with all the messages that are queued, there's
        #   nothing else for the federate to do until/unless another
        #   message comes in. Request a time very far into the future
        #   and take a break until/unless a new message arrives.  
        if args.max_time:
            #logger.debug(f'Requesting time {h.HELICS_TIME_MAXTIME}')
            grantedtime = h.helicsFederateRequestTime (fed, h.HELICS_TIME_MAXTIME) 
        else:
            #logger.debug(f'Requesting next step time')
            grantedtime = fed.request_next_step()
        # logger.info(f'Granted time: {grantedtime}')

    # Close out co-simulation execution cleanly now that we're done.
    destroy_federate(fed)

    