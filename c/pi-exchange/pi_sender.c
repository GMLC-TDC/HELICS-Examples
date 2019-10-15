/*
Copyright © 2017-2019,
Battelle Memorial Institute; Lawrence Livermore National Security, LLC; Alliance for Sustainable Energy, LLC.  See
the top-level NOTICE for additional details. All rights reserved.
SPDX-License-Identifier: BSD-3-Clause
*/
static char help[] = " PI SENDER: Simple program to demonstrate the usage of HELICS C Interface.\n\
            This example creates a ZMQ broker and a value federate.\n\
            The value federate creates a global publications and publishes\n\
            t*pi for 20 time-steps with a time-step of 0.01 seconds.\n\n";


#include <stdio.h>
#include <helics/shared_api_library/ValueFederate.h>
#ifdef _MSC_VER
#include <windows.h>
#else
#include <unistd.h>
#endif

int main()
{
  helics_federate_info fedinfo;
  const char*    helicsversion;
  /*helics_status   status; */
  helics_broker  broker;
  const char*    initstring="-f 2 --name=mainbroker";
  const char*    fedinitstring="--broker=mainbroker --federates=1";
  int            isconnected;
  double         deltat=0.01;
  helics_federate vfed;
  helics_publication pub;
  double value = 22.0 / 7.0;
  helics_time currenttime = 0.0;
  int           numsteps = 20, i;
  helics_error err = helicsErrorInitialize();

  helicsversion = helicsGetVersion();

  printf("PI SENDER: Helics version = %s\n",helicsversion);
  printf("%s",help);

  /* Create broker */
  broker = helicsCreateBroker("zmq","",initstring,NULL);

  isconnected = helicsBrokerIsConnected(broker);

  if(isconnected) {
    printf("PI SENDER: Broker created and connected\n");
  }

  /* Create Federate Info object that describes the federate properties */
  fedinfo = helicsCreateFederateInfo();

  /* Set core type from string */
   helicsFederateInfoSetCoreTypeFromString(fedinfo,"zmq",NULL);

  /* Federate init string */
  helicsFederateInfoSetCoreInitString(fedinfo,fedinitstring,NULL);

  /* Set the message interval (timedelta) for federate. Note that
     HELICS minimum message time interval is 1 ns and by default
     it uses a time delta of 1 second. What is provided to the
     setTimedelta routine is a multiplier for the default timedelta.
  */
  /* Set one second message interval */
  helicsFederateInfoSetTimeProperty(fedinfo, helics_property_time_period, deltat, &err);
  helicsFederateInfoSetIntegerProperty(fedinfo, helics_property_int_log_level, 1, &err);


  /* Create value federate */
  vfed = helicsCreateValueFederate("Test sender Federate",fedinfo,NULL);
  printf("PI SENDER: Value federate created\n");

  /* Register the publication */
  pub = helicsFederateRegisterGlobalPublication(vfed,"testA",helics_data_type_double,"",NULL);
  printf("PI SENDER: Publication registered\n");

  /* Enter initialization mode */
   helicsFederateEnterInitializingMode(vfed,NULL);
  printf("PI SENDER: Entered initialization mode\n");

  /* Enter execution mode */
   helicsFederateEnterExecutingMode(vfed,NULL);
  printf("PI SENDER: Entered execution mode\n");

  /* This federate will be publishing deltat*pi for numsteps steps */


  for(i=0; i < numsteps; i++) {
    double val = currenttime*value;

    printf("PI SENDER: Sending value %3.2fpi = %4.3f at time %3.2f to PI RECEIVER\n",deltat*i,val,currenttime);
    helicsPublicationPublishDouble(pub,val,NULL);

    currenttime=helicsFederateRequestTime(vfed,currenttime, NULL);
  }

  helicsFederateFinalize(vfed,NULL);
  printf("PI SENDER: Federate finalized\n");

  helicsFederateFree(vfed);
  while(helicsBrokerIsConnected(broker)) {
#ifdef _MSC_VER
      Sleep(100);
#else
    usleep(100000); /* Sleep for 100 millisecond */
#endif
  }
  printf("PI SENDER: Broker disconnected\n");
  helicsBrokerFree(broker);
  helicsCloseLibrary();
  return(0);
}

