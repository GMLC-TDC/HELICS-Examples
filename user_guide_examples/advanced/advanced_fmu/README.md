# HELICS User Guide Advanced Topics - HELICS-FMI/FMU Example

This example demonstrates the usage of [HELICS-FMI](https://github.com/GMLC-TDC/HELICS-FMI) to run a co-simulation in helics with FMUs. The example duplicates the fundamental default example, except that the battery model has been replaced with an FMU. A full description of the example can be found in the [HELICS User Guide](https://docs.helics.org/en/latest/user-guide/examples/advanced_examples/advanced_fmu.html).

`SimpelBattery.fmu` was compiled on a Windows 10 machine.
`SimpleBatterLinux.fmu` was compiled on Ubuntu 22.04.2 LTS using OpenModelica 1.21.0.
Note that if the linux version is used, `runner.json` will have to be modified slightly to point to the right FMU.