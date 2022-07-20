function charging_voltage = calc_charging_voltage(EV_List)
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