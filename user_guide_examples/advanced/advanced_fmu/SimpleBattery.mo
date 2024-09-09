model SimpleBattery
//  Modelica.Units.SI.Voltage V "in Volts";
//  Modelica.Units.SI.Current I "in Amps";
  Modelica.Units.SI.Resistance R "in Ohm";
  type StateOfCharge=Real(unit="p.u.", min=0, max=1.25);
  
  parameter Modelica.Units.SI.Resistance Rlim[2]={8,150} "in Ohms";
  parameter Modelica.Units.NonSI.Energy_kWh E_rate=100;
  parameter StateOfCharge soc_init=0 "initial soc";
  Integer iNew;
  Modelica.Blocks.Interfaces.RealInput Vin(unit="V") annotation(
    Placement(visible = true, transformation(origin = {-50, 0}, extent = {{-20, -20}, {20, 20}}, rotation = 0), iconTransformation(origin = {-62, 0}, extent = {{-20, -20}, {20, 20}}, rotation = 0)));
  
  StateOfCharge soc;
  Modelica.Units.NonSI.Energy_kWh E "in kWh";
  Modelica.Blocks.Interfaces.RealOutput Iout(unit="A") annotation(
    Placement(visible = true, transformation(origin = {40, 0}, extent = {{-10, -10}, {10, 10}}, rotation = 0), iconTransformation(origin = {40, 0}, extent = {{-10, -10}, {10, 10}}, rotation = 0)));
initial equation
  soc = 0;
equation
//  V = Vin;
  (R, iNew) = Modelica.Math.Vectors.interpolate({0,1},Rlim,soc+soc_init);
  if (soc_init + soc) < 1 then
    Iout = Vin/R;
    der(soc) = Iout*Vin/Modelica.Units.Conversions.from_kWh(E_rate);
  else
    Iout = 0;
    der(soc) = 0;
  end if;
  /* der(E) = I*V in W
    soc = E in J/(E_rate in J)
    Therefore der(soc) = der(E)/(E_rate in J) = I*V/(E_rate in J)
  */
  E = (soc_init + soc)*E_rate;
//  Iout = I;
annotation(
    uses(Modelica(version = "4.0.0")),
    Icon(graphics = {Rectangle(origin = {-5, 1}, extent = {{-37, 37}, {37, -37}})}));
end SimpleBattery;
