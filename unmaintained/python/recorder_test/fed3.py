import helics as h
import logging
import numpy as np


logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.DEBUG)


fed = h.helicsCreateCombinationFederateFromConfig("fed3_config.json")
logger.info(f'Created federate {fed.name}')

# Setting up HELICS interfaces
ep_obj = fed.get_endpoint_by_index(0)
ep_name = ep_obj.name
logger.debug(f'\tRegistered endpoint ---> {ep_name}')
pub_obj = fed.get_publication_by_index(0)
pub_name = pub_obj.name
logger.debug(f'\tRegistered publication---> {pub_name}')

# Setting up timing
max_time = 10
update_interval = int(h.helicsFederateGetTimeProperty(
                                fed,
                                h.helics_property_time_period))
granted_time = 0.3 - update_interval

                   
fed.enter_executing_mode()
logger.info('Entered HELICS execution mode')   
          
while granted_time < max_time:
    # Time request for the next physical interval to be simulated
    requested_time = (granted_time + update_interval)
    logger.debug(f'Requesting time {requested_time}')
    granted_time = fed.request_time(requested_time)
    logger.debug(f'Granted time {granted_time}')
    
    if ep_obj.has_message():
        message_obj = ep_obj.get_message()
        message_str = message_obj.data
        message_value = float(message_str)
        pub_obj.publish(message_value)
        logger.debug(f"publishing value: {message_value}")
    else:
        logger.debug("No messages received on endpoint")

# Ending federate cleanly
fed.disconnect()
h.helicsFederateDestroy(fed)
logger.info('Federate3 finalized')