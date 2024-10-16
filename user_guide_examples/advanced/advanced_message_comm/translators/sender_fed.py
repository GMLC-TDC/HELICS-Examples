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
import argparse

sim_max_time = 10

# Setting up pretty printing, mostly for debugging.
pp = pprint.PrettyPrinter(indent=4)

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.DEBUG)




def destroy_federate(fed, max_time):
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
    if max_time:
        granted_time = h.helicsFederateRequestTime(fed, h.HELICS_TIME_MAXTIME)
    else:
        granted_time = h.helicsFederateRequestTime(fed, 99999999)
    status = h.helicsFederateDisconnect(fed)
    h.helicsFederateDestroy(fed)
    logger.info("Federate finalized")
 

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    parser = argparse.ArgumentParser(description="")
    parser.add_argument('-m', '--max_time',
                        help="flag to only create a graph of the historic data"
                                "(no data collection)",
                        action=argparse.BooleanOptionalAction)
    args = parser.parse_args()
    
    if args.max_time:
        logger.debug("max_time flag set")

    fedinfo = h.helicsCreateFederateInfo()
    fedinfo.core_type = "zmq"
    fedinfo.core_init = "-f 1"
    fedinfo.property[h.HELICS_PROPERTY_INT_LOG_LEVEL] = h.HELICS_LOG_LEVEL_ERROR
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
        logger.debug(f"\tpublished value {out_value} as a double")
        #logger.debug(f"\treceived value {sub.double}")
        
    destroy_federate(senderFed, args.max_time)