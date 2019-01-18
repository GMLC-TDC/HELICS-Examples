/*
Copyright © 2017-2018,
Battelle Memorial Institute; Lawrence Livermore National Security, LLC; Alliance for Sustainable Energy, LLC
All rights reserved. See LICENSE file and DISCLAIMER for more details.
*/

#include "helics/application_api.hpp"
#include <iostream>
#include <thread>
#include "helics/core/BrokerFactory.hpp"
#include "helics/common/argParser.h"

static const helics::ArgDescriptors InfoArgs{
    {"startbroker","start a broker with the specified arguments"},
    {"target,t", "name of the target federate"},
    {"valuetarget","name of the value federate to target"},
    {"messgetarget","name of the message federate to target"},
    {"endpoint,e", "name of the target endpoint"},
    {"source,s", "name of the source endpoint"}
    //name is captured in the argument processor for federateInfo
};

int main (int argc, char *argv[])
{
    helics::FederateInfo fi;
    helics::variable_map vm;
    auto parseResult = argumentParser(argc, argv, vm, InfoArgs);
    fi.loadInfoFromArgs(argc, argv);
    if (parseResult != 0)
    {
        return 0;
    }

	std::string vtarget = "fed";
    std::string mtarget = "fed";
	if (vm.count("target") > 0)
	{
		mtarget= vm["target"].as<std::string>();
        vtarget = mtarget;
	}
    if (vm.count("valuetarget") > 0)
    {
        vtarget = vm["valuetarget"].as<std::string>();
    }
    if (vm.count("messagetarget") > 0)
    {
        mtarget = vm["messagetarget"].as<std::string>();
    }
    std::string targetEndpoint = "endpoint";
    if (vm.count("endpoint") > 0) {
        targetEndpoint = vm["endpoint"].as<std::string>();
    }
    std::string etarget = mtarget + "/" + targetEndpoint;
    std::string myendpoint = "endpoint";
    if (vm.count("source") > 0)
    {
        myendpoint = vm["source"].as<std::string>();
    }

	fi.setProperty(helics::defs::properties::log_level, 5);
    std::shared_ptr<helics::Broker> brk;
    if (vm.count("startbroker") > 0)
    {
        brk = helics::BrokerFactory::create(fi.coreType, vm["startbroker"].as<std::string>());
    }

    auto cFed = std::make_unique<helics::CombinationFederate> ("fed",fi);
    auto name = cFed->getName();
	std::cout << " registering endpoint '" << myendpoint << "' for " << name<<'\n';

    //this line actually creates an endpoint and gets a reference to an endpoint object
    auto &ept = cFed->registerEndpoint(myendpoint);
	//this line actually registers a publication and gets a reference to a publication object
    auto &pub = cFed->registerPublication("pub", "double");
	//this line creates a subscription to a publication at a specific target and gets a reference to the input object object
    auto &sub = cFed->registerSubscription(vtarget + "/pub");
    std::cout << "entering init State\n";
    cFed->enterInitializingMode ();
    std::cout << "entered init State\n";
    cFed->enterExecutingMode ();
    std::cout << "entered exec State\n";
    for (int i=1; i<10; ++i) {
		std::string message = "message sent from "+name+" to "+etarget+" at time " + std::to_string(i);
		ept.send(etarget, message);
        pub.publish(i);
        std::cout << message << std::endl;
        auto newTime = cFed->requestTime (i);
		std::cout << "processed time " << static_cast<double> (newTime) << "\n";
		while (ept.hasMessage())
		{
			auto nmessage = ept.getMessage();
			std::cout << "received message from " << nmessage->source << " at " << static_cast<double>(nmessage->time) << " ::" << nmessage->data.to_string() << '\n';
		}
        
        if (sub.isUpdated())
        {
            auto val = sub.getValue<double>();
            std::cout << "received updated value of "<<val<<" at " << newTime << " from " << cFed->getTarget(sub) << '\n';
        }

    }
    cFed->finalize ();
    if (brk)
    {
        while (brk->isConnected())
        {
            std::this_thread::yield();
        }
        brk = nullptr;
    }
    return 0;
}

