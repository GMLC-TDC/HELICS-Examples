#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Monday May 3 2021

Filter that doesn't filter messages at all. I sends on all messages that are
routed to it without modification. It uses the original destination of the
message to determine where the message should be sent on to; the reroute filter 
changes the simple `destination` field when it reroutes the message to the 
filter federate.

@author: hard312 (Trevor Hardy)
"""

import argparse
import logging
import pprint
import os
import sys


import helics as h
import random
from operator import itemgetter

# Setting up logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Adding custom logging level "DATA" to use for putting
#  all the simulation data on. "DATA" is between "DEBUG"
#  and "NOTSET" in terms of priority. 
DATA_LEVEL_NUM = 5
logging.addLevelName(DATA_LEVEL_NUM, "DATA")


def data(self, message, *args, **kws):
    if self.isEnabledFor(DATA_LEVEL_NUM):
        self._log(DATA_LEVEL_NUM, message, args, **kws)


logging.DATA = DATA_LEVEL_NUM
logging.Logger.data = data

# Setting up pretty printing, mostly for debugging.
pp = pprint.PrettyPrinter(indent=4, )



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


def configure_federate():
    fed = h.helicsCreateMessageFederateFromConfig("filter_config.json")
    federate_name = h.helicsFederateGetName(fed)
    logger.info(f'Created federate {federate_name}')

    # Diagnostics to confirm JSON config correctly added the required
    #   endpoints
    endid = h.helicsFederateGetEndpointByIndex(fed, 0)
    end_name = h.helicsEndpointGetName(endid)
    return fed, endid, end_name


def run_cosim(fed, endid, end_name, args):
    # The event queue ("eq") is the master list of events that the filter
    #   federates works on. In this simple filter federate, each event
    #   will be a dictionary with a few parameters:
    #       'dest' - destination of message
    #       'time' - time when the message should be sent on to its
    #               intended destination
    #       'payload' - content of the message being sent
    #
    #   When eq is empty, there are no messages being
    #   filtered by the federate. When there are events in the queue it
    #   indicates the filter federate has messages it is holding onto
    #   that it needs to forward on (at the indicated time).
    #
    eq = []

    # sub = h.helicsFederateRegisterSubscription(fed, "Charger/EV1_voltage", "")

    logger.info('Attempting to enter execution mode')
    h.helicsFederateEnterExecutingMode(fed)
    logger.info('Entered HELICS execution mode')

    hours = 24  # one week
    total_interval = int(60 * 60 * hours)

    # Blocking call for a time request at max simulation time
    # fake_max_time = int(h.HELICS_TIME_MAXTIME / 1000)
    fake_max_time = 100000000
    starttime = fake_max_time
    #starttime = 0
    logger.debug(f'Requesting initial time {starttime}')
    grantedtime = h.helicsFederateRequestTime(fed, starttime)
    logger.debug(f'Granted time {grantedtime}')

    while grantedtime < total_interval:

        # value = h.helicsInputGetString(sub)
        # logger.debug(f'Got message {value} from random sub at time {grantedtime}.')

        # In HELICS, when multiple messages arrive at an endpoint they
        # queue up and are popped off one-by-one with the
        #   "helicsEndpointHasMessage" API call. When that API doesn't
        #   return a message, you've processed them all.
        while h.helicsEndpointHasMessage(endid):
            msg = h.helicsEndpointGetMessage(endid)
            msg_str = h.helicsMessageGetString(msg)
            source = h.helicsMessageGetOriginalSource(msg)
            dest = h.helicsMessageGetOriginalDestination(msg)
            time = h.helicsMessageGetTime(msg)
            logger.debug(f'Received message from endpoint {source}'
                         f' to endpoint {dest}'
                         f' for delivery at time {time}'
                         f' with payload \"{msg_str}\"')
            h.helicsMessageSetDestination(msg, dest)
            h.helicsEndpointSendMessage(endid, msg)
            logger.debug(f'Sent message from endpoint {end_name}'
                             f' appearing to come from {source}'
                             f' to endpoint {dest}'
                             f' at time {grantedtime}'
                             f' with payload \"{msg_str}\"')
        logger.debug(f'Requesting time {fake_max_time}')
        grantedtime = h.helicsFederateRequestTime(fed, fake_max_time)


def _auto_run(args):
    """This function executes when the script is called as a stand-alone
    executable.

    A more complete description of this code can be found in the
    docstring at the beginning of this file.

    Args:
        '-a' or '--auto_run_dir' - Path of the auto_run folder
        that contains examples of the files used in this script. Used
        for development purposes as well as models/examples/documentation
        of the format and contents expected in said files

    Returns:
        (none)
    """
    fed, endid, end_name = configure_federate()
    run_cosim(fed, endid, end_name, args)
    destroy_federate(fed)


if __name__ == '__main__':
    # TDH: This slightly complex mess allows lower importance messages
    # to be sent to the log file and ERROR messages to additionally
    # be sent to the console as well. Thus, when bad things happen
    # the user will get an error message in both places which,
    # hopefully, will aid in trouble-shooting.
    fileHandle = logging.FileHandler("Filter.log", mode='w')
    fileHandle.setLevel(logging.DEBUG)
    streamHandle = logging.StreamHandler(sys.stdout)
    streamHandle.setLevel(logging.ERROR)
    logging.basicConfig(level=logging.DEBUG,
                        handlers=[fileHandle, streamHandle])

    parser = argparse.ArgumentParser(description='Demo HELICS filter federate')
    # TDH: Have to do a little bit of work to generate a good default
    # path for the auto_run folder (where the development test data is
    # held.
    script_path = os.path.dirname(os.path.realpath(__file__))
    auto_run_dir = os.path.join(script_path)
    parser.add_argument('-a',
                        '--auto_run_dir',
                        nargs='?',
                        default=script_path)
    args = parser.parse_args()
    _auto_run(args)
