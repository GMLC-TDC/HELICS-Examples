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
    sigma = 0.2;
    noise = mu + sigma*randn();
    measured_A = charging_A + noise;
    measured_R = charging_V / measured_A;
    SOC_estimate = interp1(effective_R, socs, measured_R);

end