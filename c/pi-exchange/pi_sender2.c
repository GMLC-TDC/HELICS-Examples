/*
Copyright (c) 2017-2018,
Battelle Memorial Institute; Lawrence Livermore National Security, LLC; Alliance for Sustainable Energy, LLC
All rights reserved. See LICENSE file and DISCLAIMER for more details.
*/
static char help[] = "Example to demonstrate the usage of HELICS C Interface with two federates.\n\
            This example implements a loose-coupling protocol to exchange values between two federates. \n\
            Here, a ZMQ broker is created and a value federate. The value federate can both.\n\
            publish and subscribe. This federate publishes a value and waits for the value \n\
            published by the other federate. Once the value has arrived, it publishes its next value \n\n";

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
 /* helics_status   status; */
  helics_broker  broker;
  const char*    initstring="-f2 --name=mainbroker";
  const char*    fedinitstring="--federates=1";
  int            isconnected;
  double         deltat=0.01;
  helics_federate vfed;
  helics_publication pub;
  helics_input sub;
  helics_error err= helicsErrorInitialize();

  /* This federate will be publishing deltat*pi for numsteps steps */
  double pi = 22.0 / 7.0, value;
  helics_time currenttime = 0.0;

  helicsversion = helicsGetVersion();

  printf("PI SENDER: Helics version = %s\n",helicsversion);
  printf("%s",help);

  /* Create broker */
  broker = helicsCreateBroker("zmq","",initstring,&err);

  isconnected = helicsBrokerIsConnected(broker);

  if(isconnected) {
    printf("PI SENDER: Broker created and connected\n");
  }

  /* Create Federate Info object that describes the federate properties */
  fedinfo = helicsCreateFederateInfo();

  /* Set core type from string */
 helicsFederateInfoSetCoreTypeFromString(fedinfo,"zmq",&err);

  /* Federate init string */
   helicsFederateInfoSetCoreInitString(fedinfo,fedinitstring,&err);

  /* Set the message interval (timedelta) for federate. Note that
     HELICS minimum message time interval is 1 ns and by default
     it uses a time delta of 1 second. What is provided to the
     setTimedelta routine is a multiplier for the default timedelta.
  */

  helicsFederateInfoSetTimeProperty(fedinfo, helics_property_time_period, deltat,&err);
  helicsFederateInfoSetIntegerProperty(fedinfo, helics_property_int_log_level, 1, &err);

  /* Create value federate */
  vfed = helicsCreateValueFederate("TestA Federate",fedinfo,&err);
  printf("PI SENDER: Value federate created\n");

  /* Register the publication */
  pub = helicsFederateRegisterGlobalPublication(vfed,"testA",helics_data_type_double,"",&err);
  printf("PI SENDER: Publication registered\n");

  /* Subscribe to PI SENDER's publication */
  sub = helicsFederateRegisterSubscription(vfed,"testB",NULL,&err);
  printf("PI SENDER: Subscription registered\n");
  fflush(NULL);
  /* Register the subscription */

  /* Enter initialization mode */
  helicsFederateEnterInitializingMode(vfed,NULL);
  printf("PI SENDER: Entered initialization mode\n");

  /* Enter execution mode */
 helicsFederateEnterExecutingMode(vfed,NULL);
  printf("PI SENDER: Entered execution mode\n");

  while(currenttime < 0.2) {
      int  isupdated = 0;
    value = currenttime*pi;

    printf("PI SENDER: Sending value %3.2f*pi = %4.3f at time %3.2f to PI RECEIVER\n",currenttime,value,currenttime);
     helicsPublicationPublishDouble(pub,value,&err); /* Note: the receiver will get this at currenttime+deltat */

    while(!isupdated) {
      currenttime=helicsFederateRequestTime(vfed,currenttime, &err);
      isupdated = helicsInputIsUpdated(sub);
    }

    /* NOTE: The value sent by sender at time t is received by receiver at time t+deltat */
    value=helicsInputGetDouble(sub,&err); /* Note: The receiver sent this at currenttime-deltat */
    printf("PI SENDER: Received value = %4.3f at time %3.2f from PI RECEIVER\n",value,currenttime);
  }

   helicsFederateDestroy(vfed);
  printf("PI SENDER: Federate finalized\n");

  helicsBrokerWaitForDisconnect(broker,-1,&err);

  helicsBrokerFree(broker);
  printf("PI SENDER: Broker disconnected\n");
  helicsCloseLibrary();
  printf("PI SENDER: Library closed\n");
  fflush(NULL);
  return(0);
}

