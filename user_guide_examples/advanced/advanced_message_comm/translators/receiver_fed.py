# -*- coding: utf-8 -*-
"""
Created on Jan 28, 2022

Test federate for evaluating translator functionality

@author: Trevor Hardy
trevor.hardy@pnnl.gov
"""

import helics as h
import logging
import numpy as np
import json
import pprint 

sim_max_time = 11 # To make sure the last message is receeived

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.DEBUG)




def destroy_federate(fed):
    """
    As part of ending a HELICS co-simulation it is good housekeeping to
    formally destroy a federate. Doing so informs the rest of the
    federation that it is no longer a part of the co-simulation and they
    should proceed without it (if applicable). Generally this is done
    when the co-simulation is complete and all federates end execution
    at more or less the same wall-clock time.

    :param fed: Federate to be destroyed
    :return: (none)
    """
    
    # Adding extra time request to clear out any pending messages to avoid
    #   annoying errors in the broker log. Any message are tacitly disregarded.
    granted_time = h.helicsFederateRequestTime(fed, h.HELICS_TIME_MAXTIME)
    status = h.helicsFederateDisconnect(fed)
    h.helicsFederateFree(fed)
    h.helicsCloseLibrary()
    logger.info("Federate finalized")
 

if __name__ == "__main__":
    
    
    fedinfo = h.helicsCreateFederateInfo()
    fedinfo.core_type = "zmq"
    fedinfo.core_init = "-f 1"
    fedinfo.property[h.HELICS_PROPERTY_INT_LOG_LEVEL] = h.HELICS_LOG_LEVEL_ERROR
    receiverFed = h.helicsCreateCombinationFederate("receiverFed", fedinfo)
    
    # ep = receiverFed.register_global_endpoint("endpoint")
    ep = h.helicsFederateRegisterGlobalTargetedEndpoint(receiverFed, "endpoint", "")
    
    # Add subscription
    # sub = receiverFed.register_subscription("value_out_1", "double")

    #Add the translator(s)
    translator = h.helicsFederateRegisterGlobalTranslator(receiverFed, h.HELICS_TRANSLATOR_TYPE_JSON, "translator")
    # Cheating and just copying the hard-coded names from both federates
    # To do this properly you might have to do a query or something similar.
    # As of Feb 1, the APIs to wire in the translator from the translator's
    # viewpoint don't work but from the other end should.
    #h.helicsTranslatorAddSourceTarget(translator, "value_out_1") 
    #h.helicsTranslatorAddDestinationTarget(translator, "endpoint")
    h.helicsEndpointAddSourceTarget(ep, "translator")
    
    
    receiverFed.enter_executing_mode()
    logger.info('Entered HELICS execution mode')
    
    query = h.helicsCreateQuery("root", "dependency_graph")
    graph = h.helicsQueryExecute(query, receiverFed)
    logger.info("Dependency graph query result:")
    logger.info(pprint.pformat(graph))
    
    granted_time = 0
    
    while granted_time < sim_max_time:
        request_time = int(granted_time + 1)
        logger.debug(f"Requested time: {request_time}")
        # Pick one timing strategy from the lines below
        granted_time = receiverFed.request_time(request_time) # Traditional
        # granted_time = receiverFed.request_time(h.HELICS_TIME_MAXTIME) # controller-style
        
        logger.debug(f"Granted time: {granted_time}")
        # logger.debug(f"\tlast published value: {sub.double}")
        msgDict = {"type": "double", "value": 0}
        if ep.has_message():
            msg = ep.get_message()
            logger.debug(f"\tmessage sent at {msg.time}")
            logger.debug(f"\ttranslated value: {msg.data}")
            msgDict = json.loads(msg.data)
#         out_value = msgDict["value"] - 0.3
#         jsonStr = f'{{"type": "double", "value": {out_value} }}'
#         out_msg = ep.create_message()
#         out_msg.data = jsonStr
#         out_msg.destination = "translator"
#         ep.send_data(out_msg)
#         logger.debug(f"\tnew sent message: {jsonStr}\n")
        
    destroy_federate(receiverFed)