/* Auto-generated from Battery.py in Advanced Default example using ChatGPT 4o
 on Jan 13, 2025. No attempt to compile or run this code has been made.
*/


#include <iostream>
#include <vector>
#include <map>
#include <ctime>
#include <cstdlib>
#include "helics.h"

// Randomly assigns charging levels to the EVs
void get_new_EV(int numEVs, int &numLvl1, int &numLvl2, int &numLvl3, std::vector<int> &listOfEVs) {
    listOfEVs.clear();
    numLvl1 = numLvl2 = numLvl3 = 0;
    double lvl1 = 0.05, lvl2 = 0.6, lvl3 = 0.35;
    
    for (int i = 0; i < numEVs; ++i) {
        double r = static_cast<double>(rand()) / RAND_MAX;
        if (r < lvl1) {
            listOfEVs.push_back(1);
            ++numLvl1;
        } else if (r < lvl1 + lvl2) {
            listOfEVs.push_back(2);
            ++numLvl2;
        } else {
            listOfEVs.push_back(3);
            ++numLvl3;
        }
    }
}

// Determine charging voltage based on EV charging level
std::vector<int> calc_charging_voltage(const std::vector<int>& EV_list) {
    std::vector<int> charging_voltage;
    int charge_voltages[] = {120, 240, 630};

    for (int i = 0; i < EV_list.size(); ++i) {
        charging_voltage.push_back(charge_voltages[EV_list[i] - 1]);
    }
    
    return charging_voltage;
}

// Estimate the SOC based on measured values and add some noise
double estimate_SOC(double charging_V, double charging_A) {
    double socs[] = {0.0, 1.0};
    double effective_R[] = {8.0, 150.0};
    double mu = 0.0, sigma = 0.2;
    double noise = ((rand() % 100 - 50) / 50.0) * sigma;  // Rough Gaussian
    double measured_A = charging_A + noise;
    double measured_R = charging_V / measured_A;
    double SOC_estimate = (measured_R - effective_R[0]) / (effective_R[1] - effective_R[0]); // Linear interpolation
    
    return SOC_estimate >= 0 ? (SOC_estimate <= 1 ? SOC_estimate : 1) : 0;
}

void destroy_federate(HelicsFederate* fed) {
    helicsFederateRequestTime(fed, helics_time_max_time - 1);
    helicsFederateDisconnect(fed);
    helicsFederateFree(fed);
    helicsCloseLibrary();
    std::cout << "Federate finalized" << std::endl;
}

int main() {
    srand(1490);  // Seed random generator

    HelicsFederateInfo fedinfo = helicsCreateFederateInfo();
    HelicsFederate* fed = helicsCreateCombinationFederateFromConfig("ChargerConfig.json", &fedinfo);

    const char* federate_name = helicsFederateGetName(fed);
    std::cout << "Created federate " << federate_name << std::endl;

    int end_count = helicsFederateGetEndpointCount(fed);
    int sub_count = helicsFederateGetInputCount(fed);
    int pub_count = helicsFederateGetPublicationCount(fed);

    std::cout << "Number of endpoints: " << end_count << std::endl;
    std::cout << "Number of subscriptions: " << sub_count << std::endl;
    std::cout << "Number of publications: " << pub_count << std::endl;

    helicsFederateEnterExecutingMode(fed);
    const double charge_rate[] = {1.8, 7.2, 50.0};

    double total_interval = 60 * 60 * 24 * 7;  // One week
    double update_interval = helicsFederateGetTimeProperty(fed, helics_property_time_period);
    double grantedtime = 0.0;

    // Initial EV fleet generation
    int numLvl1, numLvl2, numLvl3;
    std::vector<int> EVlist;
    get_new_EV(end_count, numLvl1, numLvl2, numLvl3, EVlist);
    std::vector<int> charging_voltage = calc_charging_voltage(EVlist);
    std::map<int, double> currentsoc;
    std::vector<int> time_sim;
    std::vector<double> power;
    std::map<int, double> charging_current;

    // Initial time request
    grantedtime = helicsFederateRequestTime(fed, 60);

    // Apply initial charging voltage
    for (int j = 0; j < pub_count; ++j) {
        helicsPublicationPublishDouble(helicsFederateGetPublicationByIndex(fed, j), charging_voltage[j]);
    }

    while (grantedtime < total_interval) {
        double requested_time = grantedtime + update_interval;
        grantedtime = helicsFederateRequestTime(fed, requested_time);

        for (int j = 0; j < end_count; ++j) {
            HelicsInput input = helicsFederateGetInputByIndex(fed, j);
            charging_current[j] = helicsInputGetDouble(input);

            if (charging_current[j] == 0) {
                std::vector<int> newEVtype;
                get_new_EV(1, numLvl1, numLvl2, numLvl3, newEVtype);
                EVlist[j] = newEVtype[0];
                std::vector<int> charge_V = calc_charging_voltage(newEVtype);
                charging_voltage[j] = charge_V[0];
                currentsoc[j] = 0.0;
            } else {
                currentsoc[j] = estimate_SOC(charging_voltage[j], charging_current[j]);
            }

            HelicsEndpoint endpoint = helicsFederateGetEndpointByIndex(fed, j);
            if (helicsEndpointHasMessage(endpoint)) {
                HelicsMessage msg = helicsEndpointGetMessage(endpoint);
                const char* instructions = helicsMessageGetString(msg);
                if (atoi(instructions) == 0) {
                    charging_voltage[j] = 0;
                }
            }

            helicsPublicationPublishDouble(helicsFederateGetPublicationByIndex(fed, j), charging_voltage[j]);
        }

        double total_power = 0.0;
        for (int j = 0; j < pub_count; ++j) {
            total_power += charging_voltage[j] * charging_current[j];
        }

        time_sim.push_back(grantedtime);
        power.push_back(total_power);
    }

    destroy_federate(fed);
    return 0;
}