This example can be run to show parallel operation of three co-simulations on one computer. All three co-simulations are identical except for naming and random number seed. Running the three co-simulations demonstrates the need for a more comprehensive analysis of the peak power requirements for the EV charging infrastructure while showing that the default advanced example wasn't representative.

```
helics run --path=./federation_1/federation_1_runner.json &
helics run --path=./federation_2/federation_2_runner.json &
helics run --path=./federation_3/federation_3_runner.json &

```