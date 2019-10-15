/*
Copyright © 2017-2019,
Battelle Memorial Institute; Lawrence Livermore National Security, LLC; Alliance for Sustainable Energy, LLC.  See
the top-level NOTICE for additional details. All rights reserved.
SPDX-License-Identifier: BSD-3-Clause
*/

#include "helics/application_api.hpp"
#include "helics/core/helicsCLI11.hpp"
#include <iostream>
#include <thread>

int main (int argc, char *argv[])
{
    helics::helicsCLI11App app ("Filter Fed", "FilterFed");
    std::string targetFederate = "fed";
    std::string targetEndpoint = "endpoint";
    std::string delay = "1.0";
    std::string filtType = "delay";
    helics::filter_types ftype;
    double dropprob = 0.33;

    app.add_option ("--target,-t", targetFederate, "name of the federate to target");
    app.add_option ("--endpoint,-e", targetEndpoint, "name of the endpoint to filter");
    app.add_option ("--delay", delay, "the time to delay the message");
    app.add_option ("--filtertype", filtType, "the type of filter to implement")
        ->check(CLI::IsMember({
                        "delay",
                        "random_drop",
                        "random_delay"
                        }));
    app.add_option ("--dropprob", dropprob, "the probability a message will be dropped, only used with filtertype=random_drop");

    auto ret = app.helics_parse (argc, argv);
    if (ret != helics::helicsCLI11App::parse_output::ok)
    {
        return -1;
    }

    if (filtType == "delay")
    {
        ftype = helics::filter_types::delay;
    }
    else if (filtType == "random_drop")
    {
        ftype = helics::filter_types::random_drop;
    }
    else if (filtType == "random_delay")
    {
        ftype = helics::filter_types::random_delay;
    }

    std::string target = targetFederate + "/" + targetEndpoint;

    auto core = helics::CoreFactory::create(argc, argv);
    std::cout << " registering filter '"<< "' for " << target <<'\n';

    //create a source filter object with type, the fed pointer and a target endpoint
    auto filt = helics::make_filter(ftype, core.get());
    filt->addSourceTarget(target);

    // get a few specific parameters related to the particular filter
    switch (ftype)
    {
    case helics::filter_types::delay:
    default:
    {
        filt->setString("delay", delay);
        break;
    }
    case helics::filter_types::random_drop:
    {
        filt->set("dropprob", dropprob);
        break;
    }
    case helics::filter_types::random_delay:
    {
        filt->setString("distribution", "uniform");
        filt->setString("max", delay);
        break;
    }
    }

    // setup and run
    core->setCoreReadyToInit();

    core->waitForDisconnect();
    return 0;
}

