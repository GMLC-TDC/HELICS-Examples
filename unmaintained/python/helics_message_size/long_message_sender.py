# -*- coding: utf-8 -*-
"""
Created on 19 Nove 2024

Test federation to evaluate any message size limits of HELICS. 
This federate will send a message (string) of increasing size 
and the other federate will recieve it and check the size.

The message size is 10000 times the size of the granted time.


@author: Trevor Hardy
trevor.hardy@pnnl.gov
"""

import helics as h
import logging


logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.DEBUG)


if __name__ == "__main__":
    time_requests = [1, 10, 100, 1000, 10000, 100000, 1000000]
    
    fedinfo = h.helicsCreateFederateInfo()
    fedinfo.core_name = "long_message_sender_core"
    fedinfo.core_type = "zmq"
    fed = h.helicsCreateCombinationFederate("LongMessageSender", fedinfo)
    fed.register_global_endpoint("sender_ep")
    fed.property[h.HELICS_PROPERTY_TIME_PERIOD] = 0.0001
    fed.flag[h.HELICS_FLAG_WAIT_FOR_CURRENT_TIME_UPDATE] = False

    fed.enter_executing_mode()

    for time in time_requests:
        granted_time = fed.request_time(time)
        message_size = int(granted_time) * 1000
        send_string = 'x' * message_size
        fed.endpoints["sender_ep"].send_data(send_string, "receiver_ep")
        logger.info(f"Sent message of length {message_size}")

    h.helicsFederateDestroy(fed)
    h.helicsCloseLibrary()

