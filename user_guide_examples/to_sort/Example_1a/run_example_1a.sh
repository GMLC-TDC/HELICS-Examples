(helics_broker -t="zmq" --federates=2 --name=mainbroker &> ./broker.log &)
cd Transmission
(exec python Transmission_simulator.py &> ./TransmissionSim.log &)
cd ..
cd Distribution
(gridlabd IEEE_123_feeder_0.glm &> ./DistributionSim.log &)
cd ..