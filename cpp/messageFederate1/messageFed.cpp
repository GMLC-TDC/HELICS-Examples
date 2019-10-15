/*
Copyright © 2017-2019,
Battelle Memorial Institute; Lawrence Livermore National Security, LLC; Alliance for Sustainable Energy, LLC.  See
the top-level NOTICE for additional details. All rights reserved.
SPDX-License-Identifier: BSD-3-Clause
*/
#include "helics/MessageFederates.hpp"
#include "helics/apps/BrokerApp.hpp"
#include "helics/core/helicsCLI11.hpp"
#include "helics/core/helics_definitions.hpp"

#include <iostream>

int main (int argc, char *argv[])
{
    helics::helicsCLI11App app ("Message Fed", "MessageFed");
    std::string targetFederate = "fed";
    std::string targetEndpoint = "endpoint";
    std::string myendpoint = "endpoint";
    helics::apps::BrokerApp brk;
    std::string brokerArgs = "";

    app.add_option ("--messagetarget,--target,-t", targetFederate, "name of the target federate");
    app.add_option ("--endpoint,-e", targetEndpoint, "name of the target endpoint");
    app.add_option ("--source,-s", myendpoint, "name of the source endpoint");
    app.add_option ("--startbroker", brokerArgs, "start a broker with the specified arguments");

    auto ret = app.helics_parse (argc, argv);

    helics::FederateInfo fi;
    if (ret == helics::helicsCLI11App::parse_output::help_call)
    {
        fi.loadInfoFromArgs ("--help");
        return 0;
    }
    else if (ret == helics::helicsCLI11App::parse_output::ok)
    {
        return -1;
    }
    fi.defName = "fed";
    fi.loadInfoFromArgs (app.remainArgs ());

    std::string target = targetFederate + "/" + targetEndpoint;

    fi.setProperty(helics::defs::properties::log_level, 5);
    if (app["--startbroker"]->count () > 0)
    {
        brk = helics::apps::BrokerApp (fi.coreType, brokerArgs);
    }

    auto mFed = std::make_unique<helics::MessageFederate> (std::string{},fi);
    auto name = mFed->getName();
    std::cout << " registering endpoint '" << myendpoint << "' for " << name<<'\n';

    //this line actually creates an endpoint
    auto &ept = mFed->registerEndpoint(myendpoint);

    std::cout << "entering init State\n";
    mFed->enterInitializingMode ();
    std::cout << "entered init State\n";
    mFed->enterExecutingMode ();
    std::cout << "entered exec State\n";
    for (int i=1; i<10; ++i) {
        std::string message = "message sent from "+name+" to "+target+" at time " + std::to_string(i);
        mFed->sendMessage(ept, target, message.data(), message.size());
        std::cout << message << std::endl;
        auto newTime = mFed->requestTime (i);
        std::cout << "processed time " << static_cast<double> (newTime) << "\n";
        while (mFed->hasMessage(ept))
        {
            auto nmessage = mFed->getMessage(ept);
            std::cout << "received message from " << nmessage->source << " at " << static_cast<double>(nmessage->time) << " ::" << nmessage->data.to_string() << '\n';
        }

    }
    mFed->finalize ();
    return 0;
}

