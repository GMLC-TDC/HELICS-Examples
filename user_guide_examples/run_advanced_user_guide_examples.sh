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

echo "\n###### Advanced broker hierarchies #####"
cd ./advanced/advanced_brokers/hierarchies
helics run --path=./broker_hierarchy_runner_A.json &
helics run --path=./broker_hierarchy_runner_B.json &
helics run --path=./broker_hierarchy_runner_C.json

# Fails due to broker port out of range
echo "\n###### Advanced multi-broker     SKIPPING    ######"
echo "\tHELICS Issue #2721"
echo "\n"
cd ../multi_broker
# helics run --path=./multi_broker_runner.json


echo "\n###### Advanced simultaneous co-simulations ######"
cd ../simultaneous/federation_1
helics run --path=./federation_1_runner.json &
cd ../federation_2
helics run --path=./federation_2_runner.json &
cd ../federation_3
helics run --path=./federation_3_runner.json

echo "\n##### Advanced input and output     SKIPPING      ######"
echo "\tHELICS issue #2524"
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

echo "\n##### Translators    SKIPPING      ######"
echo "\tHELICS issue #2562"
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

echo "\n##### Connector matchfile direct    SKIPPING     ######"
echo "\tHELICS issue #2722"
cd ../matchfile
# helics run --path=./connector_matchfile_direct_runner.json

echo "\n##### Connector matchfile regex ######"
helics run --path=./connector_matchfile_regex_runner.json

echo "\n##### Advanced default Pythonic ######"
cd ../../advanced_default_pythonic/
helics run --path=./advanced_default_runner.json

echo "\n##### Dynamic federation ######"
cd ../advanced_dynamic_federation/
helics run --path=./dynamic_federation_runner.json

echo "\n##### Single core federation ######"
cd ../advanced_single_core
helics run --path=./single_core_runner.json