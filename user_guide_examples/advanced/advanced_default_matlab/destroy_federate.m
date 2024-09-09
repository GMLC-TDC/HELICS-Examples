function destroy_federate(fed, fid)
    %{
    As part of ending a HELICS co-simulation it is good housekeeping to
    formally destroy a federate. Doing so informs the rest of the
    federation that it is no longer a part of the co-simulation and they
    should proceed without it (if applicable). Generally this is done
    when the co-simulation is complete and all federates end execution
    at more or less the same wall-clock time.

    :param fed: Federate to be destroyed
    :return: (none)
    %}

    % Adding extra time request to clear out any pending messages to avoid
    % annoying errors in the broker log. Any message are tacitly disregarded.
    grantedtime = helics.helicsFederateRequestTime(fed, getHelicsMaxTime());
    helics.helicsFederateDisconnect(fed);
    helics.helicsFederateFree(fed);
    helics.helicsCloseLibrary();
    fprintf(fid, 'Federate finalized\n');
end