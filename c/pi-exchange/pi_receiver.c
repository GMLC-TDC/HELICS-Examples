/*
Copyright © 2017-2018,
Battelle Memorial Institute; Lawrence Livermore National Security, LLC; Alliance for Sustainable Energy, LLC
All rights reserved. See LICENSE file and DISCLAIMER for more details.
*/
static char help[] = " PI RECEIVER: Simple program to demonstrate the usage of HELICS C Interface.\n\
            This example creates a value federate subscribing to the publication \n\
            registered by PI SENDER.\n\n";

#include <ValueFederate.h>
#include <stdio.h>

int main ()
{
    helics_federate_info fedinfo;
    const char *helicsversion;

    const char *fedinitstring = "--federates=1";
    double deltat = 0.01;
    helics_federate vfed;
    helics_input sub;
    helics_time currenttime = 0.0;
	helics_error err= helicsErrorInitialize();
    double value = 0.0;

    helicsversion = helicsGetVersion ();

    printf ("PI RECEIVER: Helics version = %s\n", helicsversion);
    printf ("%s", help);

    /* Create Federate Info object that describes the federate properties */
    fedinfo = helicsCreateFederateInfo ();

    /* Set core type from string */
    helicsFederateInfoSetCoreTypeFromString (fedinfo, "zmq",&err);

    /* Federate init string */
    helicsFederateInfoSetCoreInitString (fedinfo, fedinitstring,&err);

    /* Set the message interval (timedelta) for federate. Note that
       HELICS minimum message time interval is 1 ns and by default
       it uses a time delta of 1 second. What is provided to the
       setTimedelta routine is a multiplier for the default timedelta.
    */
    /* Set one second message interval */
	helicsFederateInfoSetTimeProperty(fedinfo, helics_property_time_period, deltat, &err);

    helicsFederateInfoSetIntegerProperty(fedinfo, helics_property_int_log_level,1,&err);

    /* Create value federate */
    vfed = helicsCreateValueFederate ("TestB Federate",fedinfo,&err);
    printf ("PI RECEIVER: Value federate created\n");
	//free the federateInfo structure
	helicsFederateInfoFree(fedinfo);

    /* Subscribe to PI SENDER's publication */
    sub = helicsFederateRegisterSubscription (vfed, "testA", "",&err);
    printf ("PI RECEIVER: Subscription registered\n");

    /* Enter initialization mode */
	helicsFederateEnterInitializingMode(vfed, &err);
    if (err.error_code == helics_ok)
    {
        printf ("PI RECEIVER: Entered initialization mode\n");
    }
    else
    {
		printf("PI RECEIVER: Failed to Entered initialization mode: %s\n",err.message);
        return (err.error_code);
    }

    /* Enter execution mode */
	helicsFederateEnterExecutingMode(vfed, &err);
    if (err.error_code == helics_ok)
    {
        printf ("PI RECEIVER: Entered execution mode\n");
    }
	else
	{
		printf("PI RECEIVER: Failed to Entered execution mode: %s\n", err.message);
		return (err.error_code);
	}
    while (currenttime < 0.20)
    {
        int isupdated;
		currenttime=helicsFederateRequestTime (vfed, currenttime, &err);

        isupdated = helicsInputIsUpdated (sub);
        if (isupdated!=helics_false)
        {
            /* NOTE: The value sent by sender at time t is received by receiver at time t+deltat */
            value=helicsInputGetDouble (sub, &err);
            printf ("PI RECEIVER: Received value = %4.3f at time %3.2f from PI SENDER\n", value, currenttime);
        }
    }
    helicsFederateDestroy (vfed);
    printf ("PI RECEIVER: Federate finalized\n");
    helicsCloseLibrary ();
    return (0);
}

