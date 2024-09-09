# -*- coding: utf-8 -*-
import time
import helics as h


def get_input(grantedtime):

    valid_input = False
    while not valid_input:
        print(
            "Enter request_time (int) (and value_to_send (str)) [e.g.: 4 hello, world]: ",
            end="",
        )
        string = input()
        string = string.strip()
        request_time_str = string.replace(",", " ").split(" ")[0]
        try:
            request_time = int(request_time_str)
            if request_time <= grantedtime:
                raise RuntimeError("Cannot proceed here because invalid input.")
        except:
            print(
                "request_time has to be an 'int' and has to be greater than grantedtime."
            )
            valid_input = False
            continue
        else:
            valid_input = True

        try:
            value_to_send = (
                string.replace(request_time_str, "").strip().strip(",").strip()
            )
        except:
            value_to_send = None
            valid_input = True
            continue

        try:
            value_to_send = str(value_to_send)
        except:
            print("value_to_send must be a str or be blank")
            valid_input = False
            continue
        else:
            valid_input = True

    return request_time, value_to_send


def create_broker():
    initstring = "-f 2"
    broker = h.helicsCreateBroker("zmq", "", initstring)
    isconnected = h.helicsBrokerIsConnected(broker)

    if isconnected == 1:
        pass

    return broker


def create_value_federate(broker, deltat=1.0, fedinitstring="--federates=1 --tick=0"):

    fedinfo = h.helicsCreateFederateInfo()

    h.helicsFederateInfoSetCoreName(fedinfo, "TestA Federate")

    h.helicsFederateInfoSetCoreTypeFromString(fedinfo, "zmq")

    h.helicsFederateInfoSetCoreInitString(fedinfo, fedinitstring)

    h.helicsFederateInfoSetTimeProperty(fedinfo, h.helics_property_time_delta, deltat)

    h.helicsFederateInfoSetIntegerProperty(fedinfo, h.helics_property_int_log_level, 1)

    fed = h.helicsCreateCombinationFederate("TestA Federate", fedinfo)

    return fed


def destroy_value_federate(fed, broker):
    h.helicsFederateFinalize(fed)

    state = h.helicsFederateGetState(fed)

    while h.helicsBrokerIsConnected(broker):
        time.sleep(1)

    h.helicsFederateFree(fed)

    h.helicsCloseLibrary()


def main(delay=None):

    broker = create_broker()
    fed = create_value_federate(broker)

    pubid = h.helicsFederateRegisterGlobalTypePublication(
        fed, "federate1-to-federate2", "string", ""
    )
    subid = h.helicsFederateRegisterSubscription(fed, "federate2-to-federate1", "")
    epid = h.helicsFederateRegisterGlobalEndpoint(fed, "endpoint1", "")

    if delay is not None:
        fid = h.helicsFederateRegisterGlobalFilter(
            fed, h.helics_filter_type_delay, "filter-name"
        )
        h.helicsFilterAddSourceTarget(fid, "endpoint1")

    h.helicsInputSetDefaultNamedPoint(subid, "", 0)

    print("Entering execution mode")
    h.helicsFederateEnterExecutingMode(fed)

    if delay is not None:
        h.helicsFilterSet(fid, "delay", delay)
    grantedtime = -1
    while True:
        try:
            stop_at_time, value_to_send = get_input(grantedtime)
            print(stop_at_time)
        except KeyboardInterrupt:
            print("")
            break
        while grantedtime < stop_at_time:
            print(">>>>>>>> Requesting time = {}".format(stop_at_time))
            grantedtime = h.helicsFederateRequestTime(fed, stop_at_time)
            grantedtime = int(grantedtime)
            if grantedtime != stop_at_time:
                value = h.helicsSubscriptionGetKey(subid)
                print("Interrupt value '{}' from Federate 2".format(value))
            print("<<<<<<<< Granted Time = {}".format(grantedtime))
        assert (
            grantedtime == stop_at_time
        ), "stop_at_time = {}, grantedtime = {}".format(stop_at_time, grantedtime)
        if value_to_send is not None and value_to_send != "":
            print("Sending '{}' to Federate 2".format(value_to_send))
            h.helicsPublicationPublishString(pubid, str(value_to_send))
            h.helicsEndpointSendMessageRaw(epid, "endpoint2", str(value_to_send))
        value = h.helicsSubscriptionGetKey(subid)
        print("Received value '{}' from Federate 2".format(value))
        while h.helicsEndpointHasMessage(epid):
            value = h.helicsEndpointGetMessage(epid)
            print(
                "Received message '{}' at time {} from Federate 2".format(
                    value.data, value.time
                )
            )
        print("----------------------------------")

    destroy_value_federate(fed, broker)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()

    parser.add_argument("--delay", default=False, help="Delay messages")
    args = parser.parse_args()
    if args.delay is not False:
        delay = int(args.delay)
    else:
        delay = None

    main(delay)
