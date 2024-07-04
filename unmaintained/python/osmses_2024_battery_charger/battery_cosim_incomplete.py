# -*- coding: utf-8 -*-
"""
Created on 4 July 2024

Simple constant-current battery charger model

Co-simulation data exchange

                 
                  ---- charging current ---- >
Battery federate                                Charger federate 
                  <--- charging voltage -----


The following API calls need to be added to this script to enable it to 
participate in a HELICS-based co-simulation. API defintions at:
https://python.helics.org/api/capi-py/

            h.helicsCreateValueFederateFromConfig(<JSON configuration file name>)
(optional)  h.helicsFederateGetName(<name of federate object>)
            h.helicsFederateGetInputByIndex(<name of federate object>, 0)
(optional)  h.helicsInputGetTarget(<name of input object>)
            h.helicsFederateGetPublicationByIndex(<name of federate object>, 0)
(optional)  h.helicsPublicationGetName(<name of pub object>)
            h.helicsFederateEnterExecutingMode(<name of federate object>)
            h.helicsFederateGetTimeProperty(<name of federate object>, h.HELICS_PROPERTY_TIME_PERIOD)
            h.helicsFederateRequestTime(<name of federate object>, <time to request>)
            h.helicsInputGetDouble(<name of input object>)
            h.helicsPublicationPublishDouble(<name of pub object>, <value to publish>)
            h.helicsFederateDisconnect(<name of federate object>)
            h.helicsFederateDestroy(<name of federate object>)

            
Other edits may need to be made to the code to transition the code from
working solo to working in a co-simulation.

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
    # Battery size and initial SOC
    battery_size_kWh = 100
    init_soc = 0.1
    soc = init_soc

    # This models the reduced charging current as the SOC of the battery
    # increases.
    # 8 ohms (SOC = 0.0) to 150 ohms (SOC = 1.0)
    R_range= np.array([8, 150])
    soc_range = np.array([0, 1])

    # The charging voltage is fixed when running solo.
    charging_voltage = 240

    # Simulation time management variable
    hours = 24 * 7
    final_sim_time = int(60 * 60 * hours)
    sim_time_stepsize_s = 60
    init_sim_time = 0
    sim_time =  init_sim_time

    # Data collection variables
    recorded_time = []
    recorded_soc = []
    recorded_charging_current = []

    # *****  HELICS setup  *****

    # ******  HELICS start co-simulation  *****

    # As long as granted time is in the time range to be simulated, 
    # update the model
    while sim_time < final_sim_time:  

        # *****  Advance simulation time  *****
        sim_time += sim_time_stepsize_s
        sim_time_hr = sim_time / 3600 
        logger.debug(f"Sim time (hr): {sim_time_hr:.2f}")  

        # *****  Get latest inputs from rest of federation *****

        # *****  Update internal model  *****
        # R is modeled as a function of SOC. Calculate the effective charging
        # R as a linear interpolation of the 
        charging_R = np.interp(soc, soc_range, R_range)
        logger.debug(f"\tCharging R (ohms): {charging_R:.2f}")
        # If battery is full assume its stops charging on its own
        #  and the charging current goes to zero.
        if soc >= 1:
            charging_current = 0
        else:
            charging_current = charging_voltage / charging_R
        logger.debug(f"\tCharging current (A): {charging_current:.2f}")
        added_energy_kWh = (charging_current * charging_voltage * (sim_time_stepsize_s / 3600)) / 1000
        logger.debug(f"\tAdded energy (kWh): {added_energy_kWh:.4f}")
        soc = soc + added_energy_kWh / battery_size_kWh
        logger.debug(f"\tSOC: {soc:.4f}")
        # Collect data for later analysis
        recorded_time.append(sim_time_hr)
        recorded_soc.append(soc)
        recorded_charging_current.append(charging_current)

        # *****  Publish out latest outputs to rest of federation  *****


    # *****  HELICS end co-simulation  *****

    # Printing out final results graphs
    fig, axs = plt.subplots(2, sharex=True)
    fig.suptitle("Battery Charging Performance")

    axs[0].plot(recorded_time, recorded_soc, color="tab:blue", linestyle="-")
    axs[0].set_yticks(np.arange(0, 1.2, 0.2))
    axs[0].set(ylabel="SOC")
    axs[0].grid(True)

    axs[1].plot(recorded_time, recorded_charging_current, color="tab:blue", linestyle="-")
    axs[1].set_yticks(np.arange(0, 30, 3))
    axs[1].set(ylabel="Charging Current (A)")
    axs[1].grid(True)

    plt.xlabel("Time (hr)")
    plt.show()
