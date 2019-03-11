% PISENDER script demonstrating MATLAB-HELICS interface
%
% Usage:
%  1. Start two separate MATLAB terminals 
%  2. In the first: 
%     >> pisender
%  3. In the second:
%     >> pireciever


%% Initialize HELICS library in MATLAB
helicsStartup()

import helics.*;
%% Configuration
deltat = 1;  %Base time interval (seconds)
numsteps = 20;

% HELICS options
% Note: these configure this matlab process to host the main broker and 1
% federate
pisend_start_broker = true;
helics_core_type = 'zmq'; 
broker_initstring = '--federates 2 --name=mainbroker';
fed_initstring = '--broker=mainbroker --federates=1';

%% Provide summary information

fprintf('PI SENDER (with main broker): Helics version = %s\n', helicsGetVersion())

%% Create broker (if desired)
if pisend_start_broker
    disp('Creating Broker');
    broker = helicsCreateBroker(helics_core_type, '', broker_initstring);
    disp('Created Broker');

    fprintf('Checking if Broker is connected...');
    isconnected = helics.helicsBrokerIsConnected(broker);

    if isconnected == 1
        fprintf('SUCCESS, Broker created and connected\n');
    else
        fprintf('\n')
        error('NOT CONNECTED (helicsBrokerIsConnected return = %d)', isconnected)
    end
end

%% Create Federate Info object that describes the federate properties
fedinfo = helicsCreateFederateInfo();
assert(not(isempty(fedinfo)))

% Set core type from string
helicsFederateInfoSetCoreTypeFromString(fedinfo, helics_core_type);


% Federate init string
helicsFederateInfoSetCoreInitString(fedinfo, fed_initstring);

% Note:
% HELICS minimum message time interval is 1 ns and by default
% it uses a time delta of 1 second. What is provided to the
% setTimedelta routine is a multiplier for the default timedelta 
% (default unit = seconds).

% Set one message interval
helicsFederateInfoSetTimeProperty(fedinfo,helics_property_time_delta,deltat);
helicsFederateInfoSetIntegerProperty(fedinfo,helics_property_int_log_level,helics_log_level_warning);

%% Actually create value federate
vfed = helicsCreateValueFederate('MATLAB Pi SENDER Federate',fedinfo);
disp('PI SENDER: Value federate created');

%% Register our value to publish
pub = helicsFederateRegisterGlobalPublication(vfed, 'testA', helics_data_type_double, '');
disp('PI SENDER: Publication registered (testA)');

%% Start execution
try
    helicsFederateEnterExecutingMode(vfed);
    disp('PI SENDER: Entering execution mode');
catch e
    error('PI SENDER: Failed to enter execution mode (status = X)\n Try running pisender.m first. (or start the broker seperately)');
end

%% Execution Loop
% This federate will be publishing deltat*pi for numsteps steps
this_time = 0.0;
value = pi;

for i = 1:numsteps
    val = value;

     granted_time = helicsFederateRequestTime(vfed, i);

%    fprintf('PI SENDER: Publishing value pi = %g at time %f\n', val, this_time + (deltat * i));
    fprintf('PI SENDER: Publishing value pi = %g at time %4.1f... ', val, granted_time);
  helicsPublicationPublishDouble(pub, val);
    fprintf('DONE\n');
end

%% Shutdown

if pisend_start_broker
    % If we started the broker in this thread, we have to be careful
    % sequencing the shutdown in hopes of doing so cleanly
    helicsFederateFinalize(vfed);
    disp('PI SENDER: Federate finalized');

    %Make sure the broker is gone in case we have a lingering low-level
    %reference (to avoid memory leaks)
    helicsBrokerWaitForDisconnect(broker,-1);
    disp('PI SENDER: Broker disconnected');

    helics.helicsFederateFree(vfed);
    helics.helicsCloseLibrary();
else
    %But if we just setup the federate, we can simply call endFederate
    helicsFederateDestroy(vfed); %#ok<UNRCH>  
    disp('PI SENDER: Federate finalized');
end



