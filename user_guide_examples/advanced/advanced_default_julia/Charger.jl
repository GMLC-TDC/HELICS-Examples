# Auto-generated from Battery.py in Advanced Default example from ChatGPT 4o
# on Jan 13, 2025. As of that data, it has not been verified to work.

using PyPlot
using HELICS
using Random
using Logging

logger = global_logger(ConsoleLogger(stdout, Logging.Info))

function destroy_federate(fed)
    """
    Cleanup for a HELICS co-simulation federate.
    """
    grantedtime = helicsFederateRequestTime(fed, HELICS_TIME_MAXTIME - 1)
    status = helicsFederateDisconnect(fed)
    helicsFederateFree(fed)
    helicsCloseLibrary()
    info(logger, "Federate finalized")
end

function get_new_EV(numEVs)
    """
    Generates a distribution of EVs with different charging level capabilities.
    """
    # Probabilities for each charging level
    lvl1 = 0.05
    lvl2 = 0.6
    lvl3 = 0.35

    listOfEVs = rand([1, 2, 3], numEVs, [lvl1, lvl2, lvl3])
    numLvl1 = count(x -> x == 1, listOfEVs)
    numLvl2 = count(x -> x == 2, listOfEVs)
    numLvl3 = count(x -> x == 3, listOfEVs)

    return numLvl1, numLvl2, numLvl3, listOfEVs
end

function calc_charging_voltage(EV_list)
    """
    Maps charging levels to standard charging voltages.
    """
    charge_voltages = [120, 240, 630]
    return [charge_voltages[ev] for ev in EV_list]
end

function estimate_SOC(charging_V, charging_A)
    """
    Estimates SOC based on charging voltage and current with noise.
    """
    socs = [0.0, 1.0]
    effective_R = [8.0, 150.0]
    noise = rand(Normal(0, 0.2))
    measured_A = charging_A + noise
    measured_R = charging_V / measured_A
    SOC_estimate = interp(measured_R, effective_R, socs)
    return SOC_estimate
end

function main()
    Random.seed!(1490)

    # Registering the federate from JSON
    fed = helicsCreateCombinationFederateFromConfig("ChargerConfig.json")
    federate_name = helicsFederateGetName(fed)

    info(logger, "Created federate $federate_name")
    println("Created federate $federate_name")

    end_count = helicsFederateGetEndpointCount(fed)
    sub_count = helicsFederateGetInputCount(fed)
    pub_count = helicsFederateGetPublicationCount(fed)

    info(logger, "\tNumber of endpoints: $end_count")
    info(logger, "\tNumber of subscriptions: $sub_count")
    info(logger, "\tNumber of publications: $pub_count")

    println("\tNumber of endpoints: $end_count")
    println("\tNumber of subscriptions: $sub_count")
    println("\tNumber of publications: $pub_count")

    # Diagnostics for JSON config
    endid = Dict{Int, Nullable{helics_endpoint}}()
    for i in 1:end_count
        endid[i] = helicsFederateGetEndpointByIndex(fed, i - 1)
    end

    subid = Dict{Int, Nullable{helics_input}}()
    for i in 1:sub_count
        subid[i] = helicsFederateGetInputByIndex(fed, i - 1)
    end

    pubid = Dict{Int, Nullable{helics_publication}}()
    for i in 1:pub_count
        pubid[i] = helicsFederateGetPublicationByIndex(fed, i - 1)
    end

    # Entering Execution Mode
    helicsFederateEnterExecutingMode(fed)
    info(logger, "Entered HELICS execution mode")

    # Charging power level (kW) for levels 1, 2, 3
    charge_rate = [1.8, 7.2, 50]
    hours = 24 * 7 # one week
    total_interval = 60 * 60 * hours
    update_interval = helicsFederateGetTimeProperty(fed, HELICS_PROPERTY_TIME_PERIOD)
    grantedtime = 0

    # Initial fleet of EVs
    numLvl1, numLvl2, numLvl3, EVlist = get_new_EV(end_count)
    charging_voltage = calc_charging_voltage(EVlist)
    currentsoc = Dict{Int, Float64}()

    # Data collection
    time_sim = Float64[]
    power = Float64[]
    charging_current = Dict{Int, Float64}()

    # Blocking call for a time request at simulation time 0
    initial_time = 60
    grantedtime = helicsFederateRequestTime(fed, initial_time)

    # Apply initial charging voltage
    for j in 1:pub_count
        helicsPublicationPublishDouble(pubid[j][], charging_voltage[j])
    end

    # Main loop
    while grantedtime < total_interval
        requested_time = grantedtime + update_interval
        grantedtime = helicsFederateRequestTime(fed, requested_time)

        for j in 1:end_count
            charging_current[j] = helicsInputGetDouble(subid[j][])
            
            if charging_current[j] == 0
                _, _, _, newEVtype = get_new_EV(1)
                EVlist[j] = newEVtype[1]
                charge_V = calc_charging_voltage(newEVtype)
                charging_voltage[j] = charge_V[1]
                currentsoc[j] = 0.0
            else
                currentsoc[j] = estimate_SOC(charging_voltage[j], charging_current[j])
            end

            endpoint_name = helicsEndpointGetName(endid[j][])
            if helicsEndpointHasMessage(endid[j][])
                msg = helicsEndpointGetMessage(endid[j][])
                instructions = helicsMessageGetString(msg)
                source = helicsMessageGetOriginalSource(msg)

                if parse(Int, instructions) == 0
                    charging_voltage[j] = 0
                    info(logger, "EV full; removing charging voltage")
                end
            end

            helicsPublicationPublishDouble(pubid[j][], charging_voltage[j])

            if grantedtime % 900 == 0
                destination_name = helicsEndpointGetDefaultDestination(endid[j][])
                message = string(currentsoc[j])
                helicsEndpointSendBytes(endid[j][], message)
            end
        end

        total_power = 0.0
        for j in 1:pub_count
            charging_power = charge_rate[EVlist[j]]
            total_power += charging_voltage[j] * charging_current[j]
        end

        push!(time_sim, grantedtime)
        push!(power, total_power)
    end

    destroy_federate(fed)

    xaxis = time_sim / 3600
    yaxis = power

    plot(xaxis, yaxis, color="tab:blue", linestyle="-")
    yticks(0:1000:25000)
    ylabel("kW")
    grid(true)
    xlabel("time (hr)")
    title("Instantaneous Power Draw from 5 EVs")
    savefig("advanced_default_charging_power.png", format="png")
    show()
end

main()