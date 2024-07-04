# -*- coding: utf-8 -*-
"""
Created on 4 July 2024

Simple model of a battery charging from a fixed source.

Co-simulation data exchange

                 
                  ---- charging current ---- >
Battery federate                                Charger federate 
                  <--- charging voltage -----

Install PyHELICS by
$ pip install helics

Test co-simulation by running
$ helics run --path=osmses_2024_runner.json

OR

$ python battery_cosim_complete.py & (or launch in its own shell)
$ python charger_cosim_complete.py & (or launch in its own shell)
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
    # The charging voltage is adjusted based on charging current
    # to regulate the charging current
    init_charging_voltage = 240
    charging_voltage = init_charging_voltage
    charging_voltage_max = 480
    charging_voltage_min = 24

    # Using a simple proportional controller to adjust the charging
    # voltage to regulate the current
    charging_voltage_adjust_k = 1

    charging_current_target = 5

    # Simulation time management variable
    hours = 24 * 7
    final_sim_time = int(60 * 60 * hours)
    sim_time_stepsize_s = None
    init_sim_time = 0
    requested_sim_time = init_sim_time
    granted_sim_time = 0

    # Data collection variables
    recorded_time = []
    recorded_charging_voltage = []
    recorded_charging_current = []


    # *****  HELICS setup  *****
    fed = h.helicsCreateValueFederateFromConfig("charger_config.json")
    fed_name =  h.helicsFederateGetName(fed)
    charging_current_sub = h.helicsFederateGetInputByIndex(fed, 0)
    charging_current_sub_name = h.helicsInputGetTarget(charging_current_sub)
    charging_voltage_pub = h.helicsFederateGetPublicationByIndex(fed, 0)
    charging_voltage_pub_name = h.helicsPublicationGetName(charging_voltage_pub)
    sim_time_stepsize_s = h.helicsFederateGetTimeProperty(fed, h.HELICS_PROPERTY_TIME_PERIOD)

    # *****  HELICS start co-simulation  *****
    h.helicsFederateEnterExecutingMode(fed)

    # As long as granted time is in the time range to be simulated, 
    # update the model
    while granted_sim_time < final_sim_time:
        # *****  Advance simulation time  *****
        requested_sim_time += sim_time_stepsize_s
        logger.debug(f"Requesting time: {requested_sim_time/3600}")
        granted_sim_time = fed.request_time(requested_sim_time)
        sim_time_hr = granted_sim_time / 3600  
        logger.debug(f"Granted sim time (hr): {sim_time_hr:.2f}")    

        # *****  Get latest inputs from rest of federation  *****
        charging_current = h.helicsInputGetDouble(charging_current_sub)

        # *****  Update internal model  *****
        # Simple propotional controller 
        charging_current_delta = charging_current_target - charging_current
        logger.debug(f"\tCharging current delta: {charging_current_delta :.2f}")
        charging_voltage = charging_voltage + (charging_current_delta * charging_voltage_adjust_k)
        # Coerce voltage into charger limits
        if charging_voltage > charging_voltage_max:
            charging_voltage = charging_voltage_max
        if charging_voltage < charging_voltage_min:
            charging_voltage = charging_voltage_min
        logger.debug(f"\tCharging voltage: {charging_voltage :.2f}")
        # Collect data for later analysis
        recorded_time.append(sim_time_hr)
        recorded_charging_voltage.append(charging_voltage)
        recorded_charging_current.append(charging_current)

        # *****  Publish out latest outputs to rest of federation  *****
        h.helicsPublicationPublishDouble(charging_voltage_pub, charging_voltage)

    # *****  HELICS end co-simulation  *****
    h.helicsFederateDisconnect(fed)
    h.helicsFederateDestroy(fed)

    # Printing out final results graphs
    fig, axs = plt.subplots(2, sharex=True)
    fig.suptitle("Charger Controller Data")

    axs[0].plot(recorded_time, recorded_charging_voltage, color="tab:blue", linestyle="-")
    axs[0].set_yticks(np.arange(0, 500, 50))
    axs[0].set(ylabel="Charging Voltage (V)")
    axs[0].grid(True)

    axs[1].plot(recorded_time, recorded_charging_current, color="tab:blue", linestyle="-")
    axs[1].set_yticks(np.arange(0, 30, 3))
    axs[1].set(ylabel="Charging Current (A)")
    axs[1].grid(True)

    plt.xlabel("Time (hr)")
    plt.show()