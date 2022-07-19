
%{
Created on 8/31/2020

This is a simple battery value federate that models the physics of an EV
battery as it is being charged. The federate receives a voltage signal
representing the voltage applied to the charging terminals of the battery
and based on its internally modeled SOC, calculates the current draw of
the battery and sends it back to the EV federate. Note that this SOC should
be considered the true SOC of the battery which may be different than the
SOC modeled by the charger

@author: Trevor Hardy
trevor.hardy@pnnl.gov
%}


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
    % annoying errors in the broker log. Any message are tacitly disregarded.
    grantedtime = helics.helicsFederateRequestTime(fed, helics.HELICS_TIME_MAXTIME);
    status = helics.helicsFederateDisconnect(fed);
    helics.helicsFederateFree(fed);
    helics.helicsCloseLibrary();
    fprintf(fid, 'Federate finalized\n');
end

function listOfBatts = get_new_battery(numBattery)
    %{
    Using hard-coded probabilities, a distribution of battery of
    fixed battery sizes are generated. The number of batteries is a user
    provided parameter.

    :param numBattery: Number of batteries to generate
    :return
        listOfBatts: List of generated batteries

    %}

    % # Probabilities of a new EV having a battery at a given capacity.
    % #   The three random values (25,62, 100) are the kWh of the randomly
    % #   selected battery.
    size_1 = 0.2;
    size_2 = 0.2;
    size_3 = 0.6;
    listOfBatts = randsample([25,62,100],numBattery,true,[size_1,size_2,size_3]);
end


%% Main Program
    rng(2608);
try
    fid = fopen('Battery.log', 'w');
    %%%%%%%%%  Registering  federate and configuring from JSON %%%%%%%%
    fed = helics.helicsCreateValueFederateFromConfig("BatteryConfig.json");
    federate_name = helics.helicsFederateGetName(fed);
    fprintf(fid, 'Created federate %s\n', federate_name);
    fprintf('Created federate %s\n', federate_name);

    sub_count = helics.helicsFederateGetInputCount(fed);
    fprintf(fid,'\tNumber of subscriptions: %d\n', sub_count);
    pub_count = h.helicsFederateGetPublicationCount(fed);
    fprintf(fid,'\tNumber of publications: %d\n', pub_count);

    % Diagnostics to confirm JSON config correctly added the required
    %   publications and subscriptions
    subid = {};
    sub_name = {};
    for i=1:sub_count
        subid{i} = helics.helicsFederateGetInputByIndex(fed, i-1);
        sub_name{i} = helics.helicsSubscriptionGetTarget(subid{i});
        fprintf(fid,'\tRegistered subscription---> %s\n', sub_name{i});
    end

    pubid = {}
    pub_name = {}
    for i=1:pub_count
        pubid{i} = helics.helicsFederateGetPublicationByIndex(fed, i-1);
        pub_name{i} = helics.helicsPublicationGetName(pubid{i});
        fprintf(fid,'\tRegistered publication---> %s\n', pub_name{i});
    end




 %%   ##############  Entering Execution Mode  ##################################
    helics.helicsFederateEnterExecutingMode(fed);
    fprintf(fid, 'Entered HELICS execution mode\n');


    hours = 24*7; % one week
    total_interval = 60 * 60 * hours;
    update_interval = helics.helicsFederateGetTimeProperty(fed,helics.HELICS_PROPERTY_TIME_PERIOD);
    grantedtime = 0;

    % Define battery physics as empirical values
    socs = [0, 1];
    effective_R = [8, 150];

    batt_list = get_new_battery(pub_count);

    current_soc = randi(60,1,pub_count)./100;


    % Data collection lists
    time_sim = [];
    current = [];
    soc = cell(sub_id, 1);

    % As long as granted time is in the time range to be simulated...
    while grantedtime < total_interval

        % Time request for the next physical interval to be simulated
        requested_time = grantedtime+update_interval;
        fprintf(fid,'Requesting time %d\n', requested_time);
        grantedtime = helics.helicsFederateRequestTime(fed, requested_time);
        fprintf(fid,'Granted time %d\n', grantedtime);

        for j=1:sub_count
            fprintf(fid,'Battery %d time %d', j, grantedtime);

            % Get the applied charging voltage from the EV
            charging_voltage = helics.helicsInputGetDouble(subid{j});
            fprintf(fid,'\tReceived voltage %0.2f{charging_voltage:.2f} from input %s\n', charging_voltage, helics.helicsSubscriptionGetTarget(subid{j}));

            % EV is fully charged and a new EV is moving in
            % This is indicated by the charging removing voltage when it
            %    thinks the EV is full
            if charging_voltage == 0
                new_batt = get_new_battery(1);
                batt_list(j) = new_batt;
                current_soc(j) = randi(80)/100;
                charging_current = 0
            end
            % Calculate charging current and update SOC
            R =  interp1(socs, effective_R, current_soc(j));
            fprintf(fid, '\tEffective R (ohms): %0.2f\n',R);
            charging_current = charging_voltage / R;
            fprintf(fid,'\tCharging current (A): %0.2f\n',charging_current);
            added_energy = (charging_current * charging_voltage * update_interval/3600) / 1000;
            fprintf(fid,'\tAdded energy (kWh): %0.4f', added_energy);
            current_soc(j) = current_soc(j) + added_energy / batt_list[j];
            fprintf(fid,'\tSOC: %0.4f', current_soc(j));



            % Publish out charging current
            helics.helicsPublicationPublishDouble(pubid{j}, charging_current)
            fprintf(fid,'\tPublished %s with value %0.2f', pub_name{j}, charging_current); 

            % Store SOC for later analysis/graphing
            soc{j}(end+1) = current_soc(j)
        end
        % Data collection vectors
        time_sim(end+1) = grantedtime;

    end
%% Post Processing
    % Cleaning up HELICS stuff once we've finished the co-simulation.
    destroy_federate(fed);
    % Printing out final results graphs for comparison/diagnostic purposes.
    xaxis = time_sim/3600;
    varnames = cell(5,1);
    for k=1:5
        varnames{k} = sprintf('Batt at port %d', k);
    end
    y = array2table(cell2mat(soc).', 'VariableName', varnames);
    y.x = time_sim.'/3600;

    stackedplot(y, 'XVariable', 'x', 'Title', 'SOC of each EV Battery', 'xlabel', 'time (hr)');
    grid();

    saveas(gcf, 'advanced_default_battery_SOCs.png', 'png');
catch
    fprintf(fid, 'Something happend, closing log file\n');
    fprintf('Battery: Something happend, closing log file\n');
    fclose(fid);
end