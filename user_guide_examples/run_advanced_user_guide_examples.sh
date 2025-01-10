#! /bin/sh

# Setting environment variable to prevent plots from printing
# A faux backend that displays nothing
export MPLBACKEND=AGG

# Stop running examples once one of them fails
set -o errexit

# Delete out the existing log files so we don't fool ourselves with old results
if [ ! $CI ]; then
  find . -name "*.log" | xargs rm
fi

#Advanced

echo "\n###### Advanced broker hierarchies - SKIPPING   #####"
cd ./advanced/advanced_brokers/hierarchies
# helics run --path=./broker_hierarchy_runner_A.json &
# helics run --path=./broker_hierarchy_runner_B.json &
# helics run --path=./broker_hierarchy_runner_C.json

# Fails due to broker port out of range
echo "\n###### Advanced multi-broker - SKIPPING  ######"
cd ../multi_broker
# helics run --path=./multi_broker_runner.json


echo "\n###### Advanced simultaneous co-simulations - SKIPPING  ######"
# Fails due to graphing index problems
cd ../simultaneous/federation_1
# helics run --path=./federation_1_runner.json &
# cd ../federation_2
# helics run --path=./federation_2_runner.json &
# cd ../federation_3
# helics run --path=./federation_3_runner.json

# Example does not run due to filter bug
# HELICS issue #2524
# echo "\n##### Advanced input and output ######"
cd ../../../advanced_input_output
# helics run --path=./fib_runner.json

echo "\n###### Iteration ######"
cd ../advanced_iteration
helics run --path=./advanced_iteration_runner.json

echo "\n##### Multi-input #####"
cd ../advanced_message_comm/multi_input
helics run --path=./multi_input_runner.json

echo "\n###### Queries ######"
cd ../query
helics run --path=./query_runner.json

echo "\n##### Translators - SKIPPING   ######"
# Doesn't run to completion
cd ../translators
# helics run --path=./translator_runner.json

echo "\n##### Advanced default ######"
cd ../../advanced_default
helics run --path=./advanced_default_runner.json

echo "\n##### Async time request ######"
cd ../advanced_async_time_request
helics run --path=./async_runner.json

echo "\n##### Connector interface creation ######"
cd ../advanced_connector/interface_creation
helics run --path=./connector_interface_creation_runner.json

echo "\n##### Connector matchfile direct ######"
cd ../matchfile
# Currently not working
# HELICS Examples issue #101
# helics run --path=./connector_matchfile_direct_runner.json
helics run --path=./connector_matchfile_regex_runner.json

echo "\n##### Advanced default Pythonic ######"
cd ../../advanced_default_pythonic/
helics run --path=./advanced_default_runner.json

# Graphing needs to be looked at
# echo "\n##### Dyanmic federation ######"
cd ../advanced_dynamic_federation/
# helics run --path=./dynamic_federation_runner.json

echo "\n##### Single core federation ######"
cd ../advanced_single_core
helics run --path=./single_core_runner.json