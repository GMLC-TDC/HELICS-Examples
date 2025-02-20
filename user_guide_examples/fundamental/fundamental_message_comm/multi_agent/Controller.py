"""
Created on 8/27/2020

This is a simple EV charge controller federate that manages the charging at
a set of charging terminals in a hypothetical EV garage. It receives periodic
SOC messages from each EV (associated with a particular charging terminal)
and sends back a message indicating whether the EV should continue charging
or not (based on whether it is full).

@author: Allison M. Campbell
allison.m.campbell@pnnl.gov
"""

import argparse
import matplotlib.pyplot as plt
import helics as h
import logging
import numpy as np

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.DEBUG)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Demo HELICS Federate")
    parser.add_argument("-d", "--days", nargs="?", default=1)
    parser.add_argument("-p", "--show_plots", nargs="?", default=True)
    args = parser.parse_args()

    ##############  Registering  federate from json  ##########################
    fed = h.helicsCreateMessageFederateFromConfig("ControllerConfig.json")
    federate_name = h.helicsFederateGetName(fed)
    logger.info(f"Created federate {federate_name}")

    #### Register endpoint #####
    # Only one endpoint for the controller
    endid = h.helicsFederateGetEndpointByIndex(fed, 0)
    end_name = h.helicsEndpointGetName(endid)
    logger.info("Registered Endpoint ---> {}".format(end_name))

    ##############  Entering Execution Mode  ##################################
    h.helicsFederateEnterExecutingMode(fed)
    logger.info("Entered HELICS execution mode")

    hours = 24 * float(args.days)
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
    starttime = h.HELICS_TIME_MAXTIME
    logger.debug(f"Requesting initial time {starttime}")
    grantedtime = h.helicsFederateRequestTime(fed, starttime)
    logger.debug(f"Granted time {grantedtime}")

    time_sim = {}
    soc = {}

    while grantedtime < total_interval:

        # In HELICS, when multiple messages arrive at an endpoint they
        # queue up and are popped off one-by-one with the
        #   "helicsEndpointHasMessage" API call. When that API doesn't
        #   return a message, you've processed them all.
        while h.helicsEndpointHasMessage(endid):

            # Get the SOC from the EV/charging terminal in question
            msg = h.helicsEndpointGetMessage(endid)
            currentsoc = h.helicsMessageGetString(msg)
            source = h.helicsMessageGetOriginalSource(msg)
            logger.debug(
                f"\tReceived message from endpoint {source}"
                f" at time {grantedtime}"
                f" with SOC {currentsoc}"
            )

            # Send back charging command based on current SOC
            #   Our very basic protocol:
            #       If the SOC is less than soc_full keep charging (send "1")
            #       Otherwise, stop charging (send "0")
            soc_full = 0.95
            if float(currentsoc) <= soc_full:
                instructions = 1
            else:
                instructions = 0
            message = str(instructions)
            h.helicsEndpointSendBytesTo(endid, message.encode(), source)
            logger.debug(
                f"\tSent message to endpoint {source}"
                f" at time {grantedtime}"
                f" with payload {instructions}"
            )

            # Store SOC for later analysis/graphing
            if source not in soc:
                soc[source] = []
            soc[source].append(float(currentsoc))
            if source not in time_sim:
                time_sim[source] = []
            time_sim[source].append(grantedtime)

        # Since we've dealt with all the messages that are queued, there's
        #   nothing else for the federate to do until/unless another
        #   message comes in. Request a time very far into the future
        #   and take a break until/unless a new message arrives.
        logger.debug(f"Requesting time {h.HELICS_TIME_MAXTIME}")
        grantedtime = h.helicsFederateRequestTime(fed, h.HELICS_TIME_MAXTIME)
        logger.info(f"Granted time: {grantedtime}")

    # Close out co-simulation execution cleanly now that we're done.
    fed.disconnect()
    # Printing out final results graphs for comparison/diagnostic purposes.
    # xaxis = np.array(time_sim) / 3600
    x = []
    for key in time_sim:
        x.append(np.array(time_sim[key]) / 3600)
    y = []
    for key in soc:
        y.append(np.array(soc[key]))

    logger.debug(soc)
    fig, axs = plt.subplots(len(soc.keys()), sharex=True, sharey=True)
    fig.suptitle("SOC at each charging port")

    axs[0].plot(x[0], y[0], color="tab:blue", linestyle="-")
    axs[0].set_yticks(np.arange(0, 1.25, 0.5))
    axs[0].set(ylabel="Port 1")
    axs[0].grid(True)
    for i in range(1, len(soc.keys())):
        axs[i].plot(x[i], y[i], color="tab:blue", linestyle="-")
        axs[i].set(ylabel=f"Port {i+1}")
        axs[i].grid(True)
    plt.xlabel("time (hr)")
    # for ax in axs():
    #        ax.label_outer()
    # Saving graph to file
    plt.savefig("fundamental_combo_estimated_SOCs.png", format="png")
    if args.show_plots:
        plt.show()
