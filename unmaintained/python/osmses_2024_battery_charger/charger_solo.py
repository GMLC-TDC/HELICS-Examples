# -*- coding: utf-8 -*-
"""
Created on 4 July 2024

Simple constant-current battery charger model



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

    charging_current_target = 12


    # Modeling battery charging current as decreasing in time
    init_battery_R = 10
    battery_R = init_battery_R

    # Simulation time management variable
    hours = 24 * 7
    final_sim_time = int(60 * 60 * hours)
    sim_time_stepsize_s = 60
    init_sim_time = 0
    sim_time =  init_sim_time

    # Data collection variables
    recorded_time = []
    recorded_charging_voltage = []
    recorded_charging_current = []


    # As long as granted time is in the time range to be simulated, 
    # update the model
    while sim_time < final_sim_time:
        # Advance simulation time
        sim_time += sim_time_stepsize_s
        sim_time_hr = sim_time / 3600          
        logger.debug(f"Sim time (hr): {sim_time_hr:.2f}")  

        # Model battery charging current
        charging_current = charging_voltage / battery_R
        battery_R = battery_R * 1.0001

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

    
    # Printing out final results graphs
    fig, axs = plt.subplots(2, sharex=True)
    fig.suptitle("Battery Charging Performance")

    axs[0].plot(recorded_time, recorded_charging_voltage, color="tab:blue", linestyle="-")
    axs[0].set_yticks(np.arange(0, 330, 30))
    axs[0].set(ylabel="Charging Voltage (V)")
    axs[0].grid(True)

    axs[1].plot(recorded_time, recorded_charging_current, color="tab:blue", linestyle="-")
    axs[1].set_yticks(np.arange(0, 30, 3))
    axs[1].set(ylabel="Charging Current (A)")
    axs[1].grid(True)

    plt.xlabel("Time (hr)")
    plt.show()
