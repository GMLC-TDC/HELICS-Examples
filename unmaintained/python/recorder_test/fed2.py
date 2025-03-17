import helics as h
import logging
import numpy as np


logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.DEBUG)


fed = h.helicsCreateCombinationFederateFromConfig("fed2_config.json")
logger.info(f'Created federate {fed.name}')

# Setting up HELICS interfaces
sub_obj = fed.get_subscription_by_index(0)
sub_name = sub_obj.target
logger.debug(f'\tRegistered subscription---> {sub_name}')
ep_obj = fed.get_endpoint_by_index(0)
ep_name = ep_obj.name
logger.debug(f'\tRegistered endpoint ---> {ep_name}')

# Setting up timing
max_time = 10
update_interval = int(h.helicsFederateGetTimeProperty(
                                fed,
                                h.helics_property_time_period))
granted_time = 0.2 - update_interval
                   
fed.enter_executing_mode()
logger.info('Entered HELICS execution mode')   
          
while granted_time < max_time:
    # Time request for the next physical interval to be simulated
    requested_time = (granted_time + update_interval)
    logger.debug(f'Requesting time {requested_time}')
    granted_time = fed.request_time(requested_time)
    logger.debug(f'Granted time {granted_time}')
    
    if sub_obj.is_updated():
        received_value = sub_obj.value
        message_str = str(received_value)
        ep_obj.send_data(message_str, "Federate3_Endpoint")
        logger.debug(f"endpoint sending value: {message_str}")
    else:
        logger.debug("No messages received on endpoint")

# Ending federate cleanly
fed.disconnect()
h.helicsFederateDestroy(fed)
logger.info('Federate2 finalized')