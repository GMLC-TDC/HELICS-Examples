/*
Copyright © 2017-2018,
Battelle Memorial Institute; Lawrence Livermore National Security, LLC; Alliance for Sustainable Energy, LLC
All rights reserved. See LICENSE file and DISCLAIMER for more details.
*/

#include <helics/shared_api_library/ValueFederate.h>
#include <stdio.h>

int main ()
{
    helics_federate_info fedinfo; /* an information object used to pass information to a federate*/
    const char *fedinitstring = "--federates=1"; /* tell the core to expect only 1 federate*/
    helics_federate vfed; /* object representing the actual federate*/
    helics_input sub; /* an object representing a subscription*/
    helics_time currenttime = 0.0; /* the current time of the simulation*/
    helics_error  err=helicsErrorInitialize();/* the result code from a call to the helics Library*/
    helics_bool isUpdated;  /* storage for a check if a value has been updated*/


    /** create an info structure to define some parameters used in federate creation*/
    fedinfo = helicsCreateFederateInfo();
    /** set the core type to use
    can be "test", "ipc", "udp", "tcp", "zmq", "mpi"
    not all are available on all platforms
    and should be set to match the broker and receiver
    zmq is the default*/
    helicsFederateInfoSetCoreTypeFromString (fedinfo, "zmq",&err);
    helicsFederateInfoSetCoreInitString (fedinfo, fedinitstring,&err);

    /** set the period of the federate to 1.0*/
    helicsFederateInfoSetTimeProperty(fedinfo,helics_property_time_period, 1.0,&err);

    /** create the core using the informational structure*/
    vfed = helicsCreateValueFederate ("hello_world_receiver",fedinfo,&err);
    if (err.error_code!= helics_ok) /*check to make sure the federate was created*/
    {
        return (-2);
    }

    /** free the federateInfo structure when it isn't needed*/
    helicsFederateInfoFree(fedinfo);
    /** register a subscription interface on vFed, with a Name of "hello", with no units*/
    sub = helicsFederateRegisterSubscription (vfed, "hello",NULL,&err);
    if (err.error_code != helics_ok)
    {
        return (-3);
    }
    /** transition the federate to execution mode
    * the helicsFederateEnterInitializationMode is not necessary if there is nothing to do in the initialization mode
    */
    helicsFederateEnterInitializingMode (vfed,&err);
    helicsFederateEnterExecutingMode (vfed,&err);
    /** request that helics grant the federate a time of 1.0
    the new time will be returned*/
    currenttime=helicsFederateRequestTime (vfed, 1.0,&err);
    if (err.error_code != helics_ok)
    {
        fprintf(stderr, "HELICS request time failed\n");
    }
    else
    {
        fprintf(stdout, "HELICS granted time:%f\n", currenttime);
    }
    /** check if the value was updated*/
    isUpdated = helicsInputIsUpdated (sub);
    if (isUpdated)
    { /* get the value*/
        int actualLen;
        char value[128] = ""; /**space to store the sent value*/
        helicsInputGetString(sub, value, 128,&actualLen,&err);
        printf("%s\n", value);
    }
    else
    {
        printf("value was not updated\n");
    }
    /** finalize the federate*/
    helicsFederateFinalize (vfed,&err);
    /** free the memory allocated to the federate*/
    helicsFederateFree (vfed);
    /** close the helics library*/
    helicsCloseLibrary ();
    return (0);
}

