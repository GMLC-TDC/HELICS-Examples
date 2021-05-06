# -*- coding: utf-8 -*-
"""
Created on 5/3/2021

Test federate for evaluating performance of HELICS filter timing.

This code includes data collection and graphing functionality that displays the 
histogram of the transit times of HELICS messages to and from the echo federate 
and can include processing by the filter federate if included in the federation. 
Data is saved between test case runs as iPhone Pickel files and read back in if 
both files are present to allow comparison of the with and without filter 
federate runs. The user must manually set the test case variable to define
whether the filter federate is a part of the federation or not.

@author: Trevor Hardy
trevor.hardy@pnnl.gov
"""

import helics as h
import logging
from datetime import datetime as dt
from datetime import timedelta
import numpy as np
import matplotlib.pyplot as plt
import pickle
import os.path

# 0 = without filter
# 1 = with filter
test_case = 0

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.INFO)

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


def send_message(endid, dest):
    msg_str = dt.now().strftime('%Y-%m-%d %H:%M:%S.%f')
    h.helicsEndpointSendBytesTo(endid, msg_str.encode(), dest)

def save_and_load(ts_data, case_idx):
    filenames = ['results_without_filter.pickle', 'results_with_filter.pickle']

    #saving results from this run
    pickle.dump(ts_data, open(filenames[case_idx], 'wb'))    
    
    # Loading data for plotting
    if os.path.exists(filenames[0]):
        results_without_filter = pickle.load(open(filenames[0], 'rb'))
    else:
        results_without_filter = 0
    if os.path.exists(filenames[1]):
        results_with_filter = pickle.load(open(filenames[1], 'rb'))
    else:
        results_with_filter = 0
        
    if results_with_filter and results_without_filter:
        logger.debug('Both datasets present')
        all_data = [results_with_filter, results_without_filter]
    elif results_with_filter:
        logger.debug('results_with_filter only') 
        all_data = results_with_filter
    elif results_without_filter:
        logger.debug('results_without_filter only') 
        all_data = results_without_filter
        
    #logger.debug(f'all_data shape = {all_data.shape}')
    return all_data
    

def calc_times(ts_data):
    times = np.array([])
    for item in ts_data:
        send_dt = dt.strptime(item['send'], '%Y-%m-%d %H:%M:%S.%f')
        send_us = send_dt.timestamp() * 1000
        receive_dt = dt.strptime(item['receive'], '%Y-%m-%d %H:%M:%S.%f')
        receive_us = receive_dt.timestamp() * 1000
        transit_us = receive_us - send_us
        #logger.debug(f'{transit_us}')
        times = np.append(times, transit_us)
        #logger.debug(len(times))

    return times
    
if __name__ == "__main__":

    ts_data = []

    ##############  Registering  federate from json  ##########################
    fed = h.helicsCreateCombinationFederateFromConfig("source_sink_config.json")
    federate_name = h.helicsFederateGetName(fed)
    endid = h.helicsFederateGetEndpointByIndex(fed, 0)


    ##############  Entering Execution Mode  ##################################
    h.helicsFederateEnterExecutingMode(fed)
    logger.info('Entered HELICS execution mode')

    hours = 1
    total_interval = int(60 * 60 * hours)
    update_interval = int(h.helicsFederateGetTimeProperty(
                            fed,
                            h.HELICS_PROPERTY_TIME_PERIOD))
    grantedtime = 0


    default_dest = h.helicsEndpointGetDefaultDestination(endid)

    # Blocking call for a time request at simulation time 0
    initial_time = 0
    logger.debug(f'Requesting initial time {initial_time}')
    grantedtime = h.helicsFederateRequestTime(fed, initial_time)
    logger.debug(f'Granted time {grantedtime}')


    # Send initial message
    send_message(endid, default_dest)


    ########## Main co-simulation loop ########################################
    # As long as granted time is in the time range to be simulated...
    while grantedtime < total_interval:

        # Time request for the next physical interval to be simulated
        requested_time = (grantedtime + update_interval)
        logger.debug(f'Requesting time {requested_time}\n')
        grantedtime = h.helicsFederateRequestTime (fed, requested_time)
        logger.debug(f'Granted time {grantedtime}')
        
        if grantedtime % 10 == 0:
            send_message(endid, default_dest)
            logger.debug(f'Sending message at time {grantedtime}')

        if h.helicsEndpointHasMessage(endid):
            msg = h.helicsEndpointGetMessage(endid)
            send_ts_str = h.helicsMessageGetString(msg)
            receive_ts_str = dt.now().strftime('%Y-%m-%d %H:%M:%S.%f')
            ts_data.append({"send": send_ts_str, "receive":receive_ts_str})




    # Cleaning up HELICS stuff once we've finished the co-simulation.
    destroy_federate(fed)
    
    
    # Post-processing data
    ts_data = save_and_load(ts_data, test_case)
    
    logger.debug(f'ts_data_length: {len(ts_data)}')
    if len(ts_data) == 2:
        times_0 = calc_times(ts_data[0])
        times_1 = calc_times(ts_data[1])
        times = np.stack((times_0, times_1), 1)
    else:
        times = calc_times(ts_data)

    

    _ = plt.hist(times, bins = 'auto')
    plt.show()
