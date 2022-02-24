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



logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.DEBUG)

pp = pprint.PrettyPrinter(indent=4)


if __name__ == "__main__":
    
    # Set-up
    done = False
    
    # Federation configuration
    fed = h.helicsCreateValueFederateFromConfig('fib4_config.json')
#         fedinfo = h.helicsCreateFederateInfo()
#         fedinfo.core_type = 'zmq'
#         fedinfo.core_init = '-f 1'
#         fed = h.helicsCreateValueFederate('fib4', fedinfo)
    #out1 = fed.register_publication('out1', 'vector')
    #in1 = fed.register_input('in1', 'double',)
    #in1.option['MULTI_INPUT_HANDLING_METHOD'] = h.HELICS_MULTI_INPUT_VECTORIZE_OPERATION

    # Initialization
    #fed.enter_initializing_mode()
    
    # Add debugging query to see if the entire federation is set-up as expected
    

    # Enter execution
    fed.enter_executing_mode()
        
    while not done:
        # Request time and get inputs
        fed.request_time(h.HELICS_TIME_MAXTIME)

        # Calculate local model
    
        # Produce outputs
    
        # Check for terminate conditions and terminate as necessary
        done = True
        
    fed.disconnect()
    h.helicsCloseLibrary()
    
    