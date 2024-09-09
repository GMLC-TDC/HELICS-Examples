# -*- coding: utf-8 -*-
"""
Created on 3/3/2022

These are the functions common to both (all) federates, which are necessary to achieve
iteration.
The are grouped here for readability, reproduceability and to ensure uniform alteration.
"""
import helics as h
import matplotlib.pyplot as plt
class FedItr:
    def __init__(self, logger):
        self.logger = logger

    def check_error(self, dState):
        return sum([abs(vals[0] - vals[1]) for vals in dState.values()])

    def request_time(self, fed, requested_time, itr, itr_flag, iterative_mode=True):
        if itr == 0:
            s = "=====================\n"
        else:
            s = "---------------------\n"
        if not iterative_mode:
            grantedtime = h.helicsFederateRequestTime(fed, requested_time)
            self.logger.debug(f"{s}Requested time {requested_time} - Granted time {grantedtime}")
            return grantedtime, h.helics_iteration_result_next_step
        else:
            grantedtime, itr_state = h.helicsFederateRequestTimeIterative(fed,requested_time,itr_flag)
            self.logger.debug(f"{s}Requested time: {requested_time} - Granted time: {grantedtime} - itr: {itr} - itr request: {ireq(itr_flag)} - itr status: {ires(itr_state)}")
            return grantedtime, itr_state

    def set_pub(self, fed, pubid, pubvals, nametyp=None, init=False):
        if init:
            self.logger.info("=== Entering HELICS Initialization mode")
            h.helicsFederateEnterInitializingMode(fed)
        else:
            self.logger.debug(f"\tPublications: (helics mode: {fedstate(h.helicsFederateGetState(fed))})")
        pub_count = h.helicsFederateGetPublicationCount(fed)
        for j in range(0, pub_count):
            h.helicsPublicationPublishDouble(pubid[j], pubvals[j])
            if init:
                self.logger.debug(f"\t{nametyp} {j+1} published {h.helicsPublicationGetName(pubid[j])} with value " 
                    "{:.2f}".format(pubvals[j]))
            else:
                self.logger.debug(f"\t\tPublished {h.helicsPublicationGetName(pubid[j])} with value " 
                    "{:.2f}".format(pubvals[j]))

    def get_sub(self, fed, subid, itr, valarray, valinit, nametyp, proptyp):
        self.logger.debug("\tSubscriptsion:")
        sub_count = h.helicsFederateGetInputCount(fed)
        for j in range(0, sub_count):
            x = h.helicsInputGetDouble((subid[j]))
            self.logger.debug(f"\t\t{nametyp} {j+1} received {proptyp} {x:.2f}" 
                        f" from input {h.helicsSubscriptionGetTarget(subid[j])}")
            if itr == 0:
                valarray[j] = [valinit] * 2
            else:
                valarray[j].insert(0, valarray[j].pop())
            valarray[j][0] = x
            self.logger.debug(f"\t\t\t{proptyp} array={valarray[j]}")


def ires(n):
    if n == 0:
        return "NEXT_STEP"
    elif n == 1:
        return "ITR_ERROR"
    elif n == 2:
        return "HALTED"
    elif n == 3:
        return "ITERATING"
    else:
        return n

def ireq(n):
    if n == 0:
        return "NO_ITERATION"
    elif n == 1:
        return "FORCE_ITERATION"
    elif n == 2:
        return "ITERATE_IF_NEEDED"
    else:
        return n

def fedstate(n):
    return {0: "STARTUP",
    1: "INITIALIZATION",
    2: "EXECUTION",
    3: "FINALIZE",
    4: "ERROR",
    5: "PENDING_INIT",
    6: "PENDING_EXEC",
    7: "PENDING_TIME",
    8: "PENDING_ITERATIVE_TIME",
    9: "PENDING_FINALIZE",
    10: "FINISHED"}[n]

def state_plot(d, savename, xlabel="", ykey="", title=""):
    fig, axs = plt.subplots(len(d), sharex=True, sharey=False)
    fig.suptitle(title)
    for k, v in d.items():
        axs[k].plot(range(len(v)), v, color="tab:blue", linestyle="-")
        axs[k].set(ylabel=f"{ykey} {k+1}")
        axs[k].grid(True)
    
    plt.xlabel(xlabel)

    plt.savefig(savename, format="png")
    plt.close()