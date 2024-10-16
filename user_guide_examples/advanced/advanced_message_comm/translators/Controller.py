"""
Created on 8/22/2023

This is a simple EV charge controller federate that manages the charging at
a set of charging terminals in a hypothetical EV garage. It receives periodic
SOC messages from each EV (associated with a particular charging terminal)
and sends back a message indicating whether the EV should continue charging
or not (based on whether it is full).

This version implements a translator which allows the charger to send the
SOC information as a message (as it does in the Advanced Fundamental Default
example) but have it converted to a value used by the a new version of the 
Controller written to do so. And just to keep things interesting, the 
Controller signal to the Charger is implemented as a message back with 
no translator necessary.

@author: Trevor Hardy
trevor.hardy@pnnl.gov
"""

import matplotlib.pyplot as plt
import helics as h
import logging
import numpy as np
import sys
import time
import pandas as pd
import argparse

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.DEBUG)


def destroy_federate(fed, max_time):
	'''
	As part of ending a HELICS co-simulation it is good housekeeping to
	formally destroy a federate. Doing so informs the rest of the
	federation that it is no longer a part of the co-simulation and they
	should proceed without it (if applicable). Generally this is done
	when the co-simulation is complete and all federates end execution
	at more or less the same wall-clock time.

	:param fed: Federate to be destroyed
	:return: (none)
	'''
	# Adding extra time request to clear out any pending messages to avoid
	#	annoying errors in the broker log. Any message are tacitly disregarded.
	if max_time:
		grantedtime = h.helicsFederateRequestTime(fed, h.HELICS_TIME_MAXTIME)
	else: 
		granted_time = h.helicsFederateRequestTime(fed, 99999999)
	status = h.helicsFederateDisconnect(fed)
	h.helicsFederateFree(fed)
	h.helicsCloseLibrary()
	logger.info('Federate finalized')


if __name__ == "__main__":
	logging.basicConfig(level=logging.DEBUG)
	parser = argparse.ArgumentParser(description="")
	parser.add_argument('-m', '--max_time',
                        help="flag to only create a graph of the historic data"
                                "(no data collection)",
                        action=argparse.BooleanOptionalAction)
	args = parser.parse_args()



	np.random.seed(1490)
	
	##############	Registering	 federate from json	 ##########################
	fed = h.helicsCreateCombinationFederateFromConfig("ControllerConfig.json")
	federate_name = h.helicsFederateGetName(fed)
	logger.info(f'Created federate {federate_name}')
	
	endid = h.helicsFederateGetEndpointByIndex(fed, 0)
	end_name = h.helicsEndpointGetName(endid)
	logger.info("Registered Endpoint ---> {}".format(end_name))
	
	sub_count = h.helicsFederateGetInputCount(fed)
	logger.debug(f'Number of inputs: {sub_count}')
	subid = {}
	sub_name = {}
	for i in range(0, sub_count):
		subid[i] = h.helicsFederateGetInputByIndex(fed, i)
		sub_name[i] = h.helicsInputGetName(subid[i])
		logger.debug(f'\tRegistered input---> {sub_name[i]}')
	
	translator_count = h.helicsFederateGetTranslatorCount(fed)
	logger.debug(f'Number of translators: {translator_count}')
	for i in range(0, translator_count):
		translator_obj = h.helicsFederateGetTranslatorByIndex(fed, i)
		translator_name = h.helicsTranslatorGetName(translator_obj)
		logger.debug(f'\tRegistered translator---> {translator_name}')
		valid = h.helicsTranslatorIsValid(translator_obj)
		logger.debug(f'\tTranslator valid: {valid}')
		if i == 0:
			info = h.helicsTranslatorGetInfo(translator_obj)
			logger.debug(f'\tTranslator info: {info}')
		
	


	##############	Entering Execution Mode	 ##################################
	h.helicsFederateEnterExecutingMode(fed)
	logger.info('Entered HELICS execution mode')
	
	query = h.helicsCreateQuery("broker", "global_flush")
	flush_results = h.helicsQueryExecute(query, fed)
	logger.debug(f'{flush_results}')
	
	query = h.helicsCreateQuery("broker", "data_flow_graph")
	graph = h.helicsQueryExecute(query, fed)
	logger.debug(f'Data flow graph: {graph}')

	hours = 24*7 # one week
	total_interval = int(60 * 60 * hours)
	grantedtime = 0

	# It is common in HELICS for controllers to have slightly weird timing
	#	Generally, controllers only need to produce new control values when
	#	their inputs change. Because of this, it is common to have them
	#	request a time very far in the future (helics_time_maxtime) and
	#	when a signal arrives, they will be granted a time earlier than
	#	that, recalculate the control output and request a very late time
	#	again.


	# Bug related to inconsistent interpretation of HELICS_TIME_MAXTIME
	# (maybe just in PyHELICS?) has us temporarily changing the terminal
	# condition for this example

	if args.max_time:
		logger.debug('MAXTIME flag set')
		starttime = h.HELICS_TIME_MAXTIME
	else:
		starttime = 300
	logger.debug(f'Requesting initial time {starttime}')
	grantedtime = h.helicsFederateRequestTime(fed, starttime)
	logger.debug(f'Granted time {grantedtime}')


	time_sim = []
	soc = {}

	while grantedtime < total_interval:

		# In HELICS, when multiple messages arrive at an endpoint they
		# queue up and are popped off one-by-one with the
		#	"helicsEndpointHasMessage" API call. When that API doesn't
		#	return a message, you've processed them all.
		for j in range(0, sub_count):

			# Get SOC from Charger presented as a value after passing through
			#	the translators.
			currentsoc = h.helicsInputGetDouble((subid[j]))
			logger.debug(f'\tReceived SOC {currentsoc:.2f} from input {sub_name[j]}')

			# Using a naming convention for this example, define the string that
			#	is the name of the endpoint that is the original source of this
			#	information.
			#	sub_name = Controller/EV1.soc
			#	endpoint to send message to: Charger/EV1.soc
			name_list = sub_name[j].split('/')
			source = 'Charger/' + name_list[1]
			logger.debug(f'\tMessage target endpoint: {source}')

			# Send back charging command based on current SOC
			#	Our very basic protocol:
			#		If the SOC is less than soc_full keep charging (send "1")
			#		Otherwise, stop charging (send "0")
			soc_full = 0.95
			if float(currentsoc) <= soc_full:
				instructions = 1
			else:
				instructions = 0
			message = str(instructions)
			h.helicsEndpointSendBytesTo(endid, message.encode(), source)
			logger.debug(f'\tSent message to endpoint {source}'
						 f' at time {grantedtime}'
						 f' with payload {instructions}')

			# Store SOC for later analysis/graphing
			if source not in soc:
				soc[source] = []
			soc[source].append(float(currentsoc))
			
			if len(time_sim) > 0:
				if time_sim[-1] != grantedtime:
					time_sim.append(grantedtime)
			else:
				time_sim.append(grantedtime)

		# Since we've dealt with all the messages that are queued, there's
		#	nothing else for the federate to do until/unless another
		#	message comes in. Request a time very far into the future
		#	and take a break until/unless a new message arrives.
		if args.max_time:
			logger.debug(f'Requesting time HELICS_TIME_MAXTIME')
			grantedtime = h.helicsFederateRequestTime(fed, h.HELICS_TIME_MAXTIME)
		else:
			logger.debug(f'Requesting next time')
			grantedtime = h.helicsFederateRequestNextStep(fed)
			logger.info(f'Granted time: {grantedtime}')

	# Close out co-simulation execution cleanly now that we're done.
	destroy_federate(fed, args.max_time)


	
	# Printing out final results graphs for comparison/diagnostic purposes.
	xaxis = np.array(time_sim)/3600
	y = []
	for key in soc:
		y.append(np.array(soc[key]))

	if len(y) > 0:
		fig, axs = plt.subplots(5, sharex=True, sharey=True)
		fig.suptitle('SOC at each charging port')

		axs[0].plot(xaxis, y[0], color='tab:blue', linestyle='-')
		axs[0].set_yticks(np.arange(0,1.25,0.5))
		axs[0].set(ylabel='Port 1')
		axs[0].grid(True)

		axs[1].plot(xaxis, y[1], color='tab:blue', linestyle='-')
		axs[1].set(ylabel='Port 2')
		axs[1].grid(True)

		axs[2].plot(xaxis, y[2], color='tab:blue', linestyle='-')
		axs[2].set(ylabel='Port 3')
		axs[2].grid(True)

		axs[3].plot(xaxis, y[3], color='tab:blue', linestyle='-')
		axs[3].set(ylabel='Port 4')
		axs[3].grid(True)

		axs[4].plot(xaxis, y[4], color='tab:blue', linestyle='-')
		axs[4].set(ylabel='Port 5')
		axs[4].grid(True)
		plt.xlabel('time (hr)')
		#for ax in axs():
	#		 ax.label_outer()
		# Saving graph to file
		plt.savefig('advanced_default_estimated_SOCs.png', format='png')
		plt.show()
	else:
		logger.warning("No SOC Controller data; co-simulation results are likely invalid.")
