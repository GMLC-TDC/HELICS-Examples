# -*- coding: utf-8 -*-
"""
Created on 4 July 2024

Simple EV charge management demonstration where GridLAB-D models the EVs and
this Python script implements a simple charge management algorithm to 
regulate the total charging power in the power system.

This implements a silly charge management algorithm where the lower the 
SOC, the greater the charging power allowed.

Co-simulation data exchange diagram:

                     ---  vehicle_location -- >
                     ----  battery_SOC ------ >
GridLAB-D EV models                              Charge manager 
                     <-- maximum_charge_rate ---

GridLAB-D/evcharger_det/battery_SOC
GridLAB-D/evcharger_det/vehicle_location
ChargeManager/EV/maximum_charge_rate

Install PyHELICS by
$ pip install helics

Test co-simulation by running
$ helics run --path=gld_python_demo.json

OR

$ python EV_charge_manager.py & (or launch in its own shell)
$ gridlabd five_EV_chargers.glm& (or launch in its own shell)
$ helics_broker -f 2  (or launch in its own shell)

@author: Trevor Hardy
trevor.hardy@pnnl.gov
"""

import matplotlib.pyplot as plt
import helics as h
import logging
import numpy as np


logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.DEBUG)


if __name__ == "__main__":
    # *****  Model parameter definitions and data setup  *****
    # Maximum charging power per EV
    manage_charging = True
    start_time_hr = 7
    min_ev_charging_power = 3000
    max_ev_charging_power = 10000
    regulated_total_charging_power = 250000
    ev_charging_power_delta = max_ev_charging_power - min_ev_charging_power
    regulated_charging_power = {}

    # Simulation time management variable
    hours = 24
    final_sim_time = int(60 * 60 * hours)
    sim_time_stepsize_s = None
    init_sim_time = 0
    requested_sim_time = init_sim_time
    granted_sim_time = 0

    

    # *****  HELICS configuration  *****
    # Load in HELICS configuration from JSON 
    fed = h.helicsCreateValueFederateFromConfig("charge_manager_config.json")
    fed_name =  h.helicsFederateGetName(fed)
    sub_count = h.helicsFederateGetInputCount(fed)
    logger.debug(f"\tNumber of subscriptions: {sub_count}")
    pub_count = h.helicsFederateGetPublicationCount(fed)
    logger.debug(f"\tNumber of publications: {pub_count}")
    sim_time_stepsize_s = h.helicsFederateGetTimeProperty(fed, h.HELICS_PROPERTY_TIME_PERIOD)


    # Diagnostics to confirm JSON config correctly added the required
    #   publications and subscriptions
    subs = {}
    for i in range(0, sub_count):
        sub_obj = h.helicsFederateGetInputByIndex(fed, i)
        sub_name = h.helicsInputGetTarget(sub_obj)
        subs[i] = {"sub obj": sub_obj, "sub name": sub_name}
        logger.debug(f"\tRegistered subscription---> {sub_name} as sub index {i}")

    pubs = {}
    for i in range(0, pub_count):
        pub_obj = h.helicsFederateGetPublicationByIndex(fed, i)
        pub_name = h.helicsPublicationGetName(pub_obj)
        pubs[i] = {"pub obj": pub_obj, "pub name": pub_name}
        logger.debug(f"\tRegistered publication---> {pub_name} as pub index {i}")

    # *****  Data collection setup  *****
    # Each EV produces two subscriptions and one publication in the HELICS
    # configuration
    ev_count = pub_count
    logger.debug(f"ev_count: {ev_count}")

    recorded_charging_power = {}
    recorded_ev_SOCs= {}
    recorded_time = []
    ev_names = []
    # Setting up data collection dictionaries with the keys being the 
    # EV name
    for idx, sub in subs.items():
        sub_name_parts = sub["sub name"].split("/") #{fed name}/{ev name}/{property}
        ev_name = sub_name_parts[1]
        ev_names.append(ev_name)
        recorded_charging_power[ev_name] = []
        recorded_ev_SOCs[ev_name] = []

    recorded_total_charging_power = []
    average_ev_SOC_percent = []
    
    # *****  HELICS start co-simulation  *****
    fed.enter_executing_mode()

    # As long as granted time is in the time range to be simulated, 
    # update the model
    while granted_sim_time < final_sim_time:
         # ***** Advance simulation time *****
        requested_sim_time += sim_time_stepsize_s
        logger.debug(f"Requesting time: {requested_sim_time/3600}")
        granted_sim_time = fed.request_time(requested_sim_time)
        sim_time_hr = granted_sim_time / 3600  
        logger.debug(f"Granted sim time (hr): {sim_time_hr:.2f}")   
        recorded_time.append(sim_time_hr + start_time_hr)

        total_charging_power = 0
        average_ev_SOC = 0
        for i in range(0, pub_count): 
            ev_name = ev_names[i]
            # Get latest inputs from rest of federation 
            # SOC and corresponding vehicle location subs are separated by 
            # an index delta of sub_count
            logger.debug(f"\tsub index: {i} -> {subs[i]['sub name']}")
            soc_percent = h.helicsInputGetDouble(subs[i]["sub obj"])  
            average_ev_SOC += soc_percent 
            logger.debug(f"\t\treceived SOC of {soc_percent}")
            logger.debug(f"\tsub index: {i + ev_count} {subs[i + ev_count]['sub name']}")
            vehicle_location = h.helicsInputGetString(subs[i + ev_count]["sub obj"])  
            logger.debug(f"\t\treceived location of {vehicle_location}")

            
            
            # Manage charging power of each vehicle based on SOC
            # Set charging power inversely propotional to the SOC
            # Higher SOC -> lower charging power (down to min_charging_power)
            # Lower SOC -> higher charging power (up to max_charging_power)
            soc_factor = soc_percent/100
            recorded_ev_SOCs[ev_names[i]].append(soc_factor) 
            soc_remainder = 1 - soc_factor
            if soc_factor == 1:
                regulated_charging_power[i] = 0
            else:
                # Only worry about charging if the vehicle is at home
                if vehicle_location == "HOME":
                    if manage_charging:
                        regulated_charging_power[i] = (soc_remainder * ev_charging_power_delta) + min_ev_charging_power
                    else:
                        # Let every vehicle charge at our maximum charging power
                        regulated_charging_power[i] = max_ev_charging_power
                else: 
                    regulated_charging_power[i] = 0
            
            total_charging_power += regulated_charging_power[i]

        # Keep the total charging power below a defined limit.
        if manage_charging:
            logger.debug(f"\t\tPre-regulated total charging power: {total_charging_power}")
            if total_charging_power > regulated_total_charging_power:
                scaling_factor = regulated_total_charging_power/total_charging_power
                logger.debug(f"\t\tReducing charging power by factor of {scaling_factor} to stay under total charging limit of {regulated_total_charging_power}.") 
            else:
                scaling_factor = 1
                logger.debug(f"\t\tNo reduction in charging power needed to stay under total charging limit of {regulated_total_charging_power}.")
        else:
            logger.debug(f"\t\tNot managing total charging power; scaling_factor = 1.")
            scaling_factor = 1

        total_charging_power = 0
        for i in range(0, ev_count): 
            regulated_charging_power[i] = regulated_charging_power[i] * scaling_factor
            total_charging_power += regulated_charging_power[i]
            h.helicsPublicationPublishDouble(pubs[i]["pub obj"], regulated_charging_power[i])
            logger.debug(f"\t\t{pubs[i]['pub name']} sent charging power of {regulated_charging_power[i]}") 
            recorded_charging_power[ev_name].append(regulated_charging_power[i])
        logger.debug(f"\t\tPost-regulated total charging power: {total_charging_power}")      
        recorded_total_charging_power.append(total_charging_power)
        
        # Collect data on average SOC for use in post-processing
        average_ev_SOC_percent.append(average_ev_SOC/ev_count)
    
    # *****  HELICS end co-simulation  *****
    fed.disconnect()
    h.helicsFederateDestroy(fed)


   # Printing out final results graphs for comparison/diagnostic purposes.
    # Total charging power
    fig, axs = plt.subplots()
    axs.plot(recorded_time, recorded_total_charging_power)
    if manage_charging:
        axs.set_yticks(np.arange(0, regulated_total_charging_power/10, regulated_total_charging_power))
    else:
        axs.set_yticks(np.arange(0, ev_count*max_ev_charging_power/10, ev_count*max_ev_charging_power))
    axs.set_xlabel("Time (hrs)")
    axs.set_ylabel("Total Charging Power (W)")
    
    # Average EV SOC
    fig2, axs2 = plt.subplots()
    axs2.plot(recorded_time, average_ev_SOC_percent)
    axs2.set_yticks(np.arange(0, 100, 20))
    axs2.set_xlabel("Time (hrs)")
    axs2.set_ylabel("Average EV SOC (%)")
    
    plt.show()




