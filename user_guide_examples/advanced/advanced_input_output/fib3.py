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
import struct



logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.DEBUG)

pp = pprint.PrettyPrinter(indent=2)


if __name__ == "__main__":
    
    # Set-up
    done = False
    time = 0  # Set up so each federate
    messages = []
    output2 = 0

    
    # Federation configuration
    # fed = h.helicsCreateValueFederateFromConfig('fib1_config.json')
    fedinfo = h.helicsCreateFederateInfo()
    fedinfo.core_type = 'zmq'
    fedinfo.core_init = '-f 1'
    fed = h.helicsCreateCombinationFederate('fib3', fedinfo)
    ep = fed.register_endpoint('ep')
    out1 = fed.register_publication('out1', 'double')
    out2 = fed.register_publication('out2', 'double')
    out1.add_target('fib4/in1')
    out2.add_target('fib4/in1')

    # Initialization
    fed.enter_initializing_mode()

    # Enter execution
    fed.enter_executing_mode()
        
    while not done:
        time += 1
        
        # Request time and get inputs
        granted_time = fed.request_time(time)
        logger.debug(f'Granted_time: {granted_time}')
        
        while ep.has_message():
            message = ep.get_message()
            messages.append(message.data)
            logger.debug(f'\tmessage received: {messages[-1]}')

        if len(messages) == 2:
        
            # Calculate local model (Fibonnaci series)
            output1 = int(messages[1])
            output2 = int(messages[0]) + int(messages[1])

            # Produce outputs
            out1.publish(output1)
            out2.publish(output2)
            logger.debug(f'\tPublished output 1: {output1}')
            logger.debug(f'\tPublished output 2: {output2}')
            messages = [] # delete current list of messages

            # Check for terminate conditions and terminate as necessary
            if output2 >= 100:
                done = True
            else:
                done = False
        elif len(messages) == 0:
            logger.debug(f'\tReceived no messages')
        elif len(messages) != 2 and len(messages) != 0:
            logger.debug(f'\tReceived (len(messages) messages, expecting 2)')
        
        if granted_time >= 1000: # Give up if this takes too many iterations
            done = True
        elif int(output2) > 100:
            done = True
        else:
            done = False 
    
      
    fed.disconnect()
    h.helicsCloseLibrary()
    
    