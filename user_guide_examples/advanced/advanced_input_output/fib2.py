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
    output2 = '0'

    
    # Federation configuration
    # fed = h.helicsCreateValueFederateFromConfig('fib1_config.json')
    fedinfo = h.helicsCreateFederateInfo()
    fedinfo.core_type = 'zmq'
    fedinfo.core_init = '-f 1'
    fed = h.helicsCreateMessageFederate('fib2', fedinfo)
    ep = fed.register_endpoint('ep')
    ep.subscribe('fib1/out1')
    ep.subscribe('fib1/out2')
    ep.default_destination = 'fib3/ep'
    # Leave default destination blank so translator can send this to the
    #  destination of the translator
    msg1 = ep.create_message()
    msg2 = ep.create_message()

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
            
            # Message is raw bytes that need to be decoded. Following the 
            #   guidance Phil gave me on handing this:
            #   "just ignore the first 8 bytes and cast the next 8 to an int64"
            msg_bytes = bytearray(message.raw_data)
            del msg_bytes[0:8]
            msg_int = struct.unpack('q', msg_bytes) # long long int
            message = msg_int[0]
            messages.append(message)
            logger.debug(f'\tmessage received: {messages[-1]}')

        if len(messages) == 2:
        
            # Calculate local model (Fibonnaci series)
            output1 = str(messages[1])
            output2 = str(messages[0] + messages[1])

            # Produce outputs
            msg1.data = output1
            ep.send_data(msg1)
            msg2.data = output2
            ep.send_data(msg2)
            logger.debug(f'\tSent message  1: {output1}')
            logger.debug(f'\tSent message 2: {output2}')
            messages = [] # delete current list of messages

            # Check for terminate conditions and terminate as necessary
            if int(output2) >= 100:
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
    
    