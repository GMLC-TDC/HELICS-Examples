from datetime import datetime, timedelta
from pypsse import pyPSSE_instance
from helper_federate import Helper
from shutil import copyfile
from cymepy import cymepy
import multiprocessing
import pandas as pd
import numpy as np
import helics as h

import time
import toml
import os

def run_broker(n, ip, port):
    print("Creating Broker")
    initstring = f"-f {n} --name=mainbroker --brokerport={port}"
    broker = h.helicsCreateBroker("zmq", "", initstring)
    # print(broker.address)
    print(f"Created Broker: {broker} with settings {initstring}")
    isconnected = h.helicsBrokerIsConnected(broker)

    if isconnected == 1:
        print("Broker created and connected")

    while h.helicsBrokerIsConnected(broker):
        time.sleep(1)

    print("Closing broker")
    h.helicsCloseLibrary()
    return

def run_cyme(settings):
    dist_instance = cymepy.cymeInstance(settings)
    dist_instance.runSimulation()

def run_psse(model_path):
    trans_inst = pyPSSE_instance.pyPSSE_instance(model_path)
    trans_inst.init()
    trans_inst.run()

def run_helper(broker_ip, broker_port, publications, duration_sec, timestep_sec, maxitrs,  method):
    helper_federate = Helper(broker_ip, broker_port, publications, duration_sec, timestep_sec, maxitrs,  method)
    helper_federate.run()

class Cosimulation:

    maxiters = 5
    algo = 0

    cyme_model_paths = [
        r"C:\Users\alatif\Desktop\Models\Cyme\ieee13node1\Settings.toml",
        r"C:\Users\alatif\Desktop\Models\Cyme\ieee13node2\Settings.toml",
        # r"C:\Users\alatif\Desktop\Models\Cyme\ieee13node3\Settings.toml",
        # r"C:\Users\alatif\Desktop\Models\Cyme\ieee13node4\Settings.toml",
        # r"C:\Users\alatif\Desktop\Models\Cyme\ieee13node5\Settings.toml",
    ]

    Pinit = 1984
    Qinit = 1514

    coupling_buses = [
        153,
        154,
        203,
        205,
        3005,
        3007,
        3008
    ]

    loads = {
        153: [200, 100],
        154: [600, 450],
        203: [300, 150],
        205: [1200, 700],
        3005: [100, 50],
        3007: [200, 75],
        3008: [200, 75],
    }

    psse_model = r"C:\Users\alatif\Desktop\Models\PSSE\static_example\Settings\pyPSSE_settings.toml"
    base_path = os.getcwd()
    broker = "127.0.0.1"
    port = 23404

    publications = []

    def update_psse_settings(
            self, fault_bus, duration, timestep, fault_resistance, fault_reactance, fault_time, itrmode,
            cosim_mode, helper_federate
    ):
        setttings = toml.load(self.psse_model)
        setttings["Simulation"]["PSSE solver timestep (sec)"] = timestep
        setttings["HELICS"]["Cosimulation mode"] = cosim_mode
        setttings["HELICS"]["Iterative Mode"] = itrmode
        setttings["HELICS"]["Broker"] = self.broker
        setttings["HELICS"]["Broker port"] = self.port
        setttings["HELICS"]["Iterative Mode"] = itrmode
        setttings["HELICS"]["Time delta"] = timestep / 10.0
        setttings["HELICS"]["Max co-iterations"] = 5
        setttings["Simulation"]["Simulation time (sec)"] = duration
        setttings["Simulation"]["Step resolution (sec)"] = timestep
        if fault_bus:
            setttings["contingencies"]["bus_fault"]["bf_1"]["time"] = fault_time
            setttings["contingencies"]["bus_fault"]["bf_1"]["bus_id"] = fault_bus
            setttings["contingencies"]["bus_fault"]["bf_1"]["fault_impedance"] = [fault_resistance, fault_reactance]

        toml.dump(setttings, open(self.psse_model, "w"))

        self.setup_psse_subscriptions(helper_federate)
        return setttings

    def setup_psse_subscriptions(self, helper_federate):
        data = {
            "bus_subsystem_id": 0,
            "bus": None,
            "element_type": "Load",
            "element_id": 1,
            "property": None,
            "sub_tag": "CYME1.Source.SUB650WYE-S2.",
            "scaler": None,
        }

        mapper = {
            "PL": "KWTOT",
            "QL": "KVARTOT",
        }
        subs = []
        for i in range(len(self.cyme_model_paths)):
            bus = self.coupling_buses[i]
            S = self.loads[bus]
            data["bus"] = bus
            for k, v in zip(mapper, S):
                data["property"] = [k]
                data["scaler"] = [v / self.Pinit if k == "PL" else v / self.Qinit]
                if helper_federate:
                    pub = f"CYME{i+1}.Source.SUB650WYE-S2.{mapper[k]}..helper"
                    data["sub_tag"] = pub
                    self.publications.append(pub)
                else:
                    pub = f"CYME{i+1}.Source.SUB650WYE-S2.{mapper[k]}"
                    data["sub_tag"] = pub
                    self.publications.append(pub)
                subs.append(data.copy())

        subs = pd.DataFrame(subs)
        subpath = self.psse_model.replace("pyPSSE_settings.toml", "Subscriptions.csv")
        subs.to_csv(subpath, index=False)

    def update_cyme_settings(self, duration_sec, timestep_sec, itrmode, cosim_mode, helper_federate):
        all_settings = []
        cyme_subscriptions = []
        M = 1
        for cBus, mdl in zip(self.coupling_buses, self.cyme_model_paths):
            setttings = toml.load(mdl)
            startTime = datetime.strptime(setttings["project"]['start_time'], '%Y-%m-%d %H:%M:%S.%f')
            endTime = startTime + timedelta(seconds=duration_sec)
            
            setttings["project"]["project_path"] = mdl.replace("Settings.toml", "")
            setttings["project"]["project_path"] = mdl.replace("Settings.toml", "")

            setttings["project"]["end_time"] = str(endTime) + ".0"
            setttings["project"]["time_step_min"] = timestep_sec / 60.0
            setttings["helics"]["cosimulation_mode"] = cosim_mode
            setttings["helics"]["coiter_mode"] = itrmode
            setttings["helics"]["broker"] = self.broker
            setttings["helics"]["broker_port"] = self.port
            setttings["helics"]["time_delta"] = timestep_sec / 600.0
            setttings["helics"]["max_coiter"] = 5
            setttings["Exports"]["export_file_type"] = "h5"
            all_settings.append(setttings)

            subscriptions = toml.load(mdl.replace("Settings.toml", "Subscriptions.toml"))
            for obj, subs in subscriptions.items():
                for s in subs:
                    if not helper_federate:
                        s['subscription'] = f"psse.Buses.{cBus}.PU"
                        self.publications.append(f"psse.Buses.{cBus}.PU")
                        #print(f"CYME{M}/{s['property']}: psse.Buses.{cBus}.PU")
                    else:
                        s['subscription'] = f"psse.Buses.{cBus}.PU..helper"
                        self.publications.append(f"psse.Buses.{cBus}.PU..helper")
                        #print(f"CYME{M}/{s['property']}: psse.Buses.{cBus}.PU..helper")

            toml.dump(subscriptions, open(mdl.replace("Settings.toml", "Subscriptions.toml"), "w"))
            M += 1
        return all_settings

    def run_scenarios(
            self, sim_time, timestep, fault_resistance, fault_reactance, fault_time, itrmode, cosim_mode,
            helper_federate, fault_bus
    ):
        self.jobs = []

        #UPDATE SIMULATOR SETTINGS
        cyme_settings = self.update_cyme_settings(
            sim_time, timestep, itrmode, cosim_mode, helper_federate
        )
        psse_settings = self.update_psse_settings(
            fault_bus, sim_time, timestep, fault_resistance, fault_reactance,
            fault_time, itrmode, cosim_mode, helper_federate
        )

        #RUN BROKER
        if cosim_mode:
            if helper_federate:
                n = len(cyme_settings) + 2
            else:
                n = len(cyme_settings) + 1
            p = multiprocessing.Process(target=run_broker, args=(n, self.broker, self.port,))
            self.jobs.append(p)
            p.start()

        # RUN HELPER FEDERATE
        if helper_federate:
            p = multiprocessing.Process(
                target=run_helper,
                args=(self.broker, self.port, self.publications, sim_time, timestep, self.maxiters, self.algo,)
            )
            self.jobs.append(p)
            p.start()

        # #RUN CYME INSTANCES
        for i, sc in enumerate(cyme_settings):
            p = multiprocessing.Process(target=run_cyme, args=(sc,))
            self.jobs.append(p)
            p.start()

        #RUN PSSE INSTANCE
        run_psse(self.psse_model)

        return


    def get_results(self, rPath, scenario):
        nPath = os.path.join(rPath, scenario)
        if not os.path.exists(nPath):
            os.mkdir(nPath)

        for i, cPath in enumerate(self.cyme_model_paths):
            cePath = cPath.replace("Settings.toml", r"exports\Results.h5")
            cenewPath = os.path.join(nPath, f"CYME{i+1}.h5")

            copyfile(cePath, cenewPath)

        pePath = self.psse_model.replace(r"Settings\pyPSSE_settings.toml", r"Exports\Simulation_results.hdf5")
        penewPath = os.path.join(nPath, f"PSSE.h5")
        copyfile(pePath, penewPath)


if __name__ == '__main__':

    timestep = 900.0
    sim_time_sec = 86400.0
    fault_resistance = 0.001
    fault_reactance = 0.001
    fault_time = 87000.0
    itrmode = True
    cosim_mode = True
    helper_federate = True
    fault_bus = 102

    simulation_instance = Cosimulation()
    simulation_instance.run_scenarios(
        sim_time_sec,
        timestep,
        fault_resistance,
        fault_reactance,
        fault_time,
        itrmode,
        cosim_mode,
        helper_federate,
        fault_bus
    )

    isItr = "itr" if itrmode else "noItr"
    isHelper = "helper" if helper_federate else "noHelper"
    simulation_instance.get_results(
        r"C:\Users\alatif\Desktop\Models\Results",
        f"{isItr}-{isHelper}-{simulation_instance.algo}"
    )