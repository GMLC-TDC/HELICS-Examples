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