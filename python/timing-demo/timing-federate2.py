# -*- coding: utf-8 -*-
import helics as h


def get_input(grantedtime):

    valid_input = False
    while not valid_input:
        print(
            "Enter request_time (int) (and value_to_send (float)) [e.g.: 4, 10.0]: ",
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


def create_value_federate(deltat=1.0, fedinitstring="--federates=1 --tick=0"):

    fedinfo = h.helicsCreateFederateInfo()

    h.helicsFederateInfoSetCoreName(fedinfo, "TestB Federate")

    h.helicsFederateInfoSetCoreTypeFromString(fedinfo, "zmq")

    h.helicsFederateInfoSetCoreInitString(fedinfo, fedinitstring)

    h.helicsFederateInfoSetTimeProperty(fedinfo, h.helics_property_time_delta, deltat)

    h.helicsFederateInfoSetIntegerProperty(fedinfo, h.helics_property_int_log_level, 1)

    fed = h.helicsCreateCombinationFederate("TestB Federate", fedinfo)

    return fed


def destroy_value_federate(fed):
    h.helicsFederateFinalize(fed)

    state = h.helicsFederateGetState(fed)

    h.helicsFederateFree(fed)

    h.helicsCloseLibrary()


def main():

    fed = create_value_federate()

    pubid = h.helicsFederateRegisterGlobalTypePublication(
        fed, "federate2-to-federate1", "string", ""
    )
    subid = h.helicsFederateRegisterSubscription(fed, "federate1-to-federate2", "")
    epid = h.helicsFederateRegisterGlobalEndpoint(fed, "endpoint2", "")

    h.helicsInputSetDefaultNamedPoint(subid, "", 0)

    print("Entering execution mode")
    h.helicsFederateEnterExecutingMode(fed)

    grantedtime = -1
    while True:
        try:
            stop_at_time, value_to_send = get_input(grantedtime)
        except KeyboardInterrupt:
            print("")
            break
        while grantedtime < stop_at_time:
            print(">>>>>>>> Requesting time = {}".format(stop_at_time))
            grantedtime = h.helicsFederateRequestTime(fed, stop_at_time)
            grantedtime = int(grantedtime)

            if grantedtime != stop_at_time:
                value = h.helicsSubscriptionGetKey(subid)
                print("Interrupt value '{}' from Federate 1".format(value))
            print("<<<<<<<< Granted Time = {}".format(grantedtime))
        assert (
            grantedtime == stop_at_time
        ), "stop_at_time = {}, grantedtime = {}".format(stop_at_time, grantedtime)
        if value_to_send is not None and value_to_send != "":
            print("Sending '{}' to Federate 1".format(value_to_send))
            h.helicsPublicationPublishString(pubid, str(value_to_send))

            h.helicsEndpointSendMessageRaw(epid, "endpoint1", str(value_to_send))

        value = h.helicsSubscriptionGetKey(subid)
        print("Received value '{}' from Federate 1".format(value))
        while h.helicsEndpointHasMessage(epid):
            value = h.helicsEndpointGetMessage(epid)
            print(
                "Received message '{}' at time {} from Federate 1".format(
                    value.data, value.time
                )
            )
        print("----------------------------------")

    destroy_value_federate(fed)


if __name__ == "__main__":
    main()
