# -*- coding: utf-8 -*-
"""
Created on 19 Nove 2024

Test federation to evaluate any message size limits of HELICS. 
This federate receives the bytes and based on the granted time,
validates that all bytes sent have been received.

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
    fedinfo.core_name = "long_message_receiver_core"
    fedinfo.core_type = "zmq"
    fed = h.helicsCreateCombinationFederate("LongMessageReceiver", fedinfo)
    fed.register_global_endpoint("receiver_ep")
    fed.property[h.HELICS_PROPERTY_TIME_PERIOD] = 0.0001
    fed.flag[h.HELICS_FLAG_WAIT_FOR_CURRENT_TIME_UPDATE] = True

    fed.enter_executing_mode()

    for time in time_requests:
        granted_time = fed.request_time(time)
        intended_message_size = granted_time * 1000
        if fed.endpoints["receiver_ep"].has_message:
            helics_message = fed.endpoints["receiver_ep"].get_message()
            message_str = helics_message.data
            message_num_char = len(message_str)
            if message_num_char == intended_message_size:
                logger.debug(f"Full message received of size {int(intended_message_size)}")
            else: 
                logger.error(f"Incomplete message received of size {int(message_num_char)} out of {int(intended_message_size)}")
        else:
            logger.debug(f"No message waiting at time {granted_time}")

    h.helicsFederateDestroy(fed)
    h.helicsCloseLibrary()

