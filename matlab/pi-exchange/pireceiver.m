% PIRECEIVER script demonstrating MATLAB-HELICS interface
%
% See pisender for usage information
%
% This example attempts to request the next time equal to its
% sim_stop_time, but the corresponding pisender will request intermediate
% times such that the pireceiver will be granted times earlier than
% requested
%
% Note to non-programmers: if unfamiliar, the assert functions simply check
% if the condition is true and if so continues. If false, execution stops.

%% Initialize HELICS library in MATLAB
helicsStartup()

import helics.*;
%% Configuration
deltat = 0.01;  %Base time interval (seconds)
sim_stop_time = 20;

% HELICS options
helics_core_type = 'zmq'; 
fedinitstring = '--federates=1';  % required with current C interface when using separate processes for each federate

%% Provide summary information
helicsversion = helicsGetVersion();

fprintf('PI RECEIVER: Helics version = %s\n', helicsversion)

%% Create Federate Info object that describes the federate properties
fedinfo = helicsCreateFederateInfo();
assert(not(isempty(fedinfo)))

% Set core type from string
helicsFederateInfoSetCoreTypeFromString(fedinfo, helics_core_type);


% Federate init string
helics.helicsFederateInfoSetCoreInitString(fedinfo, fedinitstring);


%% Set the message interval (timedelta) for federate. 
% Note:
% HELICS minimum message time interval is 1 ns and by default
% it uses a time delta of 1 second. What is provided to the
% setTimedelta routine is a multiplier for the default timedelta 
% (default unit = seconds).

% Set one message interval
helicsFederateInfoSetTimeProperty(fedinfo,helics_property_time_delta,deltat);
helicsFederateInfoSetIntegerProperty(fedinfo,helics_property_int_log_level,helics_log_level_warning);



%% Actually create value federate
vfed = helicsCreateValueFederate('MATLAB Pi Receiver Federates',fedinfo);
disp('PI RECEIVER: Value federate created');

% Subscribe to PI SENDER's publication (note: published as global)
sub = helicsFederateRegisterSubscription(vfed, 'testA', '');

disp('PI RECEIVER: Subscription registered (testA)');

%% Start execution
try
    helicsFederateEnterExecutingMode(vfed);
    disp('PI RECEIVER: Entering execution mode');
catch e
    error('PI RECEIVER: Failed to enter execution mode (status = x)\n Try running pisender.m first. (or start the broker seperately)');
end

%% Execution Loop
granted_time =- 1;  %Force at least one run

%% Continue execution until end of requested simulation time
while granted_time <= sim_stop_time

    granted_time = helicsFederateRequestTime(vfed, sim_stop_time);

    isupdated = helicsInputIsUpdated(sub);

    if (isupdated == 1)
        value = helicsInputGetDouble(sub);
        fprintf('PI RECEIVER: Received value = %g at time %4.1f from PI SENDER\n', value, granted_time);
    end
end

%% Shutdown
helicsFederateDestroy(vfed);

disp('PI RECEIVER: Federate finalized');

