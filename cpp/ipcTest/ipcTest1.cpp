/*

Copyright © 2017-2018,
Battelle Memorial Institute; Lawrence Livermore National Security, LLC; Alliance for Sustainable Energy, LLC
All rights reserved. See LICENSE file and DISCLAIMER for more details.
*/

#include <fstream>
#include <iomanip>
#include <iostream>
#include <random>
#include <thread>

#include <helics/ValueFederates.hpp>
#include <helics/application_api/BrokerApp.hpp>

#include "common.hpp"

// TestA will send doubles
using ValueSetter = ValuePacket<double>;

// TestB will send ints
using ValueRecver = ValuePacket<int>;

void sendPublication(ValueSetter const &vs);

int main (int, char **)
{
    constexpr unsigned num_tsteps = 10;
    const double base_time = 0.0;
    const double delta_t = 0.1;

    std::cout << "trying to create broker..." << std::endl;

    auto init_string = std::string ("-f2 --name=stevebroker");
    helics::BrokerApp broker(helics::core_type::INTERPROCESS, init_string);

    std::cout << "created broker \"" << broker->getIdentifier () << "\"\n"
              << "broker is connected: " << std::boolalpha << broker->isConnected () << std::endl;

    std::mt19937_64 gen (std::random_device{}());
    std::uniform_real_distribution<double> dist (0.0, std::nextafter (10.0, std::numeric_limits<double>::max ()));

    std::ofstream ofs ("TestA.log");

    helics::FederateInfo fed_info;
    fed_info.coreType = helics::core_type::IPC;
    fed_info.coreInitString = "--broker=stevebroker --federates 1";
    fed_info.setProperty(helics::defs::properties::time_delta, delta_t);
    fed_info.setProperty(helics::defs::properties::log_level, 5);

    helics::ValueFederate fed ("TestA Federate",fed_info);

    auto id = fed.registerGlobalPublication ("testA", "double");

    fed.enterExecutingMode ();

    for (unsigned tstep = 0; tstep < num_tsteps; ++tstep)
    {
        const double this_time = base_time + tstep * delta_t;
        const double this_value = dist (gen);

        auto thisTime = fed.requestTime (helics::Time (this_time));

        // Output to stdout
        std::cout << "welcome to timestep " << tstep << '\n'
                  << "   x(" << this_time << ") = " << this_value << '\n'
                  << "   sending...";

        // Output to log file
        ofs << std::setw (10) << std::right << this_time << std::setw (10) << std::right << this_value
            << std::endl;

        sendPublication ( ValueSetter (thisTime, id, this_value));

        std::cout << "done." << std::endl;
    }

    fed.finalize ();
	broker.waitForDisconnect();

    return 0;
}

void sendPublication (ValueSetter const &vs) { vs.pub_.publish (vs.value_); }

