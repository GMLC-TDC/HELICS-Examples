% KNOCK_KNOCK script 1 of 2 demonstrating basic MATLAB-HELICS message interfaces
%
%  Exchanges knock-knock jokes with the whos_there federate. Also
%  establishes the federation and its broker.
%
% Usage:
%  1. Start two separate MATLAB terminals 
%  2. In the first: 
%     >> knock_knock
%  3. In the second:
%     >> whos_there


%% Initialize HELICS library in MATLAB
helicsStartup()

%% Configuration
%Local setup
joke_strings = {'Boo'       'Don''t cry, there''s an even better one coming next'
                'You'       'YooHoo, message federates in HELICS are working in MATLAB'};

deltat = 0.1;  %Base time interval (seconds)
numjokes = size(joke_strings,1);
my_fed_name = 'Knock_Knock_MsgFed_MATLAB';
my_endpt_name = 'JokeTeller';

between_jokes = 1.0;    %Time in seconds, must be >0
response_delay = 0.1;   %Time in seconds between steps of the joke, must be >0
timeout = 10;


%Information about other federate
their_fed_name = 'Whos_There_MsgFed_MATLAB';
their_endpt_name = 'Audience';
% IMPORTANT (as of HELICS 1.3.0), Message federates are not granted times
% earlier than they request, so the final time request must match that of
% the WHOS_THERE federate or the federate requesting the later time will
% hang. As a work around we ensure we use the same delay for this final
% request.
%TODO: more gracefully handle 2 message federates requesting unequal final
%times
their_response_delay = 0.2;

% HELICS options
% Note: these configure this matlab process to host the main broker and 1
% federate
knock_knock_start_broker = true;
helics_core_type = 'zmq'; 
broker_initstring = '2 --name=mainbroker';
fed_initstring = '--broker=mainbroker --federates=1';

%% Provide summary information
helicsversion = helics.helicsGetVersion();

fprintf('KNOCK KNOCK (with main broker): Helics version = %s\n', helicsversion)

%% Create broker (if desired)
if knock_knock_start_broker
    disp('Creating Broker');
    broker = helics.helicsCreateBroker(helics_core_type, '', broker_initstring);
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
fedinfo = helics.helicsFederateInfoCreate();
assert(not(isempty(fedinfo)))

% Set Federate name
status = helics.helicsFederateInfoSetFederateName(fedinfo, my_fed_name);
assert(status==0)

% Set core type from string
status = helics.helicsFederateInfoSetCoreTypeFromString(fedinfo, helics_core_type);
assert(status==0)

% Federate init string
status = helics.helicsFederateInfoSetCoreInitString(fedinfo, fed_initstring);
assert(status==0)


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
disp('KNOCK KNOCK: Message federate created');

%% Register our endpoint (where we will publish the jokes)
% Note that by default, an Endpoint's name is prepended with the federate
% name and a separator ('/') to create unique names within the federation
my_endpt = helics.helicsFederateRegisterEndpoint(mfed, my_endpt_name, 'string');
fprintf('KNOCK KNOCK: Our Endpoint registered as "%s/%s"\n', my_fed_name, my_endpt_name);

%% Start execution
status = helics.helicsFederateEnterExecutionMode(mfed);
if status == 0
    disp('KNOCK KNOCK: Entering execution mode');
else
    error('KNOCK KNOCK: Failed to enter execution mode (status = %d)\n make sure knock_knock_start_broker = true. (or start the broker seperately)', status);
end

%% Execution Loop
% Message endpoint names are prepended by the federate name, so build the
% fullname of endpoint we will send to and receive from
their_endpt_fullname = sprintf('%s/%s', their_fed_name, their_endpt_name);

%Start by advancing to our desired start time
granted_time = 0;
while granted_time < between_jokes
    [status, granted_time] = helics.helicsFederateRequestTime(mfed, between_jokes);
    assert(status==0)
end

%Now loop over the list of jokes, waiting between_jokes seconds between
for joke_id = 1:numjokes
    %Clear out any old messages
    while helics.helicsEndpointHasMessage(my_endpt)
        rx_msg = h.helicsEndpointGetMessage(my_endpt);
        fprintf('KNOCK KNOCK: Received message "%s" at time %4.1f from %s\n', rx_msg.data, rx_msg.time, rx_msg.source)
    end    
    
    %And each step of the joke, waiting for a response (with timeout) and
    %then after the response_delay send the next part of the joke
    num_steps_after_opener = size(joke_strings,2);
    for joke_step = 0:num_steps_after_opener
        if joke_step == 0
            to_send = 'Knock, Knock';
        else
            to_send = joke_strings{joke_id, joke_step};
        end

        %Send next line of joke
        fprintf('KNOCK KNOCK: Sending message "%s" to "%s" at time %4.1f... ', to_send, their_endpt_fullname, granted_time);
        status = helics.helicsEndpointSendMessageRaw(my_endpt, their_endpt_fullname, to_send);
        fprintf('DONE (status=%d)\n', status);
        
        %Wait for a response (with timeout)
        give_up_time = granted_time + timeout;

        while granted_time < give_up_time && not(helics.helicsEndpointHasMessage(my_endpt))
            [status, granted_time] = helics.helicsFederateRequestTime(mfed, give_up_time);
            assert(status==0)
        end
        
        if granted_time >= give_up_time
            fprintf('KNOCK KNOCK: You''re a tough crowd. (no response in %4.1f sec)', timeout)
            break
        end
        
        %Display all messages
        while helics.helicsEndpointHasMessage(my_endpt)
            rx_msg = helics.helicsEndpointGetMessage(my_endpt);
            fprintf('KNOCK KNOCK: Received message "%s" at time %4.1f from %s\n', rx_msg.data, rx_msg.time, rx_msg.source)
        end    
        
        %Pause before advancing to the next step
        if joke_step < num_steps_after_opener
            target_time = granted_time + response_delay;
        else
            target_time = granted_time + between_jokes;
        end
        while granted_time < target_time
            [status, granted_time] = helics.helicsFederateRequestTime(mfed, target_time);
            assert(status==0)
        end

    end
end

%% Send a final message so audience knows to stop
to_send = 'Goodbye';
fprintf('KNOCK KNOCK: Sending message "%s" to "%s" at time %4.1f... ', to_send, their_endpt_fullname, granted_time);
status = helics.helicsEndpointSendMessageRaw(my_endpt, their_endpt_fullname, to_send);
fprintf('DONE (status=%d)\n', status);
%Important: The message will not actually be made available to the receiver
%until we advance the time
[status, granted_time] = helics.helicsFederateRequestTime(mfed, granted_time + their_response_delay);
assert(status==0)
fprintf('KNOCK KNOCK: Shutting Down (Final time granted= %4.1f)\n', granted_time);


%% Shutdown

if knock_knock_start_broker
    % If we started the broker in this thread, we have to be careful
    % sequencing the shutdown in hopes of doing so cleanly
    status = helics.helicsFederateFinalize(mfed);
    disp('KNOCK KNOCK: Federate finalized');

    %Make sure the broker is gone in case we have a lingering low-level
    %reference (to avoid memory leaks)
    for foo = 1:60
        if not(helics.helicsBrokerIsConnected(broker))
            break
        end
        pause(1);
    end
    disp('KNOCK KNOCK: Broker disconnected');

    helics.helicsFederateFree(mfed);
    helics.helicsCloseLibrary();
else
    %But if we just setup the federate, we can simply call endFederate
    helicsDestroyFederate(mfed); %#ok<UNRCH>  
    disp('KNOCK KNOCK: Federate finalized');
end



