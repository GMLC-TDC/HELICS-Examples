#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Monday Sept 14 13:32 2020
(The day I should have been camping but, you know, all of the West Coast
was on fire so I didn't.)

This is a simple filter federate designed to show how such a federate
is written and connected to the federation as a whole.

Ideally, all the filter functionality that is needed could be covered either
by native HELICS filters or existing communication simulation tools (ns-3).
Writing a new simulation tool should be the third and last option. This
federate contains some basic functionality that can be useful to do
slightly fancy things (delays, data contention, cyber security) but
doesn't contain a lot of functionality needed for real communications
network simulation (routing being at the top of the list). All that to
say, this is a demonstration more of how filter federates work than an
example to be followed.


@author: hard312 (Trevor Hardy)
"""

import argparse
import logging
import pprint
import os
import sys
import json
import helics as h
import random
from operator import itemgetter

# Setting up logging
logger = logging.getLogger(__name__)


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




def _open_file(file_path, type='r'):
    """Utilty function to open file with reasonable error handling.


    Args:
        file_path (str) - Path to the file to be opened

        type (str) - Type of the open method. Default is read ('r')


    Returns:
        fh (file object) - File handle for the open file
    """
    try:
        fh = open(file_path, type)
    except IOError:
       logger.error('Unable to open {}'.format(file_path))
    else:
        return fh



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
    fed = h.helicsCreateMessageFederateFromConfig("FilterConfig.json")
    federate_name = h.helicsFederateGetName(fed)
    logger.info(f'Created federate {federate_name}')

    # Diagnostics to confirm JSON config correctly added the required
    #   endpoints
    end_count = h.helicsFederateGetEndpointCount(fed)
    logger.debug(f'\tNumber of endpoints: {end_count}')
    endid = h.helicsFederateGetEndpointByIndex(fed, 0)
    end_name = h.helicsEndpointGetName(endid)
    logger.debug("Registered Endpoint ---> {}".format(end_name))
    return fed, endid


def filter_delay(eq, event):
    delay = 850 + (100 * random.random())
    logger.debug(f'\tRandom delay time: {delay}')
    event['time'] = event['time'] + delay
    eq.append(event)
    logger.debug(f'\tMessage from endpoint {event["source"]}'
                 f' to endpoint {event["dest"]}'
                 f' delayed {delay} seconds'
                 f' with message {event["payload"]}')
    return eq



def filter_hack(eq, event):
    if random.random() > 0.5:
        logger.debug(f'\tMessage hacked')
        if event['msg'] == '0':
            event['msg'] == '1'
        else:
            event['msg'] == '0'
        eq.append(event)
        logger.debug(f'\tMessage from endpoint {event["source"]}'
                     f' to endpoint {event["dest"]}'
                     f' had payload altered to {event["msg"]}')
    else:
        logger.debug(f'\tMessage not hacked')
    return eq


def filter_interfere(eq, event):
    # event must be the first element in the eq
    threshold = 300
    event_time = event['time']
    delete_idx = []

    # Interference can only happen if there is more than one message
    #   in the event queue
    if len(eq) > 1:
        for idx, e in enumerate(eq):
            logger.debug(f'Comparing primary message to eq[{eq}]')
            # Don't check for interference between the primary message
            #   (`event` = eq[0]) and itself.
            if idx > 0:
                dt = e['time'] - event_time
                logger.debug(f'\tTime delta: {dt}')
                if dt < 0:
                    logger.warning(f'eq apppears unordered:'
                                   f'\n\teq[0]["time"] = {event_time}'
                                   f'\n\teq[{idx}]["time"] = {e["time"]}')
                if dt < threshold:
                    logger.debug(f'\t{dt} is less than interference '
                                 f'threshold ({threshold}) and is '
                                 f'interfering')
                    # If the list is empty, add the primary event as the
                    #   to the delete_list. That is, the primary message
                    #   and the next message in eq (eq[1]) are interfering
                    #   with each other.
                    if not delete_idx:
                        delete_idx.append(0)
                        logger.debug(f'\tScheduling event for deletion: '
                                     f'eq[0]')
                    delete_idx.append(idx)
                    logger.debug(f'\tScheduling event for deletion: '
                                 f'eq[{idx}]')
                else:
                    break

        # Deleting events from the eq that are causing interference
        #   Work from the largest idx to the smallest so the index
        #   values we care about don't change as the events are removed
        #   from eq
        delete_idx.sort(reverse=True)
        for i in delete_idx:
            logger.debug(f'Deleting event from queue:'
                         f'\tsource: {eq[i]["source"]}'
                         f'\tdestination: {eq[i]["dest"]}'
                         f'\tpayload: {eq[i]["payload"]}'
                         f'\tdelivery time: {eq[i]["time"]}')
            del eq[i]
    return eq





def filter_message(eq, event, cmd):
    if cmd == 'delay':
        logger.debug(f'Peforming filter operation delay')
        eq = filter_delay(eq, event)
    elif cmd == 'hack':
        logger.debug(f'Peforming filter operation hack')
        eq = filter_hack(eq, event)
    elif cmd == 'interfere':
        logger.debug(f'Peforming filter operation interfere')
        eq = filter_interfere(eq, event)
    else:
        logger.warning(f'Unrecognized command: {cmd}'
                       f'\n\t event queue unmodified')
    return eq



def run_cosim(fed, endid):

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


    h.helicsFederateEnterExecutingMode(fed)
    logger.info('Entered HELICS execution mode')


    hours = 24*7 # one week
    total_interval = int(60 * 60 * hours)

    # Blocking call for a time request at max simulation time
    fake_max_time = int(h.HELICS_TIME_MAXTIME / 1000)
    starttime = fake_max_time
    logger.debug(f'Requesting initial time {starttime}')
    grantedtime = h.helicsFederateRequestTime (fed, starttime)
    logger.debug(f'Granted time {grantedtime}')

    while grantedtime < total_interval:
        # In HELICS, when multiple messages arrive at an endpoint they
        # queue up and are popped off one-by-one with the
        #   "helicsEndpointHasMessage" API call. When that API doesn't
        #   return a message, you've processed them all.
        while h.helicsEndpointHasMessage(endid):
            msg = h.helicsEndpointGetMessage(endid)
            msg_str = h.helicsMessageGetString(msg)
            source = h.helicsMessageGetOriginalSource(msg)
            dest = h.helicsMessageGetOriginalDestination(msg)
            time =  h.helicsMessageGetTime(msg)
            logger.debug(f'Received message from endpoint {source}'
                         f' to endpoint {dest}'
                         f' at time {grantedtime}'
                         f' with message {msg_str}')
            event = {"payload":msg_str,
                        "source":source,
                        "dest":dest,
                        "time":time}
            eq = filter_message(eq, event, 'delay')
            if source == 'EVController_federate/endpoint':
                eq = filter_message(eq, event, 'hack')

        # Sort event queue to get it back in order
        eq = sorted(eq, key=itemgetter('time'))

        # Acting on any events that need to be dequeued
        # Running interference filter. This filter has the ability to
        #   remove events from eq. We may not have any messages to send
        #   after interference runs
        event = eq[0]
        eq = filter_message(eq, event, 'interfere')

        # After filtering, send all messages whose time has come (or past;
        #   in which case something has gone wrong)
        if eq:
            while eq[0]['time'] <= grantedtime:
                h.helicsEndpointSendMessageRaw(endid, eq[0]['dest'],
                                               eq[0]['payload'].encode())
                logger.debug(f'Sent message from endpoint {endid}'
                             f' to endpoint {eq[0]["dest"]}'
                             f' at time {grantedtime}'
                             f' with message {eq[0]["payload"]}')
                del eq[0]


        if eq:
            # Event queue not empty, need to schedule filter federate to
            #   run again when its time to deliver the next message in the
            #   queue
            requested_time = eq[0]['time']
        else:
            # If no events in queue, schedule run for end of simulation.
            #   Filter federate will be granted an earlier time if a
            #   message is rerouted to the filter federate.
            requested_time = fake_max_time
        logger.debug(f'Requesting time {requested_time}')
        grantedtime = h.helicsFederateRequestTime(fed, requested_time)
        logger.debug(f'Granted time {grantedtime}')



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
    random.seed(args.random_seed)
    logger.debug(f'Intializing RNG with seed {args.random_seed}')
    fed, endid = configure_federate()
    run_cosim(fed, endid)
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
    parser.add_argument('-r',
                        '--random_seed',
                        nargs='?',
                        default=2608)
    args = parser.parse_args()
    _auto_run(args)
