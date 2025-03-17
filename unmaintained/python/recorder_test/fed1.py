import helics as h
import logging
import numpy as np


logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.DEBUG)


fed = h.helicsCreateValueFederateFromConfig("fed1_config.json")
logger.info(f'Created federate {fed.name}')

# Setting up HELICS interfaces
sub_obj = fed.get_subscription_by_index(0)
sub_name = sub_obj.target
logger.debug(f'\tRegistered subscription---> {sub_name}')
pub_obj = fed.get_publication_by_index(0)
pub_name = pub_obj.name
logger.debug(f'\tRegistered publication---> {pub_name}')

# Setting up timing

max_time = 10
update_interval = int(h.helicsFederateGetTimeProperty(
                                fed,
                                h.helics_property_time_period))
granted_time = 0.1 - update_interval
initial_value = 1
                   
fed.enter_executing_mode()
logger.info('Entered HELICS execution mode')   
pub_obj.publish(initial_value)


while granted_time < max_time:
     # Time request for the next physical interval to be simulated
    requested_time = (granted_time + update_interval)
    logger.debug(f'Requesting time {requested_time}')
    granted_time = fed.request_time(requested_time)
    logger.debug(f'Granted time {granted_time}')

    if sub_obj.is_updated():
        new_value = sub_obj.value + 1
        pub_obj.publish(new_value)
        logger.debug(f"publishing value: {new_value}")
    else:
        logger.debug("Subscription not updated")
        
   

# Ending federate cleanly
fed.disconnect()
h.helicsFederateDestroy(fed)
logger.info('Federate1 finalized')