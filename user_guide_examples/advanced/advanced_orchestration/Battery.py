# -*- coding: utf-8 -*-
"""
Created on 5/27/2020

@author: bearcub
"""

import helics as h
import random
import string
import time
from datetime import datetime, timedelta
import json
import logging
import numpy as np
import sys
import argparse
import matplotlib.pyplot as plt
import pandas as pd
plt.style.use('ggplot')

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
    h.helicsFederateFree(fed)
    h.helicsCloseLibrary()
    logger.info('Federate finalized')

def tsplot(x, y, n=20, percentile_min=1, percentile_max=99, color='r', plot_mean=True, plot_median=False, line_color='k', **kwargs):
    # calculate the lower and upper percentile groups, skipping 50 percentile
    perc1 = np.percentile(y, np.linspace(percentile_min, 50, num=n, endpoint=False), axis=0)
    perc2 = np.percentile(y, np.linspace(50, percentile_max, num=n+1)[1:], axis=0)

    if 'alpha' in kwargs:
        alpha = kwargs.pop('alpha')
    else:
        alpha = 1/n
    # fill lower and upper percentile groups
    for p1, p2 in zip(perc1, perc2):
        plt.fill_between(x, p1, p2, alpha=alpha, color=color, edgecolor=None)


    if plot_mean:
        plt.plot(x, np.mean(y, axis=0), color=line_color)


    if plot_median:
        plt.plot(x, np.median(y, axis=0), color=line_color)

    return plt.gca()


def create_message_federate(fedinitstring,name,period,offset):
    fedinfo = h.helicsCreateFederateInfo()
    h.helicsFederateInfoSetCoreTypeFromString(fedinfo, "tcpss")
    h.helicsFederateInfoSetCoreInitString(fedinfo, fedinitstring)
    # Set one second message interval
    h.helicsFederateInfoSetTimeProperty(fedinfo, h.helics_property_time_period, period)
    # set wait for current time update to true
    h.helicsFederateInfoSetTimeProperty(fedinfo,h.helics_property_time_offset, offset)
    h.helicsFederateInfoSetFlagOption(fedinfo, h.helics_flag_uninterruptible, False)
    h.helicsFederateInfoSetIntegerProperty(fedinfo, h.helics_property_int_log_level, 1)
    # "terminate_on_error": true,
    h.helicsFederateInfoSetFlagOption(fedinfo, 72, True)
    h.helicsFederateInfoSetFlagOption(fedinfo, h.helics_flag_wait_for_current_time_update, True)
    fed = h.helicsCreateMessageFederate(name, fedinfo)
    print("Message federate created")
    return fed


def get_new_EV(numEVs):
    '''
    A distribution of EVs with support
    for specific charging levels are generated. The number of EVs
    generated is defined by the user.

    :param numEVs: Number of EVs
    :return
        numLvL1: Number of new EVs that will charge at level 1
        numLvL2: Number of new EVs that will charge at level 2
        numLvL3: Number of new EVs that will charge at level 3
        listOfEVs: List of all EVs (and their charging levels) generated

    '''
    lvl1 = np.random.poisson(np.random.normal(30,np.random.uniform(1,3)),1)
    lvl2 = np.random.poisson(np.random.normal(50,np.random.uniform(1,2)),1)
    lvl3 = np.random.poisson(np.random.normal(20,np.random.uniform(.05,.25)),1)
    total = lvl1+lvl2+lvl3
    #print(lvl1,lvl2,lvl3,total)
    p1,p2,p3 = lvl1/total,lvl2/total,lvl3/total
    #print(p1,p2,p3)
    listOfEVs = np.random.choice([1,2,3],numEVs,p=[p1[0],p2[0],p3[0]]).tolist()
    numLvl1 = listOfEVs.count(1)
    numLvl2 = listOfEVs.count(2)
    numLvl3 = listOfEVs.count(3)

    return numLvl1,numLvl2,numLvl3,listOfEVs


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='EV simulator')
    parser.add_argument('--seed', type=int, default=867530,
                    help='The seed that will be used for our random distribution')
    parser.add_argument('--port', type=int, default=-1,
                    help='port of the HELICS broker')
    parser.add_argument('--numEVs', type=int, default=1,
                    help='number of EVs in the federation')
    parser.add_argument('--hours', type=int, default=1,
                    help='duration of co-sim in hours')
    parser.add_argument('--plot', type=int, default=0,
                    help='plot or not')
    parser.add_argument('--outdir', type=str, default='.',
                    help='directory for results')

    args = parser.parse_args()
    np.random.seed(args.seed)
    print('outdir: ',args.outdir)
    if args.port != -1:
        fedinitstring="--brokerport="+str(args.port)
    else:
        fedinitstring=""

    print("Federate Init String = {}".format(fedinitstring))
    print("Random seed = {}".format(str(args.seed)))



    name = 'Battery'
    period = 60.0  # 15 min  # this is the default time step for the EV federate
    offset = 10.0
    fed = create_message_federate(fedinitstring,name,period,offset)

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


        dest_name = f'Charger/EV{EV}.soc'
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

#
######################   Entering Execution Mode  ##########################################################

    h.helicsFederateEnterExecutingMode(fed)


    # we will explore the question: what is the distribution of instantaneous power draw,
    # given unrestricted access by 10 vehicles.
    # in each iteration, we will draw from a distribution of lvl1, lvl2, lvl3 chargers
    # placing a gaussian over each.
    # eg: out of 100 EVs, ~ 60 will be lvl2, 10 will be lvl3, 30 will be lvl1
    # But this is the expectation of each.
    # We can assign stddev to each of these.
    # lvl2 ~ norm(60,unif(0,5))  -- assumes that most of lvl2 EVs are around 60% of population
    # lvl1 ~ norm(30,unif(0,10)) -- assumes that there is a large amount of spread in # of lvl1 EVs
    # lvl3 ~ norm(10,unif(0,1)) -- assumes not many lvl3 EVs, with small spread
    # in each iteration, the number of EVs connected to the Charger may not addup to 100
    # that's ok -- we're just calculating the prior predictive check of the
    # power draw from a distribution of EVs

    # when the simulation starts, draw numEVs samples from this joint distribution
    # the simulation starts in a snapshot of existing power discharge to the vehicles
    # i.e., each vehicle is at a random soc, and is connected to the EV Charger.
    # if an EV reaches >95% SOC, it is disconnected, and the EV Charger
    # selects a new EV from the joint distribution
    # each vehicle will have its own characteristics:
    # lvl1 = leaf, 120V
    # lvl2 = leaf, 240V
    # lvl3 = leaf, 480V
    # assumes 15amp outlet, same battery size
    charge_rate = [1.8,7.2,50]
    # [120V*15A, 240V*30A, 50kW DC charging]
    batt_size = 62 # leaf capacity is 62 kWh
    hours = args.hours # one week
    total_interval = int(60 * 60 * hours)
    update_interval = int(h.helicsFederateGetTimeProperty(
                                fed,
                                h.helics_property_time_period))
    update_offset = int(h.helicsFederateGetTimeProperty(
                                fed,
                                h.helics_property_time_offset))
    grantedtime = -1

    numLvl1,numLvl2,numLvl3,EVlist = get_new_EV(end_count)

    time_sim = []
    power_raw = []
    soc = []
    # get N values for soc, where N = end_count, and soc
    # is a random float between 0 and 1
    currentsoc = np.random.rand(end_count)
    currentpower = np.zeros(end_count)

    # Initial SOC message sent to Charger
    grantedtime = h.helicsFederateRequestTime(fed,0)
    for j in range(0,end_count):
        end_name = str(h.helicsEndpointGetName(end_EVsoc[j]))
        destination_name = str(h.helicsEndpointGetDefaultDestination(end_EVsoc[j]))
        h.helicsEndpointSendBytesTo(end_EVsoc[j], str(currentsoc[j]), "") #
    time_sim = []
    power = []

    while grantedtime < total_interval:

        # Time request for the next interval to be simulated
        requested_time = (grantedtime+update_interval+update_offset)
        logger.debug(f'Requesting time {requested_time}')
        grantedtime = h.helicsFederateRequestTime(fed, requested_time)
        logger.debug(f'Granted time {grantedtime}')


        for j in range(0,end_count):
            logger.debug(f'Battery {j+1} time {grantedtime}')
            endpoint_name = h.helicsEndpointGetName(end_EVsoc[j])

            # 1. Receive instructions
            if h.helicsEndpointHasMessage(end_EVsoc[j]):
                msg = h.helicsEndpointGetMessage(end_EVsoc[j])
                instructions = h.helicsMessageGetString(msg)
            # 2. Change SOC based on instructions
                if int(instructions) == 1:
                    logger.debug(f'\tStart SOC: {currentsoc[j]:.4f}')
                    currentpower[j] = charge_rate[(EVlist[j]-1)]
                    addenergy = currentpower[j]*((update_interval+update_offset)/3600)   #time_since_last_msg[j]
                    currentsoc[j] = currentsoc[j] + addenergy/batt_size
                    logger.debug(f'\tEnd SOC: {currentsoc[j]:.4f}')
                    logger.debug(f'\tAdded energy (kWh): {addenergy:.4f}')

                else:
                    _,_,_,newEVtype = get_new_EV(1)
                    EVlist[j] = newEVtype[0]
                    currentsoc[j] = np.random.uniform(.05,.5)
                    logger.debug(f'\tSOC: {currentsoc[j]:.4f}')

            else:
                logger.debug(f'\tNo messages at endpoint {endpoint_name} '
                             f'recieved at '
                             f'time {grantedtime}')

            # 3. Send SOC
            # send charging current message
            # to this endpoint's default destination, ""
            destination_name = str(h.helicsEndpointGetDefaultDestination(end_EVsoc[j]))
            h.helicsEndpointSendBytesTo(end_EVsoc[j], str(currentsoc[j]), "") #
            logger.debug(f'Sent SOC message {currentsoc[j]:.2f}'
                         f' from endpoint {endpoint_name}'
                         f' at time {grantedtime}')

            # Store SOC for later analysis/graphing
            # if end_EVsoc[j] not in soc:
            #     soc[end_EVsoc[j]] = []
            # soc[end_EVsoc[j]].append(float(currentsoc[j]))

            # if end_EVsoc[j] not in power_draw:
            #     power_draw[end_EVsoc[j]] = []
            # power_draw[end_EVsoc[j]].append(float(currentpower[j]))
            # # Data collection vectors

        power_raw.append(currentpower.copy())
        logger.debug(f'\tTHE STATE OF CHARGE IS: {currentsoc}')
        soc.append(currentsoc.copy())
        #logger.debug(f'\tTHE STATE OF CHARGE LIST IS: {soc}')

        total_power = 0
        for j in range(0, end_count):
            if currentsoc[j] > 0: # EV is still charging
                total_power += currentpower[j]



        # Data collection vectors
        time_sim.append(grantedtime)
        power.append(total_power)
        #power_raw.append(currentpower)

    # Cleaning up HELICS stuff once we've finished the co-simulation.
    destroy_federate(fed)
    # Printing out final results graphs for comparison/diagnostic purposes.
    xaxis = np.array(time_sim)/3600
#    y = []
#    for key in soc:
#        y.append(np.array(soc[key]))
    logger.debug('shape of power series is: ',np.array(power_raw).T.shape)
    logger.debug('shape of time series is: ',np.array(time_sim).shape)



    if args.plot == 1:

        xaxis = np.array(time_sim)/3600
        yaxis = np.array(power)
        plt.figure()
        plt.plot(xaxis, yaxis, color='tab:blue', linestyle='-')
        plt.yticks(np.arange(0,100,10))
        plt.ylabel('kW')
        plt.grid(True)
        plt.xlabel('time (hr)')
        plt.title('Instantaneous Power Draw from 5 EVs')
        plt.savefig('advanced_orchestration_charger_power.png', format='png')

        plt.show()

        t = (np.array(time_sim)/3600)
        y = np.array(power_raw).T
        tsplot(t, y, n=100, percentile_min=2.5, percentile_max=97.5, plot_median=True, plot_mean=False, color='g', line_color='navy')

        plt.plot()
        plt.show()
        t = pd.DataFrame({'Hour':(np.array(time_sim)/3600).T})
        vals = pd.DataFrame(np.array(power_raw))
        all_power = t.join(vals)
        all_power.to_csv(args.outdir+'/power_at_all_evs_'+str(args.seed)+'.csv',index=False)

        vals = pd.DataFrame(np.array(soc))
        all_soc = t.join(vals)
        all_soc.to_csv(args.outdir+'/soc_at_all_evs_'+str(args.seed)+'.csv',index=False)

        vals = pd.DataFrame(np.array(power))
        all_peak_power = t.join(vals)
        all_peak_power.to_csv(args.outdir+'/peak_power_at_all_evs_'+str(args.seed)+'.csv',index=False)


    else:
        t = pd.DataFrame({'Hour':(np.array(time_sim)/3600).T})
        vals = pd.DataFrame(np.array(power_raw))
        all_power = t.join(vals)
        all_power.to_csv(args.outdir+'/power_at_all_evs_'+str(args.seed)+'.csv',index=False)

        vals = pd.DataFrame(np.array(soc))
        all_soc = t.join(vals)
        all_soc.to_csv(args.outdir+'/soc_at_all_evs_'+str(args.seed)+'.csv',index=False)

        vals = pd.DataFrame(np.array(power))
        all_peak_power = t.join(vals)
        all_peak_power.rename(columns={0: "sample_"+str(args.seed)},inplace=True)
        all_peak_power.to_csv(args.outdir+'/peak_power_at_all_evs_'+str(args.seed)+'.csv',index=False)

        print('no plots generated')
