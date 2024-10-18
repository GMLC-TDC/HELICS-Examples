"""
Created on 10/17/2024

This federate was created to be a generic federate for use in validating 
a timing diagram created for explanatory purposes. The instantiation of
this simulator (that does nothing but sleep and send data) in a federation
creates and logs the data necessary to create a real-world timing 
diagram and validate the one created by reasoning about the HELICS timing
algorithm. Thus it also serves as a demonstration of how said algorithm 
works.

The timing of the federation is configured through the "timing.json" file
that is expected to be in the same folder as this file. The topology of the
federation is hard-coded at this time.

@author: Trevor Hardy
trevor.hardy@pnnl.gov
"""

import matplotlib.pyplot as plt
import helics as h
import logging
import numpy as np
import argparse
import time
import json


logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.DEBUG)

def _open_file(file_path: str, type='r'):
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
    # Adding extra time request to clear out any pending messages to avoid
    #   annoying errors in the broker log. Any message are tacitly disregarded.

    granted_time = h.helicsFederateRequestTime(fed, 1000000)
    status = h.helicsFederateDisconnect(fed)
    h.helicsFederateFree(fed)
    h.helicsCloseLibrary()
    logger.info('Federate finalized')



if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    parser = argparse.ArgumentParser(description="")
    parser.add_argument('-f', '--fednum',
                        help="identifies which federate this is by a numeric value",
                        required = True,
                        type = int
                        )
    parser.add_argument('-m', '--max_time',
                        help="maximum time to run the co-simulation",
                        nargs='?',
                        default = 30)
    parser.add_argument('-c', '--config',
                        nargs='?',
                        help="configuration file for timing federation",
                        default = "timing_fed_config.json")
    args = parser.parse_args()
    fednum = args.fednum
    parser.add_argument('-o', '--output_file',
                        nargs='?',
                        help="output timing log file name",
                        default = f"timing_log_{fednum}.json")
    args = parser.parse_args()

    # Loading in configuration information from a custom-formatted JSON
    fh = _open_file(args.config)
    config = json.load(fh)
    fh.close()

    # Configure federate per config JSON
    
    period = config[str(fednum)]["period"]
    fed_name = f"fed{fednum}"
    logger.debug(f"Federate name: {fed_name}")
    fedinitstring = "--federates=1"
    fedinfo = h.helicsCreateFederateInfo()
    h.helicsFederateInfoSetCoreInitString(fedinfo, fedinitstring)
    h.helicsFederateInfoSetTimeProperty(fedinfo, h.helics_property_time_period, period)
    fed = h.helicsCreateValueFederate(fed_name, fedinfo)

    # Federates only need one dummy publication for this example
    pub = fed.register_global_publication(f"fed{fednum}pub", h.HELICS_DATA_TYPE_INT)
    
    # Subscriptions are defined in the timing config JSON
    for sub_name in config[str(fednum)]["subs"]:
        fed.register_subscription(sub_name)

    # Set up timing logging
    timing_log = []
    
    
    # Begin co-simulation
    # Entering executing mode is equivalent to being granted t = 0 and is 
    # a blocking call until all the federates have requested entering it.
    fed.enter_executing_mode()
    reference_time = time.monotonic()
    grant_time = 0
    grant_wall_clock_time = 0
    while grant_time < args.max_time:
        # Generate publications, particularly for any feds that are requesting
        # large times and need the publication to wake them up earlier.        
        pub.publish(grant_time)

        # Dummy execution time as specified in the timing config file
        sleep_time = config[str(fednum)]["execution time"][str(int(grant_time))]
        logger.debug(f"Sleeping for {sleep_time} seconds")
        time.sleep(sleep_time)
        
        if config[str(fednum)]["max time request"]:
            request_time = 100000
        else:
            request_time = grant_time + period
        request_wall_clock_time = time.monotonic() - reference_time
        timing_log.append({"grant time": grant_time, 
                        "grant wall clock time": grant_wall_clock_time,
                        "request time": request_time,
                        "request wall clock time": request_wall_clock_time})
        grant_time = fed.request_time(timing_log[-1]["request time"])
        grant_wall_clock_time = time.monotonic() - reference_time

    # Cleaning up HELICS stuff once we've finished the co-simulation.
    destroy_federate(fed)
    fh = _open_file(args.output_file, "w")
    json.dump(timing_log, fh, indent=4)
    fh.close()