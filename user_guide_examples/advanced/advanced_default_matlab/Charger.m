# -*- coding: utf-8 -*-
"""
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
"""
%% Utility Functions

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
end

function [numLvl1,numLvl2,numLvl3,listOfEVs] = get_new_EV(numEVs)
    %{
    Using hard-coded probabilities, a distribution of EVs with support
    for specific charging levels are generated. The number of EVs
    generated is defined by the user.

    :param numEVs: Number of EVs
    :return
        numLvL1: Number of new EVs that will charge at level 1
        numLvL2: Number of new EVs that will charge at level 2
        numLvL3: Number of new EVs that will charge at level 3
        listOfEVs: List of all EVs (and their charging levels) generated

    %}

    % Probabilities of a new EV charging at the specified level.
    lvl1 = 0.05;
    lvl2 = 0.6;
    lvl3 = 0.35;
    listOfEVs = randsample([1,2,3],numEVs,true,[lvl1,lvl2,lvl3]);
    numLvl1 = sum(listOfEVs == 1);
    numLvl2 = sum(listOfEVs == 2);
    numLvl3 = sum(listOfEVs == 3);

end



function charging_voltage = calc_charging_voltage(EV_list)
    %{
    This function uses the pre-defined charging powers and maps them to
    standard (more or less) charging voltages. This allows the charger
    to apply an appropriately modeled voltage to the EV based on the
    charging power level

    :param EV_list: Value of "1", "2", or "3" to indicate charging level
    :return: charging_voltage: List of charging voltages corresponding
            to the charging power.
    %}

    % Ignoring the difference between AC and DC voltages for this application
    charge_voltages = [120, 240, 630];
    charging_voltage = charge_voltages * [EV_List == [1,2,3].'];

end

function SOC_estimate = estimate_SOC(charging_V, charging_A)
    %{
    The charger has no direct knowledge of the SOC of the EV battery it
    is charging but instead must estimate it based on the effective resistance
    of the battery which is calculated from the applied charging voltage and
    measured charging current. The effective resistance model is used here is
    identical to that of the actual battery; if both the charging voltage
    and current were measured perfectly the SOC estimate here would exactly
    match the true SOC modeled by the battery. For fun, though, a small
    amount of Gaussian noise is added to the current value. This noise
    creates larger errors as the charging current goes down (EV battery
    reaching full SOC).

    :param charging_V: Applied charging voltage
    :param charging_A: Charging current as passed back by the battery federate
    :return: SOC estimate
    %}

    socs = [0, 1];
    effective_R = [8, 150];
    mu = 0;
    sigma = 0.2
    noise = mu + sigma*randn();
    measured_A = charging_A + noise;
    measured_R = charging_V / measured_A;
    SOC_estimate = interp1(effective_R, socs, measured_R);

end

%% Main Program
    rng(1490);
try
    fid = fopen('Charger.log', 'w');
    %%%%%%%%%%%%%  Registering  federate from json  %%%%%%%%%%%%%%%%%%%%%
    fed = helics.helicsCreateCombinationFederateFromConfig("ChargerConfig.json");
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
    pubid = {}
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
    update_interval = helics.helicsFederateGetTimeProperty(fed, helics.HELICS_PROPERTY_TIME_PERIOD);
    grantedtime = 0;

    % Generate an initial fleet of EVs, one for each previously defined
    %   endpoint. This gives each EV a unique link to the EV controller
    %   federate.
    numLvl1,numLvl2,numLvl3,EVlist = get_new_EV(end_count);
    charging_voltage = calc_charging_voltage(EVlist);
    currentsoc = [];

    % Data collection lists
    time_sim = []
    power = []
    charging_current = [];

    % Blocking call for a time request at simulation time 0
    initial_time = 60;
    fprintf(fid, 'Requesting initial time %d\n', initial_time);
    grantedtime = helics.helicsFederateRequestTime(fed, initial_time);
    fprintf(fid,'Granted time %d\n', grantedtime);


    % Apply initial charging voltage
    for j=1:pub_count
        helics.helicsPublicationPublishDouble(pubid{j}, charging_voltage(j));
        fprintf(fid,'\tPublishing charging voltage of %0.2f at time %d\n', charging_voltage(j). grantedtime);
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
            if charging_current(j) == 0:
                [~, ~, ~, newEVtype] = get_new_EV(1);
                EVlist(j) = newEVtype;
                charge_V = calc_charging_voltage(newEVtype);
                charging_voltage(j) = charge_V;

                currentsoc(j) = 0; % Initial SOC estimate
                printf(fid,'\t New EV, SOC estimate: %0.4f\n', currentsoc(j));
                printf(fid,'\t New EV, charging voltage: %0.2f\n', charging_voltage(j));
            else
                % SOC estimation
                currentsoc(j) = estimate_SOC(charging_voltage(j), charging_current(j));
                printf(fid,'\t EV SOC estimate: %0.4f\n', currentsoc(j));
            end


            % Check for messages from EV Controller
            endpoint_name = helics.helicsEndpointGetName(endid{j});
            if helics.helicsEndpointHasMessage(endid{j})
                msg = helics.helicsEndpointGetMessage(endid{j});
                instructions = helics.helicsMessageGetString(msg)
                source = helics.helicsMessageGetOriginalSource(msg)
                fprintf(fid, '\tReceived message at endpoint %s, from source %s at time %d with command %s', endpoint_name, source, grantedtime, instructions);

                % Update charging state based on message from controller
                % The protocol used by the EV and the EV Controller is simple:
                %       EV Controller sends "1" - keep charging
                %       EV Controller sends anything else: stop charging
                % The default state is charging (1) so we only need to
                %   do something if the controller says to stop
                if str2num(instructions) == 0:
                    % Stop charing this EV
                    charging_voltage(j) = 0;
                    fprintf(fid, '\tEV full; removing charging voltage\n');
                end
            else:
                fprintf(fid, '\tNo messages at endpoint %s recieved at time %d\n', endpoint_name, grantedtime);
            end

            % Publish updated charging voltage
            helics.helicsPublicationPublishDouble(pubid{j}, charging_voltage(j))
            fprintf(fid, '\tPublishing charging voltage of %0.2f at time %d\n', charging_voltage(j), grantedtime);

            % Send message to Controller with SOC every 15 minutes
            if mod(grantedtime,900) == 0
                destination_name = sprintf('%s', helics.helicsEndpointGetDefaultDestination(endid{j}));
                message = sprintf('%0.4f', currentsoc(j));
                helics.helicsEndpointSendBytesTo(endid{j}, message, '');
                fprintf(fid, 'Sent message from endpoint %s to destination %s at time %d with payload SOC %s', endpoint_name,destination_name, grantedtime, message);
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
catch
    fprintf(fid, 'Something happend, closing log file\n');
    fprintf('Charger: Something happend, closing log file\n');
    fclose(fid);
end