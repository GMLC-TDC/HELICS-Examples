This example federation is useful for testing filter federate performance and demonstrating its basic configuration. source_sink.py includes data collection and graphing functionality that displays the histogram of the transit times of HELICS messages to and from the echo federate and can include processing by the filter federate if included in the federation.

It also includes in echo.py, alternative implementations of the echo function, some of which work correctly in this federation and some do not. Thus, it is a good example of how imprecise implementations of simple federates can result in unexpected behavior especially when using rerouting filters and filter federates.

For more details examine the comments in echo.py to see how it has implemented its a message echoing function.

