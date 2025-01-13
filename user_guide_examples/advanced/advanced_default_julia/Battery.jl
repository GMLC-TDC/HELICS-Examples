# Auto-generated from Battery.py in Advanced Default example from ChatGPT 4o
# on Jan 13, 2025. As of that data, it has not been verified to work.

using PyPlot
using HELICS
using Random
using Logging

const logger = global_logger(ConsoleLogger(stdout, Logging.Info))

function destroy_federate(fed)
    """
    As part of ending a HELICS co-simulation it is good housekeeping to
    formally destroy a federate.
    """
    # Adding extra time request to clear out any pending messages
    grantedtime = helicsFederateRequestTime(fed, HELICS_TIME_MAXTIME - 1)
    status = helicsFederateDisconnect(fed)
    helicsFederateDestroy(fed)
    info(logger, "Federate finalized")
end

function get_new_battery(numBattery)
    """
    Generate a list of battery capacities based on defined probabilities.
    """
    size_1 = 0.2
    size_2 = 0.2
    size_3 = 0.6
    listOfBatts = rand([25, 62, 100], numBattery, [size_1, size_2, size_3])
    return listOfBatts
end

function main()
    Random.seed!(2608)

    # Registering federate and configuring from JSON
    fed = helicsCreateValueFederateFromConfig("BatteryConfig.json")
    federate_name = helicsFederateGetName(fed)
    info(logger, "Created federate $federate_name")
    println("Created federate $federate_name")

    sub_count = helicsFederateGetInputCount(fed)
    pub_count = helicsFederateGetPublicationCount(fed)

    # Diagnostics for JSON config
    subid = Dict{Int, Nullable{helics_input}}()
    sub_name = Dict{Int, String}()
    for i in 0:(sub_count-1)
        subid[i] = helicsFederateGetInputByIndex(fed, i)
        sub_name[i] = helicsInputGetTarget(subid[i][])
    end

    pubid = Dict{Int, Nullable{helics_publication}}()
    pub_name = Dict{Int, String}()
    for i in 0:(pub_count-1)
        pubid[i] = helicsFederateGetPublicationByIndex(fed, i)
        pub_name[i] = helicsPublicationGetName(pubid[i][])
    end

    # Entering Execution Mode
    helicsFederateEnterExecutingMode(fed)
    info(logger, "Entered HELICS execution mode")

    hours = 24*7 # one week
    total_interval = Int(60 * 60 * hours)
    update_interval = helicsFederateGetTimeProperty(fed, HELICS_PROPERTY_TIME_PERIOD)
    grantedtime = 0

    # Define battery physics as empirical values
    socs = [0, 1]
    effective_R = [8, 150]
    
    batt_list = get_new_battery(pub_count)
    current_soc = Dict{Int, Float64}()
    for i in 1:pub_count
        current_soc[i] = rand(0.0:0.01:0.6)
    end

    # Data collection lists
    time_sim = Float64[]
    current = Float64[]
    soc = Dict{Int, Vector{Float64}}()

    # Main simulation loop
    while grantedtime < total_interval
        # Time request for the next interval
        requested_time = grantedtime + update_interval
        grantedtime = helicsFederateRequestTime(fed, requested_time)

        for j in 1:sub_count
            charging_voltage = helicsInputGetDouble(subid[j])
            if charging_voltage == 0
                new_batt = get_new_battery(1)
                batt_list[j] = new_batt[1]
                current_soc[j] = rand(0.0:0.01:0.8)
                charging_current = 0.0
            else
                R = interp(current_soc[j], socs, effective_R)
                charging_current = charging_voltage / R
                added_energy = (charging_current * charging_voltage * update_interval / 3600) / 1000
                current_soc[j] += added_energy / batt_list[j]
            end
            helicsPublicationPublishDouble(pubid[j], charging_current)

            # Store SOC for later analysis/graphing
            if !haskey(soc, j)
                soc[j] = Float64[]
            end
            push!(soc[j], current_soc[j])
        end

        # Data collection
        push!(time_sim, grantedtime)
        push!(current, charging_current)
    end

    destroy_federate(fed)

    # Plotting results
    xaxis = time_sim / 3600
    fig, axs = subplots(5; sharex=true, sharey=true)
    fig.suptitle("SOC of each EV Battery")
    for i in 1:5
        axs[i].plot(xaxis, soc[i], color="tab:blue", linestyle="-")
        axs[i].set_yticks(0:0.5:1.25)
        axs[i].set(ylabel="Batt at\nport $i")
        axs[i].grid(true)
    end

    xlabel("time (hr)")
    savefig("advanced_default_battery_SOCs.png", format="png")
    show()
end

main()