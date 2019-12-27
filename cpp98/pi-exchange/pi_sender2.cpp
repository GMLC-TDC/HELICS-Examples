/*
Copyright (c) 2017-2019,
Battelle Memorial Institute; Lawrence Livermore National Security, LLC; Alliance for Sustainable Energy, LLC.  See the top-level NOTICE for
additional details. All rights reserved.
SPDX-License-Identifier: BSD-3-Clause
*/
static char help[] = "Example to demonstrate the usage of HELICS Cpp98 Interface with two federates.\n\
            This example implements a loose-coupling protocol to exchange values between two federates. \n\
            Here, a ZMQ broker is created and a value federate. The value federate can both.\n\
            publish and subscribe. This federate publishes a value and waits for the value \n\
            published by the other federate. Once the value has arrived, it publishes its next value \n\n";

#include <cstdio>
#include <helics/cpp98/ValueFederate.hpp>
#include <helics/cpp98/Broker.hpp>
#include <helics/cpp98/helics.hpp> // helicsVersionString


int main(int /*argc*/,char ** /*argv*/)
{
  std::string    initstring="-f 2 --name=mainbroker";
  std::string    fedinitstring="--federates=1";
  double         deltat=0.01;
  helicscpp::Publication pub;
 helicscpp::Input sub;

  std::string helicsversion = helicscpp::getHelicsVersionString();

  printf("PI SENDER: Helics version = %s\n",helicsversion.c_str());
  printf("%s",help);

  /* Create broker */
  helicscpp::Broker broker("zmq","",initstring);

  if(broker.isConnected()) {
    printf("PI SENDER: Broker created and connected\n");
  }

  /* Create Federate Info object that describes the federate properties
   * Sets federate name and core type from string
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
  helicscpp::ValueFederate* vfed = new helicscpp::ValueFederate("TestA Federate", fi);
  printf("PI SENDER: Value federate created\n");

  /* Register the publication */
  pub = vfed->registerGlobalPublication("testA","double");
  printf("PI SENDER: Publication registered\n");

  /* Subscribe to PI SENDER's publication */
  sub = vfed->registerSubscription("testB","double");
  printf("PI SENDER: Subscription registered\n");
  fflush(NULL);
  /* Register the subscription */

  /* Enter initialization state */
  vfed->enterInitializingMode(); // can throw helicscpp::InvalidStateTransition exception
  printf("PI SENDER: Entered initialization state\n");

  /* Enter execution state */
  vfed->enterExecutingMode(); // can throw helicscpp::InvalidStateTransition exception
  printf("PI SENDER: Entered execution state\n");

  /* This federate will be publishing deltat*pi for numsteps steps */
  //double this_time = 0.0;
  double pi = 22.0/7.0;
  helics_time currenttime=0.0;

  while(currenttime < 0.2) {
    double value = currenttime*pi;

    printf("PI SENDER: Sending value %3.2f*pi = %4.3f at time %3.2f to PI RECEIVER\n",currenttime,value,currenttime);
    pub.publish( value); /* Note: the receiver will get this at currenttime+deltat */

    int isupdated = 0;
    while(!isupdated) {
      currenttime = vfed->requestTime(currenttime);
      isupdated = sub.isUpdated();
    }

    /* NOTE: The value sent by sender at time t is received by receiver at time t+deltat */
    value = sub.getDouble(); /* Note: The receiver sent this at currenttime-deltat */
    printf("PI SENDER: Received value = %4.3f at time %3.2f from PI RECEIVER\n",value,currenttime);
  }

  vfed->finalize();
  printf("PI SENDER: Federate finalized\n");

  // Destructor must be called before closing the library
  delete vfed;
  broker.waitForDisconnect();
 
  printf("PI SENDER: Broker disconnected\n");
  helicsCloseLibrary();
  printf("PI SENDER: Library closed\n");
  fflush(NULL);
  return(0);
}

