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