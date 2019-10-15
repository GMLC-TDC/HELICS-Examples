/*
Copyright © 2017-2019,
Battelle Memorial Institute; Lawrence Livermore National Security, LLC; Alliance for Sustainable Energy, LLC.  See
the top-level NOTICE for additional details. All rights reserved.
SPDX-License-Identifier: BSD-3-Clause
*/
static char help[] = "Example to demonstrate the usage of HELICS C Interface with two federates.\n\
            This example implements a loose-coupling protocol to exchange values between two federates. \n\
            Here, a value federate, that can both publish and subcribe is created.\n\
            This federate can only publish a value once it receives value from the other federate.\n\n";

#include <stdio.h>
#include <helics/shared_api_library/ValueFederate.h>
#include <math.h>

int main()
{
  helics_federate_info fedinfo;
  const char*    helicsversion;
  const char*    fedinitstring="--federates=1";
  double         deltat=0.01;
  helics_federate vfed;
  helics_input sub;
  helics_error err = helicsErrorInitialize();
  helics_publication  pub;
  helics_time currenttime = 0.0;
  double        value = 0.0;
  double pi = 22.0 / 7.0;

  helicsversion = helicsGetVersion();


  printf("PI RECEIVER: Helics version = %s\n",helicsversion);
  printf("%s",help);

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
  /* Set one second message interval */
   helicsFederateInfoSetTimeProperty(fedinfo,helics_property_time_delta,deltat,NULL);

  helicsFederateInfoSetIntegerProperty(fedinfo,helics_property_int_log_level,1,NULL);

  /* Create value federate */
  vfed = helicsCreateValueFederate("Test receiver Federate",fedinfo,&err);
  printf("PI RECEIVER: Value federate created\n");

  /* Subscribe to PI SENDER's publication */
  sub = helicsFederateRegisterSubscription(vfed,"testA","",&err);
  printf("PI RECEIVER: Subscription registered\n");

  /* Register the publication */
  pub = helicsFederateRegisterGlobalTypePublication(vfed,"testB","double","",&err);
  printf("PI RECEIVER: Publication registered\n");

  fflush(NULL);
  /* Enter initialization mode */
  helicsFederateEnterInitializingMode(vfed, &err);
  if (err.error_code!= helics_ok)
  {
      printf("PI RECEIVER: Entered initialization mode\n");
  }
  else
  {
      return (-3);
  }


  /* Enter execution mode */
  helicsFederateEnterExecutingMode(vfed, &err);
  if (err.error_code != helics_ok)
  {
      printf("PI RECEIVER: Entered execution mode\n");
  }


  while(currenttime < 0.2) {

     int isupdated = 0;
    while(!isupdated) {
      currenttime=helicsFederateRequestTime(vfed,currenttime, &err);
      isupdated = helicsInputIsUpdated(sub);
      if (currenttime > 0.21)
      {
          break;
      }
    }
    value=helicsInputGetDouble(sub,&err); /* Note: The sender sent this value at currenttime-deltat */
    printf("PI RECEIVER: Received value = %4.3f at time %3.2f from PI SENDER\n",value,currenttime);

    value = currenttime*pi;

    printf("PI RECEIVER: Sending value %3.2f*pi = %4.3f at time %3.2f to PI SENDER\n",currenttime,value,currenttime);
    helicsPublicationPublishDouble(pub,value,&err); /* Note: The sender will receive this at currenttime+deltat */
  }
  helicsFederateFinalize(vfed,&err);
  printf("PI RECEIVER: Federate finalized\n");
  fflush(NULL);
  /*clean upFederate*/
  helicsFederateFree(vfed);
  helicsCloseLibrary();
  printf("PI RECEIVER: Library Closed\n");
  fflush(NULL);
  return(0);
}

