%{
Created on 8/27/2020

This is a simple EV charge controller federate that manages the charging at
a set of charging terminals in a hypothetical EV garage. It receives periodic
SOC messages from each EV (associated with a particular charging terminal)
and sends back a message indicating whether the EV should continue charging
or not (based on whether it is full).

@author: Allison M. Campbell
allison.m.campbell@pnnl.gov
%}


%% Utility functions

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
    %   annoying errors in the broker log. Any message are tacitly disregarded.
    grantedtime = helics.helicsFederateRequestTime(fed, helics.HELICS_TIME_MAXTIME);
    status = helics.helicsFederateDisconnect(fed);
    helics.helicsFederateFree(fed);
    helics.helicsCloseLibrary();
    fprintf(fid, 'Federate finalized\n');


%% Main Program
try
    fid = fopen('Controller.log', 'w');
    %%%%%%%%%%%%%%  Registering  federate from json  %%%%%%%%%%%%%%%%%%%%%%%%%%
    fed = helics.helicsCreateMessageFederateFromConfig("ControllerConfig.json");
    federate_name = helics.helicsFederateGetName(fed);
    fprintf(fid, 'Created federate %s\n', federate_name);


%%    #### Register endpoint #####
    % Only one endpoint for the controller
    endid = helics.helicsFederateGetEndpointByIndex(fed, 0);
    end_name = helics.helicsEndpointGetName(endid);
    fprintf(fid, 'Registered Endpoint ---> %s\n', end_name);

%%    ##############  Entering Execution Mode  ##################################
    helics.helicsFederateEnterExecutingMode(fed);
    fprintf(fid, 'Entered HELICS execution mode\n');

    hours = 24*7; % one week
    total_interval = 60 * 60 * hours;
    rantedtime = 0;

    % It is common in HELICS for controllers to have slightly weird timing
    %   Generally, controllers only need to produce new control values when
    %   their inputs change. Because of this, it is common to have them
    %   request a time very far in the future (helics_time_maxtime) and
    %   when a signal arrives, they will be granted a time earlier than
    %   that, recalculate the control output and request a very late time
    %   again.


 
    starttime = helics.HELICS_TIME_MAXTIME;
    fprintf(fid, 'Requesting initial time %0.2f\n', starttime);
    grantedtime = helics.helicsFederateRequestTime(fed, starttime);
    fprintf(fid, 'Granted time %d\n', grantedtime);


    time_sim = [];
    soc = struct();

    while grantedtime < total_interval

        % In HELICS, when multiple messages arrive at an endpoint they
        % queue up and are popped off one-by-one with the
        %   "helicsEndpointHasMessage" API call. When that API doesn't
        %   return a message, you've processed them all.
        while helics.helicsEndpointHasMessage(endid):

            % Get the SOC from the EV/charging terminal in question
            msg = helics.helicsEndpointGetMessage(endid);
            currentsoc = helics.helicsMessageGetString(msg);
            source = helics.helicsMessageGetOriginalSource(msg);
            fprintf(fid, '\tReceived message from endpoint %s at time %d with SOC %0.4f\n', source, granted time, currentsoc);

            % Send back charging command based on current SOC
            %   Our very basic protocol:
            %       If the SOC is less than soc_full keep charging (send "1")
            %       Otherwise, stop charging (send "0")
            soc_full = 0.95
            if double(currentsoc) <= soc_full
                instructions = 1;
            else:
                instructions = 0;
            end
            message = num2str(instructions);
            helics.helicsEndpointSendBytesTo(endid, message, source);
            fprintf(fid, '\tSent message to endpoint %s at time %d with payload %d', source grantedtime, instructions);

            % Store SOC for later analysis/graphing
            if ~isfield(soc, source)
                soc.source = [];
            end
            soc.(source)(end+1) = double(currentsoc);
            
            if length(time_sim) > 0
                if time_sim(end) != grantedtime;
                    time_sim(end+1) = grantedtime;
                end
            else:
                ime_sim(end+1) = grantedtime;
            end
        end
        % Since we've dealt with all the messages that are queued, there's
        %   nothing else for the federate to do until/unless another
        %   message comes in. Request a time very far into the future
        %   and take a break until/unless a new message arrives.
        fprintf(fid, 'Requesting time %0.2f\n', helics.HELICS_TIME_MAXTIME);
        grantedtime = helics.helicsFederateRequestTime(fed, helics.HELICS_TIME_MAXTIME);
        fprintf(fid,'Granted time: %d\n', grantedtime);
    end
    % Close out co-simulation execution cleanly now that we're done.
    destroy_federate(fed, fid);

    % Printing out final results graphs for comparison/diagnostic purposes.
    xaxis = time_sim/3600;
    varnames = cell(5,1);
    for k=1:5
        varnames{k} = sprintf('Port %d', k);
    end
    y = array2table(cell2mat(struct2cell(soc)).', 'VariableName', varnames);
    y.x = time_sim.'/3600;

    stackedplot(y, 'XVariable', 'x', 'Title', 'SOC at each charging port', 'xlabel', 'time (hr)');
    grid();
  
    saveas(gcf, 'advanced_default_estimated_SOCs.png', 'png');
catch
    fprintf(fid, 'Something happend, closing log file\n');
    fprintf('Charger: Something happend, closing log file\n');
    fclose(fid);
end