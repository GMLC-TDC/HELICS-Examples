# -*- coding: utf-8 -*-
"""
Created on Feb 22, 2022

Fibonacci federate that takes two inputs, adds them together, and produces two outputs (new sum and the previous sum). This is one of several federates produces as part of a screencast on the HELICS YouTube channel to demonstrate how to write a federate and the multiplicity of input and output options.

@author: Trevor Hardy
trevor.hardy@pnnl.gov
"""

import helics as h
import logging
import json
import pprint
from ast import literal_eval




logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.DEBUG)

pp = pprint.PrettyPrinter(indent=2)


if __name__ == "__main__":
    
    # Set-up
    done = False
    time = 0  # Set up so each federate

    
    # Federation configuration
    # fed = h.helicsCreateValueFederateFromConfig('fib1_config.json')
    fedinfo = h.helicsCreateFederateInfo()
    fedinfo.core_type = 'zmq'
    fedinfo.core_init = '-f 1'
    fed = h.helicsCreateValueFederate('fib1', fedinfo)
    fed.property[h.HELICS_PROPERTY_TIME_PERIOD] = 1.0
    out1 = fed.register_publication('out1', 'integer')
    out2 = fed.register_publication('out2', 'integer')
    in1 = fed.register_subscription('fib4/out1', 'string')
    in1.set_default('[1,1]')
    

    # Initialization
    fed.enter_initializing_mode()
    
    # Add debugging query to see if the entire federation is set-up as expected
#     data_flow_graph = fed.query('root', 'data_flow_graph')
#     logger.debug('Data flow of the federation:')
#     logger.debug(pp.pformat(data_flow_graph))

    # Enter execution
    fed.enter_executing_mode()
    

        
    while not done:
        time += 1
        
        # Request time and get inputs
        granted_time = fed.request_time(time)
        logger.debug(f'Granted_time: {granted_time}')
        
        if in1.is_updated() == True or granted_time == 1:
            input_values = in1.string
            logger.debug(f'\tin1 value: {input_values}')

            # Calculate local model (Fibonnaci series)
            in_str = input_values
            in_list = literal_eval(in_str)
            output1 = in_list[1]
            output2 = in_list[0] + in_list[1]
    
            # Produce outputs
            out1.publish(output1)
            out2.publish(output2)
            logger.debug(f'\tPublished output 1: {output1}')
            logger.debug(f'\tPublished output 2: {output2}')

            # Check for terminate conditions and terminate as necessary
            if output2 >= 100:
                done = True
            else:
                done = False
        elif granted_time >= 1000: # Give up if this takes too many iterations
            done = True
        else:
            done = False
    
      
    fed.disconnect()
    h.helicsCloseLibrary()
    
    