/*
Copyright © 2017-2019,
Battelle Memorial Institute; Lawrence Livermore National Security, LLC; Alliance for Sustainable Energy, LLC.  See
the top-level NOTICE for additional details. All rights reserved.
SPDX-License-Identifier: BSD-3-Clause
*/
#include <helics/shared_api_library/MessageFederate.h>
#include <helics/shared_api_library/MessageFilters.h>
#include <stdio.h>
#include <string.h>
#ifdef _MSC_VER
#include <windows.h>
#else
#include <unistd.h>
#endif

/*
static const helics::ArgDescriptors InfoArgs{
    {"startbroker","start a broker with the specified arguments"},
    {"target,t", "name of the target federate"},
    { "messagetarget", "name of the target federate, same as target" },
    {"endpoint,e", "name of the target endpoint"},
    {"source,s", "name of the source endpoint"}
    //name is captured in the argument processor for federateInfo
};
*/
static const char defTarget[] = "fed";
static const char defTargetEndpoint[] = "endpoint";
static const char defLocalEndpoint[] = "endpoint";

int main (int argc, char *argv[])
{
    helics_federate_info fedinfo = helicsCreateFederateInfo();
    const char *target = defTarget;
    const char *endpoint = defTargetEndpoint;
    const char *source = defLocalEndpoint;
    char *targetEndpoint = NULL;
    int ii;
    helics_federate fFed = NULL;
    helics_endpoint ept = NULL;
    helics_filter filt = NULL;
    const char *str=NULL;
    helics_time newTime;
    helics_error err = helicsErrorInitialize();
    for (ii = 1; ii < argc; ++ii)
    {

        if (strcmp(argv[ii], "--target")==0)
        {
            target=argv[ii + 1];
            ++ii;
        }
        else if (strcmp(argv[ii], "--endpoint")==0)
        {
            endpoint = argv[ii + 1];
            ++ii;
        }
        else if (strcmp(argv[ii], "--source") == 0)
        {
            source = argv[ii + 1];
            ++ii;
        }
        else if ((strcmp(argv[ii], "--help") == 0)||(strcmp(argv[ii],"-?")==0))
        {
            printf(" --target <target federate name>  ,the name of the federate to filter messages from\n");
            printf(" --endpoint <target endpoint name> , the name of the endpoint to send message to\n");
            printf(" --source <endpoint>, the name of the local endpoint to create\n");
            printf(" --help, -? display help\n");
            return 0;
        }

    }

    helicsFederateInfoLoadFromArgs(fedinfo, argc, (const char * const*)argv,&err);

    fFed = helicsCreateMessageFederate("ffed",fedinfo,&err);

    targetEndpoint = (char *)malloc(strlen(target) + 2 + strlen(endpoint));
    strcpy(targetEndpoint, target);
    strcat(targetEndpoint, "/");
    strcat(targetEndpoint, endpoint);

    str=helicsFederateGetName(fFed);
    printf("registering endpoint %s for %s\n", source, str);
    /*this line actually creates an endpoint */
    ept = helicsFederateRegisterEndpoint(fFed, source, "",&err);

    /* create a delay filter*/
    filt = helicsFederateRegisterFilter(fFed, helics_filter_type_delay, "filter", &err);
    helicsFilterAddSourceTarget(filt, targetEndpoint, &err);
    helicsFilterSet(filt, "delay", 0.5, &err);
    printf("initial delay set to 0.5\n");
    printf("entering init Mode\n");
    helicsFederateEnterInitializingMode(fFed,&err);
    printf("entered init Mode\n");
    helicsFederateEnterExecutingMode(fFed,&err);
    printf("entered execution Mode\n");
        newTime=helicsFederateRequestTime(fFed, 4.0, &err);
        
        printf("granted time %f\n", newTime);
        helicsFilterSet(filt, "delay", 1.5, &err);
        printf("delay set to 1.5\n");
        newTime = helicsFederateRequestTime(fFed, 8.0, &err);

        printf("granted time %f\n", newTime);
        helicsFilterSet(filt, "delay", 0.75, &err);
        printf("delay set to 0.75\n");
        /* request time at max*/
        newTime = helicsFederateRequestTime(fFed, 20.0, &err);
    printf("finalizing federate\n");
    helicsFederateDestroy(fFed);

    return 0;
}

