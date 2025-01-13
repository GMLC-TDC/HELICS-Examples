/* Auto-generated from Battery.py in Advanced Default example using ChatGPT 4o
 on Jan 13, 2025. No attempt to compile or run this code has been made.
*/


#include <iostream>
#include <vector>
#include <map>
#include <ctime>
#include <cstdlib>
#include "helics.hpp"

// Emulate numpy's choice function for selecting battery sizes
std::vector<int> get_new_battery(int numBattery) {
    std::vector<int> batterySizes = {25, 62, 100};
    std::vector<double> probabilities = {0.2, 0.2, 0.6};
    std::vector<int> listOfBatts(numBattery);
    
    for (int i = 0; i < numBattery; ++i) {
        double r = (double)rand() / RAND_MAX;
        double cumulative = 0.0;
        for (int j = 0; j < batterySizes.size(); ++j) {
            cumulative += probabilities[j];
            if (r <= cumulative) {
                listOfBatts[i] = batterySizes[j];
                break;
            }
        }
    }
    return listOfBatts;
}

void destroy_federate(HelicsFederate* fed) {
    helicsFederateRequestTime(fed, helics_time_max_time);
    helicsFederateDisconnect(fed);
    helicsFederateDestroy(fed);
    std::cout << "Federate finalized" << std::endl;
}

int main() {
    srand(2608); // Seed for random number generation

    helics_instance_t instance = helicsCreateInstance();
    HelicsFederateInfo fedinfo = helicsCreateFederateInfo();
    HelicsFederate* fed = helicsCreateValueFederateFromConfig("BatteryConfig.json", &fedinfo);
    const char* federate_name = helicsFederateGetName(fed);
    std::cout << "Created federate " << federate_name << std::endl;

    int sub_count = helicsFederateGetInputCount(fed);
    int pub_count = helicsFederateGetPublicationCount(fed);

    std::map<int, HelicsInput> subid;
    std::map<int, const char*> sub_name;
    for (int i = 0; i < sub_count; ++i) {
        subid[i] = helicsFederateGetInputByIndex(fed, i);
        sub_name[i] = helicsInputGetTarget(subid[i]);
    }

    std::map<int, HelicsPublication> pubid;
    std::map<int, const char*> pub_name;
    for (int i = 0; i < pub_count; ++i) {
        pubid[i] = helicsFederateGetPublicationByIndex(fed, i);
        pub_name[i] = helicsPublicationGetName(pubid[i]);
    }

    helicsFederateEnterExecutingMode(fed);

    int hours = 24 * 7; // one week
    int total_interval = 60 * 60 * hours;
    int update_interval = helicsFederateGetTimeProperty(fed, helics_property_time_period);
    double grantedtime = 0.0;

    // Define battery physics as empirical values
    double socs[] = {0.0, 1.0};
    double effective_R[] = {8.0, 150.0};

    std::vector<int> batt_list = get_new_battery(pub_count);
    std::map<int, double> current_soc;
    for (int i = 0; i < pub_count; ++i) {
        current_soc[i] = (rand() % 60) / 100.0;
    }

    std::vector<int> time_sim;
    std::vector<double> current;
    std::map<int, std::vector<double>> soc;

    while (grantedtime < total_interval) {
        double requested_time = grantedtime + update_interval;
        grantedtime = helicsFederateRequestTime(fed, requested_time);

        for (int j = 0; j < sub_count; ++j) {
            double charging_voltage = helicsInputGetDouble(subid[j]);

            if (charging_voltage == 0) {
                std::vector<int> new_batt = get_new_battery(1);
                batt_list[j] = new_batt[0];
                current_soc[j] = (rand() % 80) / 100.0;
            } else {
                double R =  ((1.0 - current_soc[j]) * effective_R[0] + current_soc[j] * effective_R[1]);
                double charging_current = charging_voltage / R;
                double added_energy = (charging_current * charging_voltage * update_interval / 3600.0) / 1000.0;
                current_soc[j] += added_energy / batt_list[j];

                helicsPublicationPublishDouble(pubid[j], charging_current);

                if (soc.find(j) == soc.end()) {
                    soc[j] = std::vector<double>();
                }
                soc[j].push_back(current_soc[j]);
            }
        }
        time_sim.push_back(grantedtime);
        // Might need to track charging_current for each battery. 
        // Would need additional logic to store properly.
    }

    destroy_federate(fed);

    // Note: Plotting functionality is not provided. You might consider using a third-party library or create a separate tool for visualization, such as via CSV export.
    return 0;
}
