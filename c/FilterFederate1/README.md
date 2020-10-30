# FilterFed

This example federate is intended to work with messageFed

## Instructions
Execution of this federate requires a helics_broker and a messageFed

$ ./helics_broker -f 2

in another terminal
$./filterFed-c


In another terminal
%./messageFed-c

## Results

filterFed-c

```txt
registering endpoint endpoint for ffed
entering init Mode
entered init Mode
entered execution Mode
granted time 4.000000
delay set to 1.5
granted time 8.000000
finalizing federate
```

for messageFed-c

```txt
registering endpoint "endpoint" for fed
entering init Mode
entered init Mode
entered execution Mode
sent <message sent from fed to fed/endpoint at time 0> to fed/endpoint at time 0.000000
fed granted time 1.000000
received message from fed/endpoint time(0.500000) at time 1.000000 ::<message sent from fed to fed/endpoint at time 0>
sent <message sent from fed to fed/endpoint at time 1> to fed/endpoint at time 1.000000
fed granted time 2.000000
received message from fed/endpoint time(1.500000) at time 2.000000 ::<message sent from fed to fed/endpoint at time 1>
sent <message sent from fed to fed/endpoint at time 2> to fed/endpoint at time 2.000000
fed granted time 3.000000
received message from fed/endpoint time(2.500000) at time 3.000000 ::<message sent from fed to fed/endpoint at time 2>
sent <message sent from fed to fed/endpoint at time 3> to fed/endpoint at time 3.000000
fed granted time 4.000000
received message from fed/endpoint time(3.500000) at time 4.000000 ::<message sent from fed to fed/endpoint at time 3>
sent <message sent from fed to fed/endpoint at time 4> to fed/endpoint at time 4.000000
fed granted time 5.000000
sent <message sent from fed to fed/endpoint at time 5> to fed/endpoint at time 5.000000
fed granted time 6.000000
received message from fed/endpoint time(5.500000) at time 6.000000 ::<message sent from fed to fed/endpoint at time 4>
sent <message sent from fed to fed/endpoint at time 6> to fed/endpoint at time 6.000000
fed granted time 7.000000
received message from fed/endpoint time(6.500000) at time 7.000000 ::<message sent from fed to fed/endpoint at time 5>
sent <message sent from fed to fed/endpoint at time 7> to fed/endpoint at time 7.000000
fed granted time 8.000000
received message from fed/endpoint time(7.500000) at time 8.000000 ::<message sent from fed to fed/endpoint at time 6>
sent <message sent from fed to fed/endpoint at time 8> to fed/endpoint at time 8.000000
fed granted time 9.000000
received message from fed/endpoint time(8.500000) at time 9.000000 ::<message sent from fed to fed/endpoint at time 7>
received message from fed/endpoint time(8.750000) at time 9.000000 ::<message sent from fed to fed/endpoint at time 8>
finalizing federate
```

If MessageFed is run without the filterFed

```txt
registering endpoint "endpoint" for fed
entering init Mode
entered init Mode
entered execution Mode
sent <message sent from fed to fed/endpoint at time 0> to fed/endpoint at time 0.000000
fed granted time 1.000000
received message from fed/endpoint time(0.000000) at time 1.000000 ::<message sent from fed to fed/endpoint at time 0>
sent <message sent from fed to fed/endpoint at time 1> to fed/endpoint at time 1.000000
fed granted time 2.000000
received message from fed/endpoint time(1.000000) at time 2.000000 ::<message sent from fed to fed/endpoint at time 1>
sent <message sent from fed to fed/endpoint at time 2> to fed/endpoint at time 2.000000
fed granted time 3.000000
received message from fed/endpoint time(2.000000) at time 3.000000 ::<message sent from fed to fed/endpoint at time 2>
sent <message sent from fed to fed/endpoint at time 3> to fed/endpoint at time 3.000000
fed granted time 4.000000
received message from fed/endpoint time(3.000000) at time 4.000000 ::<message sent from fed to fed/endpoint at time 3>
sent <message sent from fed to fed/endpoint at time 4> to fed/endpoint at time 4.000000
fed granted time 5.000000
received message from fed/endpoint time(4.000000) at time 5.000000 ::<message sent from fed to fed/endpoint at time 4>
sent <message sent from fed to fed/endpoint at time 5> to fed/endpoint at time 5.000000
fed granted time 6.000000
received message from fed/endpoint time(5.000000) at time 6.000000 ::<message sent from fed to fed/endpoint at time 5>
sent <message sent from fed to fed/endpoint at time 6> to fed/endpoint at time 6.000000
fed granted time 7.000000
received message from fed/endpoint time(6.000000) at time 7.000000 ::<message sent from fed to fed/endpoint at time 6>
sent <message sent from fed to fed/endpoint at time 7> to fed/endpoint at time 7.000000
fed granted time 8.000000
received message from fed/endpoint time(7.000000) at time 8.000000 ::<message sent from fed to fed/endpoint at time 7>
sent <message sent from fed to fed/endpoint at time 8> to fed/endpoint at time 8.000000
fed granted time 9.000000
received message from fed/endpoint time(8.000000) at time 9.000000 ::<message sent from fed to fed/endpoint at time 8>
finalizing federate
```

Notice the difference in arrival times for some of the messages.  
