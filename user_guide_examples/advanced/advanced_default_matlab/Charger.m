
%{
Created on 9/15/2020

This is a simple EV federate that models a set of EV terminals in an
EV charging garage. Each terminal can support charging at levels 1, 2,
and 3 but the EVs that come to charge have a randomly assigned charging
level.

Managing these terminals is a centralized EV Controller that receives from
the EV the current SOC and sends a command back to the terminal to continue
charging or stop charging (once the EV is full). Once an EV is full, a new
EV is moved into the charging terminal (with a randomly assigned charging
level) and begins charging.

@author: Allison M. Campbell, Trevor Hardy
allison.m.campbell@pnnl.gov, trevor.hardy@pnnl.gov
%}


%% Main Program
rng(1490);
try
    fid = fopen('Charger.log', 'w');
    %%%%%%%%%%%%%  Registering  federate from json  %%%%%%%%%%%%%%%%%%%%%
    fed = helics.helicsCreateCombinationFederateFromConfig('ChargerConfig.json');
    federate_name = helics.helicsFederateGetName(fed);
    fprintf(fid, 'Created federate %s\n', federate_name);
    end_count = helics.helicsFederateGetEndpointCount(fed);
    fprintf(fid, '\tNumber of endpoints: %d\n', end_count);
    sub_count = helics.helicsFederateGetInputCount(fed);
    fprintf(fid, '\tNumber of subscriptions: %d\n', sub_count);
    pub_count = helics.helicsFederateGetPublicationCount(fed);
    fprintf(fid, '\tNumber of publications: %d\n', pub_count);
    fprintf('Created federate %s\n', federate_name);
    fprintf('\tNumber of endpoints: %d\n', end_count);
    fprintf('\tNumber of subscriptions: %d\n', sub_count);
    fprintf('\tNumber of publications: %d\n', pub_count);

    % Diagnostics to confirm JSON config correctly added the required
    %   endpoints, publications, and subscriptions.
    endid = {};
    for i=1:end_count
        endid{i} = helics.helicsFederateGetEndpointByIndex(fed, i-1);
        end_name = helics.helicsEndpointGetName(endid{i});
        fprintf(fid,'\tRegistered Endpoint ---> %s\n', end_name);
    end
    subid = {};
    for i=1:sub_count
        subid{i} = helics.helicsFederateGetInputByIndex(fed, i-1);
        sub_name = helics.helicsSubscriptionGetTarget(subid{i});
        fprintf(fid,'\tRegistered subscription---> %s\n', sub_name);
    end
    pubid = {};
    for i=1:pub_count
        pubid{i} = helics.helicsFederateGetPublicationByIndex(fed, i-1);
        pub_name = helics.helicsPublicationGetName(pubid{i});
        fprintf(fid,'\tRegistered publication---> %s\n', pub_name);
    end

%%   ##############  Entering Execution Mode  ##################################
    helics.helicsFederateEnterExecutingMode(fed);
    fprintf(fid, 'Entered HELICS execution mode\n');

    % Definition of charging power level (in kW) for level 1, 2, 3 chargers
    charge_rate = [1.8,7.2,50];


    hours = 24*7; % one week
    total_interval = 60 * 60 * hours;
    update_interval = helics.helicsFederateGetTimeProperty(fed, helics.HelicsProperties.HELICS_PROPERTY_TIME_PERIOD);
    grantedtime = 0;

    % Generate an initial fleet of EVs, one for each previously defined
    %   endpoint. This gives each EV a unique link to the EV controller
    %   federate.
    [~,~,~,EVlist] = get_new_EV(end_count);
    charging_voltage = calc_charging_voltage(EVlist);
    currentsoc = [];

    % Data collection lists
    time_sim = [];
    power = [];
    charging_current = [];

    % Blocking call for a time request at simulation time 0
    initial_time = 60;
    fprintf(fid, 'Requesting initial time %d\n', initial_time);
    grantedtime = helics.helicsFederateRequestTime(fed, initial_time);
    fprintf(fid,'Granted time %d\n', grantedtime);


    % Apply initial charging voltage
    for j=1:pub_count
        helics.helicsPublicationPublishDouble(pubid{j}, charging_voltage(j));
        fprintf(fid,'\tPublishing charging voltage of %0.2f at time %d\n', charging_voltage(j), grantedtime);
    end

%%    ########## Main co-simulation loop ########################################
    % As long as granted time is in the time range to be simulated...
    while grantedtime < total_interval

        % Time request for the next physical interval to be simulated
        requested_time = grantedtime + update_interval;
        fprintf(fid,'Requesting time %d\n', requested_time);
        grantedtime = helics.helicsFederateRequestTime(fed, requested_time);
        fprintf(fid,'Granted time %d\n', grantedtime);

        for j=1:end_count

            fprintf(fid,'EV %d time %d', j, grantedtime);
            % Model the physics of the battery charging. This happens
            %   every time step whether a message comes in or not and always
            %   uses the latest value provided by the battery model.
            charging_current(j) = helics.helicsInputGetDouble(subid{j});
            fprintf(fid,'\tCharging current: %0.2f  from input %s\n', charging_current(j), helics.helicsSubscriptionGetTarget(subid{j}));

            % New EV is in place after removing charge from old EV,
            % as indicated by the zero current draw.
            if charging_current(j) == 0
                [~, ~, ~, newEVtype] = get_new_EV(1);
                EVlist(j) = newEVtype;
                charge_V = calc_charging_voltage(newEVtype);
                charging_voltage(j) = charge_V;

                currentsoc(j) = 0; % Initial SOC estimate
                fprintf(fid,'\tNew EV, SOC estimate: %0.4f\n', currentsoc(j));
                fprintf(fid,'\tNew EV, charging voltage: %0.2f\n', charging_voltage(j));
            else
                % SOC estimation
                currentsoc(j) = estimate_SOC(charging_voltage(j), charging_current(j));
                fprintf(fid,'\tEV SOC estimate: %0.4f\n', currentsoc(j));
            end


            % Check for messages from EV Controller
            endpoint_name = helics.helicsEndpointGetName(endid{j});
            if helics.helicsEndpointHasMessage(endid{j})
                msg = helics.helicsEndpointGetMessage(endid{j});
                instructions = helics.helicsMessageGetString(msg);
                source = helics.helicsMessageGetOriginalSource(msg);
                fprintf(fid, '\tReceived message at endpoint %s, from source %s at time %d with command %s', endpoint_name, source, grantedtime, instructions);

                % Update charging state based on message from controller
                % The protocol used by the EV and the EV Controller is simple:
                %       EV Controller sends "1" - keep charging
                %       EV Controller sends anything else: stop charging
                % The default state is charging (1) so we only need to
                %   do something if the controller says to stop
                if str2num(instructions) == 0
                    % Stop charing this EV
                    charging_voltage(j) = 0;
                    fprintf(fid, '\tEV full; removing charging voltage\n');
                end
            else
                fprintf(fid, '\tNo messages at endpoint %s recieved at time %d\n', endpoint_name, grantedtime);
            end

            % Publish updated charging voltage
            helics.helicsPublicationPublishDouble(pubid{j}, charging_voltage(j))
            fprintf(fid, '\tPublishing charging voltage of %0.2f at time %d\n', charging_voltage(j), grantedtime);

            % Send message to Controller with SOC every 15 minutes
            if mod(grantedtime,900) == 0
                destination_name = sprintf('%s', helics.helicsEndpointGetDefaultDestination(endid{j}));
                message = sprintf('%0.4f', currentsoc(j));
                helics.helicsEndpointSendBytes(endid{j}, message);
                fprintf(fid, 'Sent message from endpoint %s to destination %s at time %d with payload SOC %s\n', endpoint_name,destination_name, grantedtime, message);
            end
        end
        % Calculate the total power required by all chargers. This is the
        %   primary metric of interest, to understand the power profile
        %   and capacity requirements required for this charging garage.
        total_power = charging_voltage * charging_current.';
        % Data collection vectors
        time_sim(end+1) = grantedtime;
        power(end+1) = total_power;


    end
    % Cleaning up HELICS stuff once we've finished the co-simulation.
    destroy_federate(fed, fid);

    % Output graph showing the charging profile for each of the charging
    %   terminals
    xaxis = time_sim/3600;
    yaxis = power;
    plot(xaxis, yaxis);
    yticks(0:1000:25000);
    ylabel('kW');
    grid();
    xlabel('time (hr)');
    title('Instantaneous Power Draw from 5 EVs');
    % Saving graph to file
    saveas(gcf, 'advanced_default_charging_power.png', 'png');
catch ME
    fprintf(fid, 'Something happend, closing log file\n');
    fprintf('Charger: Something happend, closing log file\n');
    fclose(fid);
    rethrow(ME);
end