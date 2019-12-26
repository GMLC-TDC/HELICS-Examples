/*
Copyright (c) 2017-2018,
Battelle Memorial Institute; Lawrence Livermore National Security, LLC; Alliance for Sustainable Energy, LLC
All rights reserved. See LICENSE file and DISCLAIMER for more details.
*/

static char help[] = "Example to demonstrate the usage of HELICS C Interface with two federates.\n\
            This example implements a loose-coupling protocol to exchange values between two federates. \n\
            Here, a value federate, that can both publish and subscribe is created.\n\
            This federate can only publish a value once it receives value from the other federate.\n\n";

#include <cstdio>
#include <helics/cpp98/ValueFederate.hpp>
#include <helics/cpp98/helics.hpp> // helicsVersionString
#include <cmath>

int main(int /*argc*/,char ** /*argv*/)
{
  std::string    fedinitstring="--federates=1";
  double         deltat=0.01;
  helicscpp::Input sub;
  helicscpp::Publication  pub;

  printf("PI RECEIVER: Helics version = %s\n", helicsGetVersion());
  printf("%s",help);

  /* Create Federate Info object that describes the federate properties
   * Set federate name and core type from string
   */
  helicscpp::FederateInfo fi( "zmq");

  /* Federate init string */
  fi.setCoreInit(fedinitstring);

  /* Set the message interval (timedelta) for federate. Note that
     HELICS minimum message time interval is 1 ns and by default
     it uses a time delta of 1 second. What is provided to the
     setTimedelta routine is a multiplier for the default timedelta.
  */
  /* Set one second message interval */
  fi.setProperty(helics_property_time_delta, deltat);
  fi.setProperty(helics_property_int_log_level, helics_log_level_warning);


  /* Create value federate */
  helicscpp::ValueFederate vfed("Test receiver Federate", fi);
  printf("PI RECEIVER: Value federate created\n");

  /* Subscribe to PI SENDER's publication */
  sub = vfed.registerSubscription("testA");
  printf("PI RECEIVER: Subscription registered\n");

  /* Register the publication */
  pub = vfed.registerGlobalPublication("testB","double");
  printf("PI RECEIVER: Publication registered\n");

  fflush(NULL);
  /* Enter initialization state */
  vfed.enterInitializingMode(); // can throw helicscpp::InvalidStateTransition exception
  printf("PI RECEIVER: Entered initialization state\n");

  /* Enter execution state */
  vfed.enterExecutingMode(); // can throw helicscpp::InvalidStateTransition exception
  printf("PI RECEIVER: Entered execution state\n");

  helics_time currenttime=0.0;

  double pi = 22.0/7.0;

  while(currenttime < 0.2) {

    bool isupdated = false;
    while(!isupdated) {
      currenttime = vfed.requestTime(currenttime);
      isupdated = sub.isUpdated();
      if (currenttime > 0.21)
      {
          break;
      }
    }
    double value = sub.getDouble(); /* Note: The sender sent this value at currenttime-deltat */
    printf("PI RECEIVER: Received value = %4.3f at time %3.2f from PI SENDER\n",value,currenttime);

    value = currenttime*pi;

    printf("PI RECEIVER: Sending value %3.2f*pi = %4.3f at time %3.2f to PI SENDER\n",currenttime,value,currenttime);
    pub.publish(value); /* Note: The sender will receive this at currenttime+deltat */
  }
  vfed.finalize();
  printf("PI RECEIVER: Federate finalized\n");
  fflush(NULL);
  helicsCloseLibrary();
  printf("PI RECEIVER: Library Closed\n");
  fflush(NULL);
  return(0);
}

