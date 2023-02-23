import scipy.optimize as optimize
import matplotlib.pyplot as plt
import multiprocessing
import pandas as pd
import helics as h
import numpy as np
import math
import time

class Helper:

    def __init__(self, broker_ip, broker_port, publications, duration_sec, timestep_sec, maxitrs,  method=1):

        self.methods = {
            0: self.no_algorithm,
            1: self.gradient_descent,
            2: self.heavy_ball,
            3: self.newton_raphson,
        }
        self.method = self.methods[method]
        self.publication_list = list(set(publications))
        self.duration_sec = duration_sec
        self.timestep_sec = timestep_sec
        self.maxitrs = maxitrs

    def run(self):
        vfed, pub_list, sub_list = self.helics_federate_boilerplate("helper_federate")
        for t in np.arange(0,  self.duration_sec, self.timestep_sec):
            # for p in pub_list:
            #     h.helicsPublicationPublishDouble(p, 0.0)
            self.subscriptions = np.zeros((self.maxitrs, len(pub_list)))
            currenttime = h.helicsFederateRequestTime(vfed, t)
            for i in range(self.maxitrs):
                if i == 0:
                    while currenttime < t:
                        currenttime = h.helicsFederateRequestTime(vfed, t)
                else:
                    currenttime, iteration_state = h.helicsFederateRequestTimeIterative(
                        vfed,
                        t,
                        h.helics_iteration_request_force_iteration
                    )
                k = 0
                for p, s in zip(pub_list, sub_list):
                    x0 = h.helicsInputGetDouble(s)
                    self.subscriptions[i, k] = x0
                    if t > 1:
                        b = 0.05
                        a = t * 0.0025
                        x0 = self.method(i, k, x0, a, b)
                    h.helicsPublicationPublishDouble(p, x0)
                    k += 1
            self.subscriptions = np.delete(self.subscriptions, 0, 0)
            self.subscriptions = pd.DataFrame(self.subscriptions)
            #plt.plot(self.subscriptions)
        #plt.show()

    def no_algorithm(self, i, k, x0, a, b):
        return x0


    def gradient_descent(self, i, k, x0, a, b):
        dx0 = self.subscriptions[i, k] - self.subscriptions[i - 1, k]
        x0 = x0 - a * dx0
        return x0

    def heavy_ball(self, i, k, x0, a, b):
        dx0 = self.subscriptions[i, k] - self.subscriptions[i - 1, k]
        if i >= 2:
            x0 = x0 - a * dx0 + b * (x0 - self.subscriptions[i - 2, k])
        else:
            x0 = x0 - a * dx0
        return x0

    def newton_raphson(self, i, k, x0, a, b):
        return

    def helics_federate_boilerplate(self, federate_name):
        fed_name = f"Creating federate: {federate_name}"
        print(fed_name)
        fedinitstring = "--federates=1"
        fedinfo = h.helicsCreateFederateInfo()
        h.helicsFederateInfoSetCoreName(fedinfo, federate_name)
        h.helicsFederateInfoSetCoreTypeFromString(fedinfo, "zmq")
        h.helicsFederateInfoSetCoreInitString(fedinfo, fedinitstring)
        h.helicsFederateInfoSetTimeProperty(fedinfo, h.helics_property_time_delta, 0.1)
        h.helicsFederateInfoSetIntegerProperty(fedinfo, h.helics_property_int_max_iterations, 1000)
        vfed = h.helicsCreateValueFederate(federate_name, fedinfo)

        sub_list = []
        for p in self.publication_list:
            s = p.replace("..helper", "")
            sub_list.append(h.helicsFederateRegisterSubscription(vfed, s, ""))
            print(f"{federate_name} -> subscription created: {s}")


        pub_list = []
        print(self.publication_list)
        for p in self.publication_list:
            pub_list.append(h.helicsFederateRegisterGlobalTypePublication(vfed, p, "double", ""))
            print(f"{federate_name} -> publication created: {p}")



        h.helicsFederateEnterExecutingMode(vfed)
        return vfed, pub_list, sub_list


