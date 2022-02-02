(helics_broker -t="zmq" --federates=3 --name=mainbroker --loglevel=trace &> ./broker.log &)

cd Transmission
(exec python Transmission_simulator.py &> ./TransmissionSim.log &)
cd ..

# cd EV_Controller
# (exec python EV_Controller.py &> ./EVControllerSim.log &)
# cd ..

cd Distribution
(gridlabd IEEE_123_feeder_0.glm &> ./DistributionSim.log &)
cd ..