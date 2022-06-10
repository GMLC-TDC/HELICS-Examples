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
import pprint 

sim_max_time = 10

# Setting up pretty printing, mostly for debugging.
pp = pprint.PrettyPrinter(indent=4)

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
    grantedtime = h.helicsFederateRequestTime(fed, h.HELICS_TIME_MAXTIME)
    status = h.helicsFederateDisconnect(fed)
    h.helicsFederateFree(fed)
    h.helicsCloseLibrary()
    logger.info("Federate finalized")
 

if __name__ == "__main__":
    
    
    fedinfo = h.helicsCreateFederateInfo()
    fedinfo.core_type = "zmq"
    fedinfo.core_init = "-f 1"
    h.helicsFederateInfoSetIntegerProperty(fedinfo, h.HELICS_PROPERTY_INT_LOG_LEVEL, h.helics_log_level_interfaces)
    senderFed = h.helicsCreateValueFederate("senderFed", fedinfo)
    pub = h.helicsFederateRegisterGlobalPublication(senderFed, "value_out_1", h.HELICS_DATA_TYPE_DOUBLE)
    #sub = senderFed.register_subscription("translator", "double")
    h.helicsPublicationAddTarget(pub, "translator")
    senderFed.enter_executing_mode()
    logger.info('Entered HELICS execution mode')
    
    query = h.helicsCreateQuery("root", "dependency_graph")
    graph = h.helicsQueryExecute(query, senderFed)
    logger.info("Dependency graph query results:")
    logger.info(pp.pformat(graph))
    
    
    granted_time = 0
    
    while granted_time < sim_max_time:
        granted_time = senderFed.request_time(granted_time + 1)
        logger.debug(f"Granted time: {granted_time}")
        out_value = granted_time + 0.314159
        senderFed.get_publication_by_name("value_out_1").publish(out_value)
        logger.debug(f"\tsent value {out_value} as a double")
        #logger.debug(f"\treceived value {sub.double}")
        
    destroy_federate(senderFed)