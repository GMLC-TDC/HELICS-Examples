/*
Copyright © 2017-2019,
Battelle Memorial Institute; Lawrence Livermore National Security, LLC; Alliance for Sustainable Energy, LLC.  See
the top-level NOTICE for additional details. All rights reserved.
SPDX-License-Identifier: BSD-3-Clause
*/
#include "helics/ValueFederates.hpp"
#include "helics/apps/BrokerApp.hpp"
#include "helics/core/helicsCLI11.hpp"
#include "helics/core/helics_definitions.hpp"

#include <iostream>

int main (int argc, const char * const *argv)
{
    helics::helicsCLI11App app ("Value Fed", "ValueFed");
    std::string target = "fed";
    helics::apps::BrokerApp brk;
    std::string brokerArgs = "";

    app.add_option ("--valuetarget,--target,t", target, "name of the target federate", true);
    app.add_option ("--startbroker", brokerArgs, "start a broker with the specified arguments");

    auto ret = app.helics_parse (argc, argv);

    helics::FederateInfo fi;
    if (ret == helics::helicsCLI11App::parse_output::help_call)
    {
        fi.loadInfoFromArgs ("--help");
        return 0;
    }
    else if (ret != helics::helicsCLI11App::parse_output::ok)
    {
        return -1;
    }
    fi.defName = "fed";
    fi.loadInfoFromArgs (app.remainArgs ());

    fi.setProperty(helics::defs::properties::log_level, 5);
    if (app["--startbroker"]->count () > 0)
    {
        brk = helics::apps::BrokerApp (fi.coreType, brokerArgs);
    }

    auto vFed = std::make_unique<helics::ValueFederate> (std::string{},fi);

    auto &pub = vFed->registerPublication ("pub", "double");

    auto &sub = vFed->registerSubscription(target + "/pub", "double");
    //TODO:: add optional property
    std::cout << "entering init Mode\n";
    vFed->enterInitializingMode ();
    std::cout << "entered init Mode\n";
    vFed->enterExecutingMode ();
    std::cout << "entered exec Mode\n";
    for (int i=1; i<10; ++i) {
        pub.publish(i);
        auto newTime = vFed->requestTime (i);
        if (sub.isUpdated())
        {
            auto val = sub.getValue<double>();
            std::cout << "received updated value of " << val << " at "<< newTime << " from " << vFed->getTarget(sub) << '\n';
        }

        std::cout << "processed time " << static_cast<double> (newTime) << "\n";
    }
    vFed->finalize ();
    return 0;
}

