#! /bin/zsh

# Setting environment variable to prevent plots from printing
# A faux backend that displays nothing
export MPLBACKEND=AGG

# Stop running examples once one of them fails
set -o errexit

# Delete out the existing log files so we don't fool ourselves with old results
find . -name "*.log" | xargs rm

#Advanced
echo "\n###### Advanced broker hierarchies #####"
cd ./advanced/advanced_brokers/hierarchies
helics run --path=./broker_hierarchy_runner_A.json &
helics run --path=./broker_hierarchy_runner_B.json &
helics run --path=./broker_hierarchy_runner_C.json

echo "\n###### Advanced multi-broker ######"
cd ../multi_broker
helics run --path=./multi_broker_runner.json

echo "\n###### Advanced simultaneous co-simulations ######"
cd ../simultaneous/federation_1
helics run --path=./federation_1_runner.json &
cd ../federation_2
helics run --path=./federation_2_runner.json &
cd ../federation_3
helics run --path=./federation_3_runner.json

echo "\n##### Advanced input and output ######"
cd ../../../advanced_input_output
helics run --path=./fib_runner.json

echo "\n###### Advanced iteration ######"
cd ../advanced_iteration
helics run --path=./advanced_iteration_runner.json

echo "\n##### Advanced multi-input #####"
cd ../advanced_message_comm/multi_input
helics run --path=./multi_input_runner.json

echo "\n###### Advanced query ######"
cd ../query
helics run --path=./query_runner.json

echo "\n##### Advanced translators ######"
cd ../translators
helics run --path=./translator_runner.json

echo "\n##### Advanced default ######"
cd ../../advanced_default
helics run --path=./advanced_default_runner.json