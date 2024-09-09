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

# Fundamental
echo "\n###### Fundamental default #####"
cd ./fundamental/fundamental_default
helics run --path=./fundamental_default_runner.json 

echo "\n###### Fundamental integration ######"
cd ../fundamental_integration
helics run --path=./fundamental_integration_runner.json

echo "\n###### Fundamental combination ######"
cd ../fundamental_message_comm/combo
helics run --path=./fundamental_combo_runner.json

echo "\n##### Fundamental endpoints ######"
cd ../endpoints
helics run --path=./fundamental_endpoints_runner.json

echo "\n###### Fundamental native filters ######"
cd ../filter_native
helics run --path=./fundamental_filter_native_runner.json

echo "\n##### Fundamental filter federate #####"
cd ../filter_federate
helics run --path=./fundamental_filter_runner.json
