/* Auto-generated from Battery.py in Advanced Default example using ChatGPT 4o
 on Jan 13, 2025. No attempt to compile or run this code has been made.
*/

#include <iostream>
#include <vector>
#include <map>
#include <string>
#include <ctime>
#include <cstdlib>
#include "helics.h"

// This function is just a placeholder for actually sending and receiving messages within HELICS
std::string helicsMessageReceiveLogic(double grantedtime, const std::string& currentsoc, HelicsEndpoint& endid, const char* source) {
    double soc_full = 0.95;
    int instructions;

    if (std::atof(currentsoc.c_str()) <= soc_full) {
        instructions = 1;  // Keep charging
    } else {
        instructions = 0;  // Stop charging
    }
    std::string message = std::to_string(instructions);
    helicsEndpointSendBytesTo(endid, message.c_str(), message.size(), source, nullptr);
    std::cout << "\tSent message to endpoint " << source << " at time " << grantedtime << " with payload " << instructions << std::endl;
    return message;
}

void destroy_federate(HelicsFederate* fed) {
    helicsFederateRequestTime(fed, helics_time_max_time - 1);
    helicsFederateDisconnect(fed);
    helicsFederateFree(fed);
    helicsCloseLibrary();
    std::cout << "Federate finalized" << std::endl;
}

int main() {
    srand(1490);  // Seed random number generator for any potential randomness

    // Create and configure the federate
    HelicsFederateInfo fedinfo = helicsCreateFederateInfo();
    HelicsFederate* fed = helicsCreateMessageFederateFromConfig("ControllerConfig.json", &fedinfo);

    const char* federate_name = helicsFederateGetName(fed);
    std::cout << "Created federate " << federate_name << std::endl;

    HelicsEndpoint endid = helicsFederateGetEndpointByIndex(fed, 0);
    const char* end_name = helicsEndpointGetName(endid);
    std::cout << "Registered Endpoint ---> " << end_name << std::endl;

    helicsFederateEnterExecutingMode(fed);
    std::cout << "Entered HELICS execution mode" << std::endl;

    double total_interval = 60 * 60 * 24 * 7;  // One week
    double grantedtime = 0.0;
    double starttime = total_interval;

    std::map<std::string, std::vector<double>> time_sim;
    std::map<std::string, std::vector<double>> soc;

    grantedtime = helicsFederateRequestTime(fed, starttime);
    std::cout << "Granted time " << grantedtime << std::endl;

    while (grantedtime < total_interval) {
        while (helicsEndpointHasMessage(endid) == helics_true) {
            HelicsMessage msg = helicsEndpointGetMessage(endid);
            const char* currentsoc = helicsMessageGetString(msg);
            const char* source = helicsMessageGetOriginalSource(msg);
            std::cout << "\tReceived message from endpoint " << source << " at time " << grantedtime << " with SOC " << currentsoc << std::endl;

            std::string message = helicsMessageReceiveLogic(grantedtime, currentsoc, endid, source);

            std::string source_str(source);
            if (soc.find(source_str) == soc.end()) {
                soc[source_str] = std::vector<double>();
            }
            soc[source_str].push_back(std::atof(currentsoc));

            if (time_sim.find(source_str) == time_sim.end()) {
                time_sim[source_str] = std::vector<double>();
            }
            time_sim[source_str].push_back(grantedtime);
        }
        grantedtime = helicsFederateRequestTime(fed, starttime);
        std::cout << "Granted time: " << grantedtime << std::endl;
    }

    destroy_federate(fed);

    // Note: Plotting functionality is not provided in this code. You might consider using a third-party library
    // or create a separate tool for visualization, such as outputting to CSV for later graph generation.
    
    return 0;
}