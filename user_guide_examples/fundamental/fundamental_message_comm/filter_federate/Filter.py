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
import helics as h
import random
from operator import itemgetter

# Setting up logging
logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.DEBUG)

# Setting up pretty printing, mostly for debugging.
pp = pprint.PrettyPrinter(
    indent=4,
)


def _open_file(file_path, type="r"):
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
        logger.error("Unable to open {}".format(file_path))
    else:
        return fh


def configure_federate():
    fed = h.helicsCreateMessageFederateFromConfig("FilterConfig.json")
    federate_name = h.helicsFederateGetName(fed)
    logger.info(f"Created federate {federate_name}")

    # Diagnostics to confirm JSON config correctly added the required
    #   endpoints
    end_count = h.helicsFederateGetEndpointCount(fed)
    logger.debug(f"\tNumber of endpoints: {end_count}")
    endid = h.helicsFederateGetEndpointByIndex(fed, 0)
    end_name = h.helicsEndpointGetName(endid)
    logger.debug("Registered Endpoint ---> {}".format(end_name))
    return fed, endid, end_name


def filter_drop_delay(eq, drop_rate, delay_time):
    if random.random() > drop_rate:
        logger.debug(f"\t\t\tMessage not randomly dropped")
        # Pulling incoming message from its parking spot at the end of eq
        msg_dict = eq[-1]
        del eq[-1]
        # Only need to delay messages that are not dropped
        # Messages are normally sent every 900 seconds
        # Larger range of random int results in greater disturbance to control mechanism
        delay = random.randint(-delay_time, delay_time)
        if delay < 0:
            delay = 0
        logger.debug(f"\t\t\tRandom delay time: {delay}")
        transmit_time = msg_dict["time"] + delay
        h.helicsMessageSetTime(msg_dict["msg_obj"], transmit_time)
        msg_dict["time"] = transmit_time
        eq.append(msg_dict)
        logger.debug(
            f'\t\t\tMessage from endpoint {msg_dict["source"]}'
            f' to endpoint {msg_dict["dest"]}'
            f' delayed to time {msg_dict["time"]} seconds'
            f' with payload "{msg_dict["payload"]}"'
        )
    else:
        # Because the message is dropped, we remove it from the end of th eq
        del eq[-1]
        logger.debug(f"\t\t\tMessage randomly dropped")
    return eq


def filter_hack(eq, hack_success_rate):
    if random.random() < hack_success_rate:
        logger.debug(f"\t\t\tMessage hacked")
        # Pulling incoming message from its parking spot at the end of eq
        msg_dict = eq[-1]
        del eq[-1]
        if msg_dict["payload"] == "0":
            msg_dict["payload"] = "1"
        else:
            msg_dict["payload"] = "0"
        h.helicsMessageSetString(msg_dict["msg_obj"], msg_dict["payload"])
        eq.append(msg_dict)
        logger.debug(
            f'\t\t\tMessage from endpoint {msg_dict["source"]}'
            f' to endpoint {msg_dict["dest"]}'
            f' had payload altered to {msg_dict["payload"]}'
        )
    else:
        logger.debug(f"\t\t\tMessage not hacked")
    return eq


def filter_interfere(eq, interference_threshold_time):
    threshold = interference_threshold_time
    event_time = eq[0]["time"]
    delete_idx = []

    # Interference can only happen if there is more than one message
    #   in the event queue
    if len(eq) > 1:
        for idx, e in enumerate(eq):
            logger.debug(
                f"\t\t\tComparing primary message to message from"
                f' {e["source"]} going to {e["dest"]}'
            )
            # Don't check for interference between the primary message
            #   (`event` = eq[0]) and itself.
            if idx > 0:
                dt = e["time"] - event_time
                logger.debug(f"\t\t\t\tTime delta between messages: {dt}")

                if dt < 0:
                    logger.warning(
                        f"\t\t\t\teq appears unordered:"
                        f'\n\t\t\t\teq[0]["time"] = {event_time}'
                        f'\n\t\t\t\teq[{idx}]["time"] = {e["time"]}'
                    )
                if dt < threshold:
                    logger.debug(
                        f"\t\t\t\t{dt} is less than interference "
                        f"threshold ({threshold}) and is "
                        f"interfering"
                    )
                    # If the list is empty, add the primary event as the
                    #   to the delete_list. That is, the primary message
                    #   and the next message in eq (eq[1]) are interfering
                    #   with each other.
                    if not delete_idx:
                        delete_idx.append(0)
                        logger.debug(
                            f"\t\t\t\tScheduling message for deletion: " f"eq[0]"
                        )
                    delete_idx.append(idx)
                    logger.debug(
                        f"\t\t\t\tScheduling message for deletion: " f"eq[{idx}]"
                    )
                else:
                    logger.debug(
                        f"\t\t\t\tTime delta of {dt} is greater than"
                        f" max interference time of"
                        f" {interference_threshold_time}."
                    )
                    break

        # Deleting events from the eq that are causing interference
        #   Work from the largest idx to the smallest so the index
        #   values we care about don't change as the events are removed
        #   from eq
        delete_idx.sort(reverse=True)
        for i in delete_idx:
            logger.debug(
                f"\t\t\tDeleting message from queue:"
                f'\t\t\t\tsource: {eq[i]["source"]}'
                f'\t\t\t\tdestination: {eq[i]["dest"]}'
                f'\t\t\t\tpayload: {eq[i]["payload"]}'
                f'\t\t\t\tdelivery time: {eq[i]["time"]}'
            )
            del eq[i]
            logger.debug(f"\t\t\teq length: {len(eq)}")
    return eq


def filter_message(eq, cmd, args):
    if cmd == "drop_delay":
        logger.debug(f"\t\tPerforming filter operation drop and delay")
        eq = filter_drop_delay(eq, args.drop_rate, args.delay_time)
    elif cmd == "hack":
        logger.debug(f"\t\tPerforming filter operation hack")
        eq = filter_hack(eq, args.hack_success_rate)
        pass
    elif cmd == "interfere":
        logger.debug(f"\t\tPerforming filter operation interfere")
        eq = filter_interfere(eq, args.interference_threshold_time)
        # pass
    else:
        logger.warning(f"Unrecognized command: {cmd}" f" event queue unmodified")
    return eq


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

    logger.info("Attempting to enter execution mode")
    h.helicsFederateEnterExecutingMode(fed)
    logger.info("Entered HELICS execution mode")

    hours = 24 * float(args.days)
    total_interval = int(60 * 60 * hours)

    starttime = h.HELICS_TIME_MAXTIME
    # starttime = 0
    logger.debug(f"Requesting initial time {starttime}")
    grantedtime = h.helicsFederateRequestTime(fed, starttime)
    logger.debug(f"Granted time {grantedtime}")

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
            time = h.helicsMessageGetTime(msg)
            logger.debug(
                f"\tReceived message from endpoint {source}"
                f" to endpoint {dest}"
                f" for delivery at time {time}"
                f' with payload "{msg_str}"'
            )
            msg_dict = {
                "msg_obj": msg,
                "payload": msg_str,
                "source": source,
                "dest": dest,
                "time": time,
            }
            # Adding messagge to end of eq as a reserved place for all
            # filters to act on.
            eq.append(msg_dict)
            eq = filter_message(eq, "drop_delay", args)
            if source == "Controller/ep":
                eq = filter_message(eq, "hack", args)

        # Sort event queue to get it back in order
        eq = sorted(eq, key=itemgetter("time"))

        # Acting on any events that need to be dequeued
        # Running interference filter. This filter has the ability to
        #   remove events from eq. We may not have any messages to send
        #   after interference runs. eq must be freshly sorted for this
        #   filter to work.
        if len(eq) > 0:
            eq = filter_message(eq, "interfere", args)

            # After filtering, send all messages whose time has come (or past;
            #   in which case something has gone wrong)
            while eq and eq[0]["time"] <= grantedtime:
                # Change destination to original destination before sending
                #   If you don't do this is sends the message back to the rerouted
                #   destination which, in this case, is the filter endpoint.
                h.helicsMessageSetDestination(eq[0]["msg_obj"], eq[0]["dest"])
                h.helicsEndpointSendMessage(endid, eq[0]["msg_obj"])
                logger.debug(
                    f"\tSent message from endpoint {end_name}"
                    f' appearing to come from {eq[0]["source"]}'
                    f' to endpoint {eq[0]["dest"]}'
                    f" at time {grantedtime}"
                    f' with payload "{eq[0]["payload"]}"'
                )
                del eq[0]

            if eq:
                # Event queue not empty, need to schedule filter federate to
                #   run again when its time to deliver the next message in the
                #   queue
                requested_time = eq[0]["time"]
            else:
                # Reachable if interference has removed all the messages
                #   from the event queue.
                # No events in queue, schedule run for end of simulation.
                #   Filter federate will be granted an earlier time if a
                #   message is rerouted to the filter federate.
                requested_time = h.HELICS_TIME_MAXTIME

        else:
            requested_time = h.HELICS_TIME_MAXTIME
        logger.debug(f"Requesting time {requested_time}\n")
        grantedtime = h.helicsFederateRequestTime(fed, requested_time)
        logger.debug(f"Granted time {grantedtime}")


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
    logger.debug(f"Intializing RNG with seed {args.random_seed}")
    fed, endid, end_name = configure_federate()
    run_cosim(fed, endid, end_name, args)
    fed.disconnect()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Demo HELICS filter federate")
    # Have to do a little bit of work to generate a good default
    # path for the auto_run folder (where the development test data is
    # held.
    script_path = os.path.dirname(os.path.realpath(__file__))
    auto_run_dir = os.path.join(script_path)
    parser.add_argument("-a", "--auto_run_dir", nargs="?", default=script_path)
    parser.add_argument("-r", "--random_seed", nargs="?", default=2609)
    parser.add_argument("-D", "--drop_rate", nargs="?", default=0.1)
    parser.add_argument("-t", "--delay_time", nargs="?", default=1800)
    parser.add_argument("-k", "--hack_success_rate", nargs="?", default=0.02)
    parser.add_argument("-i", "--interference_threshold_time", nargs="?", default=200)
    parser.add_argument("-d", "--days", nargs="?", default=1)
    args = parser.parse_args()
    _auto_run(args)
