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
import time as t



logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.DEBUG)

pp = pprint.PrettyPrinter(indent=2)


if __name__ == "__main__":
    
    # Set-up
    done = False
    time = 0
    
    # Federation configuration
    # fed = h.helicsCreateValueFederateFromConfig('fib4_config.json')
    fedinfo = h.helicsCreateFederateInfo()
    fedinfo.core_type = 'zmq'
    fedinfo.core_init = '-f 1'
    fed = h.helicsCreateValueFederate('fib4', fedinfo)
    in1 = fed.register_input('in1', 'double',)
    in1.option['MULTI_INPUT_HANDLING_METHOD'] = h.HELICS_MULTI_INPUT_VECTORIZE_OPERATION
    out1 = fed.register_publication('out1', 'vector')

    # Initialization
    fed.enter_initializing_mode()
    

    # Enter execution
    fed.enter_executing_mode()
        
    while not done:    
        time += 1
     
        # Request time and get inputs
        granted_time = fed.request_time(time)
        logger.debug(f'Granted_time: {granted_time}')
        
        if in1.is_updated() == True:
            in_values = in1.vector
            logger.debug(f'in1 value: {in_values}')

            # Calculate local model (Fibonnaci series)
            output1 = in_values[1]
            output2 = in_values[0]+ in_values[1]

    
            # Produce outputs
            output = [output1, output2]
            out1.publish(output)
            logger.debug(f'\tPublished output: [{output1}, {output2}]')

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
    
    