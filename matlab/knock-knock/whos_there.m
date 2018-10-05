% WHOS_THERE script 2 of 2 demonstrating basic MATLAB-HELICS message interfaces
%
% See knock_knock for usage information
%
% This example simply waits until there is a joke sent and then responds
% accordingly
%
% Note to non-programmers: if unfamiliar, the assert functions simply check
% if the condition is true and if so continues. If false, execution stops.

%% Initialize HELICS library in MATLAB
helicsStartup()

%% Configuration
deltat = 0.1;  %Base time interval (seconds)
my_fed_name = 'Whos_There_MsgFed_MATLAB';
my_endpt_name = 'Audience';

response_delay = 0.2;   %Time in seconds between steps of the joke, must be >0
timeout = 10;

%Information about other federate
their_fed_name = 'Knock_Knock_MsgFed_MATLAB';
their_endpt_name = 'JokeTeller';

% HELICS options
helics_core_type = 'zmq'; 
fedinitstring = '--federates=1';  % required with current C interface when using separate processes for each federate

%% Provide summary information
helicsversion = helics.helicsGetVersion();

fprintf('WHOS_THERE: Helics version = %s\n', helicsversion)

%% Create Federate Info object that describes the federate properties
fedinfo = helics.helicsFederateInfoCreate();
assert(not(isempty(fedinfo)))

% Set Federate name
status = helics.helicsFederateInfoSetFederateName(fedinfo, my_fed_name);
assert(status==0)

% Set core type from string
status = helics.helicsFederateInfoSetCoreTypeFromString(fedinfo, helics_core_type);
assert(status==0)

% Federate init string
status = helics.helicsFederateInfoSetCoreInitString(fedinfo, fedinitstring);
assert(status==0)

%% Set the message interval (timedelta) for federate. 
% Note:
% HELICS minimum message time interval is 1 ns and by default
% it uses a time delta of 1 second. What is provided to the
% setTimedelta routine is a multiplier for the default timedelta 
% (default unit = seconds).

% Set one message interval
status = helics.helicsFederateInfoSetTimeDelta(fedinfo, deltat);
assert(status==0)

status = helics.helicsFederateInfoSetLoggingLevel(fedinfo, 1);
assert(status==0)

%% Actually create message federate
mfed = helics.helicsCreateMessageFederate(fedinfo);
disp('WHOS_THERE: Message federate created');

%% Register our endpoint (where we will publish the jokes)
% Note that by default, an Endpoint's name is prepended with the federate
% name and a separator ('/') to create unique names within the federation
my_endpt = helics.helicsFederateRegisterEndpoint(mfed, my_endpt_name, 'string');
fprintf('WHOS_THERE: Our Endpoint registered as "%s/%s"\n', my_fed_name, my_endpt_name);

%% Start execution
status = helics.helicsFederateEnterExecutionMode(mfed);
if status == 0
    disp('WHOS_THERE: Entering execution mode');
else
    error('WHOS_THERE: Failed to enter execution mode (status = %d)\n Try running knock_knock.m first. (or start the broker seperately)', status);
end

%% Execution Loop
% Message endpoint names are prepended by the federate name, so build the
% fullname of endpoint we will send to and receive from
their_endpt_fullname = sprintf('%s/%s', their_fed_name, their_endpt_name);

%% Keep responding as long as they are telling jokes
state = 'waiting';
give_up_sim_time = timeout;
granted_time = -1;  %dummy value so we will at least start

while granted_time < give_up_sim_time
    %Check for messages, if none, request our next time
    if not(helics.helicsEndpointHasMessage(my_endpt))
        [status, granted_time] = helics.helicsFederateRequestTime(mfed, give_up_sim_time);
        assert(status==0)
        continue
    end

    %If we get here, there must be a message, so receive them all and then respond accordingly
    while helics.helicsEndpointHasMessage(my_endpt)
        rx_msg = helics.helicsEndpointGetMessage(my_endpt);
        fprintf('WHOS_THERE: Received message "%s" at time %4.1f from %s\n', rx_msg.data, rx_msg.time, rx_msg.source)
    end
    
    %Advance time to introduce our response delay
    % Note: during the final exchange ("Goodbye"), this also allows the
    % sending federate to receive a valid time and end gracefully.
    [status, granted_time] = helics.helicsFederateRequestTime(mfed, granted_time + response_delay);
    
    %Build appropriate response
    switch state
        case 'waiting'
            %Start of joke or no joke
            if strcmp(rx_msg.data, 'Goodbye')
                %Note: final time advance already occurred when we
                %introduced our response delay.
                % That final time request must match that of the other
                % federate or the later request will hang.
                fprintf('WHOS_THERE: Shutting down (final time=%4.1f).\n', granted_time)
                break
            else
                to_send = 'Who''s there?';
                state = 'started';
            end
        case 'started'
            to_send = sprintf('%s who?', rx_msg.data);
            state = 'ready_to_laugh';
        case 'ready_to_laugh'
            to_send = 'Ha, ha!';
            state = 'waiting';
    end
    
    %Send response
    fprintf('WHOS_THERE: Sending message "%s" to "%s" at time %4.1f... ', to_send, their_endpt_fullname, granted_time);
    status = helics.helicsEndpointSendMessageRaw(my_endpt, their_endpt_fullname, to_send);
    fprintf('DONE (status=%d)\n', status);

    give_up_sim_time = granted_time + timeout;
end

%% Shutdown
helicsDestroyFederate(mfed);

disp('WHOS_THERE: Federate finalized');

