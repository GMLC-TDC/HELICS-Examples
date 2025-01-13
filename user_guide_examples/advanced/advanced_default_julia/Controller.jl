# Auto-generated from Battery.py in Advanced Default example from ChatGPT 4o
# on Jan 13, 2025. As of that data, it has not been verified to work.

using PyPlot
using HELICS
using Random
using Logging

logger = global_logger(ConsoleLogger(stdout, Logging.Info))

function destroy_federate(fed)
    """
    Cleanly finalize a HELICS federate.
    """
    grantedtime = helicsFederateRequestTime(fed, HELICS_TIME_MAXTIME - 1)
    helicsFederateDisconnect(fed)
    helicsFederateFree(fed)
    helicsCloseLibrary()
    info(logger, "Federate finalized")
end

function main()
    Random.seed!(1490)

    # Registering the federate from JSON
    fed = helicsCreateMessageFederateFromConfig("ControllerConfig.json")
    federate_name = helicsFederateGetName(fed)
    info(logger, "Created federate $federate_name")

    # Register endpoint
    endid = helicsFederateGetEndpointByIndex(fed, 0)
    end_name = helicsEndpointGetName(endid)
    info(logger, "Registered Endpoint ---> $end_name")

    # Entering Execution Mode
    helicsFederateEnterExecutingMode(fed)
    info(logger, "Entered HELICS execution mode")

    hours = 24 * 7 # one week
    total_interval = 60 * 60 * hours
    grantedtime = 0
    starttime = total_interval
    grantedtime = helicsFederateRequestTime(fed, starttime)

    time_sim = Dict{String, Vector{Float64}}()
    soc = Dict{String, Vector{Float64}}()

    while grantedtime < total_interval
        while helicsEndpointHasMessage(endid)
            msg = helicsEndpointGetMessage(endid)
            currentsoc = helicsMessageGetString(msg)
            source = helicsMessageGetOriginalSource(msg)

            info(logger, "Received message from endpoint $source at time $grantedtime with SOC $currentsoc")

            # Logic to decide if charging should continue
            soc_full = 0.95
            instructions = if parse(Float64, currentsoc) <= soc_full
                1
            else
                0
            end

            message = string(instructions)
            helicsEndpointSendBytesTo(endid, message, source)

            info(logger, "Sent message to endpoint $source at time $grantedtime with payload $instructions")

            # Store SOC for analysis
            if !haskey(soc, source)
                soc[source] = Float64[]
            end
            push!(soc[source], parse(Float64, currentsoc))

            if !haskey(time_sim, source)
                time_sim[source] = Float64[]
            end
            push!(time_sim[source], float(grantedtime))
        end

        grantedtime = helicsFederateRequestTime(fed, starttime)
    end

    destroy_federate(fed)

    # Plotting
    x = [time_sim[key] for key in keys(time_sim)]
    y = [soc[key] for key in keys(soc)]

    fig, axs = subplots(5, sharex=true, sharey=true)
    fig.suptitle("SOC at each charging port")

    for i in 1:5
        axs[i].plot(x[i], y[i], color="tab:blue", linestyle="-")
        axs[i].set_yticks(0:0.5:1.25)
        axs[i].set(ylabel="Port $i")
        axs[i].grid(true)
    end

    xlabel("time (hr)")
    savefig("advanced_default_estimated_SOCs.png", format="png")
end

main()