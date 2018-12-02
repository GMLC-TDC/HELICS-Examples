/*

Copyright © 2017-2018,
Battelle Memorial Institute; Lawrence Livermore National Security, LLC; Alliance for Sustainable Energy, LLC
All rights reserved. See LICENSE file and DISCLAIMER for more details.
*/
#include <fstream>
#include <iomanip>
#include <iostream>
#include <random>

#include <helics/ValueFederates.hpp>
#include <helics/core/BrokerFactory.hpp>

#include "common.hpp"

// TestA will send doubles
using ValueSetter = ValuePacket<double>;

// TestB will send ints
using ValueRecver = ValuePacket<int>;

void sendPublication ( ValueSetter const &vs);

void break_on_me (void) {}

int main (int, char **)
{
    std::ofstream ofs ("TestB.log");
    helics::Time stopTime = helics::Time (0.9);

    helics::FederateInfo fed_info;
    fed_info.coreType = helics::core_type::IPC;
    fed_info.coreInitString = "--broker=stevebroker --federates 1 --loglevel 5";
	fed_info.setTimeProperty(helics::defs::properties::time_delta, 0.1);
	fed_info.setIntegerProperty(helics::defs::properties::log_level, 5);
	fed_info.setFlagOption(helics::defs::flags::observer, false);

    std::cout << "Creating federate." << std::endl;
    helics::ValueFederate fed ("TestB Federate",fed_info);
    std::cout << "Done creating federate." << std::endl;

    // Subscribe to testA's publications
    auto &sub = fed.registerSubscription ("testA");

    fed.enterExecutingMode ();

    break_on_me ();

    std::cout << "Updated? " << std::boolalpha << sub.isUpdated() << std::endl;

    unsigned tstep = 0;
    for (;;)
    {
        auto time = fed.requestTime (stopTime);
        std::cout << "at time " << time << std::endl;
        if (time <= stopTime)
        {
            if (sub.isUpdated ())
            {
                auto this_value = sub.getValue<double> ();
                std::cout << "welcome to timestep " << ++tstep << '\n'
                          << "   x(" << time << ") = " << this_value << std::endl;

                ofs << std::setw (10) << std::right << time << std::setw (10) << std::right << this_value
                    << std::endl;
            }
        }
        else
            break;
    }

    fed.finalize ();
    return 0;
}

void sendPublication ( ValueSetter const &vs) { vs.pub_.publish (vs.value_); }

