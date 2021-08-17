"""
Created on 5/27/2020

@author: bearcub
"""

import helics as h
import logging
import numpy as np
import sys
import time
#import graph
import argparse
import matplotlib.pyplot as plt

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.DEBUG)

#

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
    h.helicsFederateFree(fed)
    h.helicsCloseLibrary()
    logger.info('Federate finalized')

def create_message_federate(fedinitstring,name,period):
    # Create Federate Info object that describes the federate properties
    fedinfo = h.helicsCreateFederateInfo()
    # Set core type from string
    h.helicsFederateInfoSetCoreTypeFromString(fedinfo, "tcpss")
    #assert status == 0
    # Federate init string
    # you need to tell helics what message bus to use
    h.helicsFederateInfoSetCoreInitString(fedinfo, fedinitstring)
    #assert status == 0
    # Set one second message interval
    h.helicsFederateInfoSetTimeProperty(fedinfo, h.helics_property_time_period, period)
    #assert status == 0
    # set wait for current time update to true
    h.helicsFederateInfoSetFlagOption(fedinfo, h.helics_flag_uninterruptible, False)
    # h.helics_flag_uninterruptible should have integer value of 1
    #assert status == 0
    # see 'helics_federate_flags' in
    # https://docs.helics.org/en/latest/doxygen/helics__enums_8h_source.html
    h.helicsFederateInfoSetIntegerProperty(fedinfo, h.helics_property_int_log_level, 1)
    # more info:
    # https://docs.helics.org/en/latest/user-guide/logging.html
    # https://docs.helics.org/en/latest/doxygen/helics__enums_8h_source.html
    # scroll to section on 'helics_log_levels'
    #print('status is',status)
    # make sure these links aren't dead
    # "terminate_on_error": true,
    h.helicsFederateInfoSetFlagOption(fedinfo, 72, True)

    # Create combo federate and give it a name
    fed = h.helicsCreateMessageFederate(name, fedinfo)

    # should this actually be a message federate?
    #fed = h.helicsCreateMessageFederate(name, fedinfo)
    print("Message federate created")

    return fed

if __name__ == "__main__":
    helicsversion = h.helicsGetVersion()
    print("EV Orchestration Example: Helics version = {}".format(helicsversion))


    parser = argparse.ArgumentParser(description='EV simulator')
    parser.add_argument('--port', type=int, default=-1,
                    help='port of the HELICS broker')

    parser.add_argument('--numEVs', type=int, default=1,
                    help='number of EVs in the federation')

    parser.add_argument('--hours', type=int, default=1,
                    help='duration of co-sim in hours')

    args = parser.parse_args()

    if args.port != -1:
        fedinitstring="--brokerport="+str(args.port)
    else:
        fedinitstring=""

    print("Federate Init String = {}".format(fedinitstring))


    name = 'Charger'
    # assume the EV Charger needs 1 minute to determine whether or not to charge
    # the vehicles
    period = 60
    fed = create_message_federate(fedinitstring,name,period)

    #### Register interfaces #####
# Register the endpoints and their destinations
# the EVCharger will subscribe to each EV
    num_EVs = args.numEVs
    end_EVsoc = []
    enddest_EVsoc = []
    EVs = range(1,num_EVs+1)
    for EV in EVs:
        end_name = f'EV{EV}.soc'
        end_EVsoc.append(
            h.helicsFederateRegisterEndpoint(
                fed, end_name, 'double'
            )

        )
        dest_name = f'Battery/EV{EV}.soc'
        enddest_EVsoc.append(
            h.helicsEndpointSetDefaultDestination(
                end_EVsoc[EV-1], dest_name
            )
        )
        print(f"end point {end_name} registered to {dest_name}")

    end_count = h.helicsFederateGetEndpointCount(fed)
    #print(end_count)
    fed_name = h.helicsFederateGetName(fed)
    print(" Federate {} has been registered".format(fed_name))
    #test = h.helicsEndpointGetName(end_EVsoc[0])
    #print(test)
######################   Entering Execution Mode  ##########################################################

    h.helicsFederateEnterExecutingMode(fed)
    print('hello!!! entering execution mode')

    hours = args.hours # one week
    total_interval = int(60 * 60 * hours)
    update_interval = int(h.helicsFederateGetTimeProperty(
                            fed,
                            h.helics_property_time_period))
    grantedtime = 0
#
## Step through each time period starting from t = 0
    time_sim = []
    instructions = []
    #for t in range(0, total_interval, update_interval): #

    while grantedtime < total_interval:

        # Time request for the next physical interval to be simulated
        requested_time = (grantedtime + update_interval)
        logger.debug(f'Requesting time {requested_time}')
        grantedtime = h.helicsFederateRequestTime (fed, requested_time)
        logger.debug(f'Granted time {grantedtime}')

        for j in range(0,end_count):
            logger.debug(f'EV {j + 1} time {grantedtime}')
            # 1. Receive SOC
            # Check for messages from Battery
            endpoint_name = h.helicsEndpointGetName(end_EVsoc[j])
            if h.helicsEndpointHasMessage(end_EVsoc[j]):
                msg = h.helicsEndpointGetMessage(end_EVsoc[j])
                currentsoc = h.helicsMessageGetString(msg)
                # 2. Send instructions
                #destination_name = str(h.helicsEndpointGetDefaultDestination(end_EVsoc[j]))
                print(grantedtime/3600,currentsoc)
                if float(currentsoc) <= 0.9:
                    instructions = 1
                else:
                    instructions = 0
                message = str(instructions)
                logger.debug(f'\t instructions: {instructions} from '
                             f' endpoint {endpoint_name}'
                             f' at time {grantedtime}')
                h.helicsEndpointSendBytesTo(end_EVsoc[j], message, "")  #
                logger.debug(f'Sent message')
                #print('Sent instructions: {}'.format(instructions))
            else:
                logger.debug(f'\tNo messages at endpoint {endpoint_name} '
                             f'recieved at '
                             f'time {grantedtime}')


    #logger.info("Destroying federate")
    destroy_federate(fed)
    #logger.info("Done!")
