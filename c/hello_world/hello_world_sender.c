/*
Copyright (c) 2017-2019,
Battelle Memorial Institute; Lawrence Livermore National Security, LLC; Alliance for Sustainable Energy, LLC.  See
the top-level NOTICE for additional details. All rights reserved.
SPDX-License-Identifier: BSD-3-Clause
*/

/* include the HELICS header for value Federates*/
#include <helics/shared_api_library/ValueFederate.h>
#include <stdio.h>

int main() {
  helics_federate_info fedinfo; /* an information object used to pass information to a federate*/
  const char*    fedinitstring="--federates=1"; /* tell the core to expect only 1 federate*/
  helics_federate vfed; /* object representing the actual federate*/
  helics_publication pub; /* an object representing a publication*/
  helics_time currenttime = 0.0; /* the current time of the simulation*/
  helics_error  err=helicsErrorInitialize();/* the result code from a call to the helics Library*/
  /** create an info structure to define some parameters used in federate creation*/
  fedinfo = helicsCreateFederateInfo();

  /** set the core type to use
  can be "test", "ipc", "udp", "tcp", "zmq", "mpi"
  not all are available on all platforms
  and should be set to match the broker and receiver
  zmq is the default*/
  helicsFederateInfoSetCoreTypeFromString(fedinfo,"zmq",&err);
  helicsFederateInfoSetCoreInitString(fedinfo,fedinitstring,&err);
  /** set the period of the federate to 1.0 get the period using the getPropertyIndex function with a string
  if could also be set directly using the enumeration helics_property_time_period*/
  helicsFederateInfoSetTimeProperty(fedinfo,helicsGetPropertyIndex("period"), 1.0,&err);

  /** create the value federate using the informational structure*/
  vfed = helicsCreateValueFederate("hello_world_sender",fedinfo,&err);

  /** free the federateInfo structure when no longer needed*/
  helicsFederateInfoFree(fedinfo);
  if (err.error_code != helics_ok) /*check to make sure the federate was created*/
  {
      return (-2);
  }
  /** register a publication interface on vFed, with a global Name of "hello"
  of a type "string", with no units*/
  pub = helicsFederateRegisterGlobalPublication(vfed, "hello", helics_data_type_string, "",&err);
  if (err.error_code != helics_ok) /*check to make sure the publication was created*/
  {
      return (-3);
  }
  /** transition the federate to execution mode
  * the helicsFederateEnterInitializationMode is not necessary if there is nothing to do in the initialization mode
  */
  helicsFederateEnterInitializingMode(vfed,&err);
  if (err.error_code != helics_ok)
  {
      fprintf(stderr, "HELICS failed to enter initialization mode:%s\n",err.message);
  }
  helicsFederateEnterExecutingMode(vfed,&err);
  if (err.error_code != helics_ok)
  {
      fprintf(stderr, "HELICS failed to enter initialization mode:%s\n",err.message);
  }
  /** the federate is now at time 0*/
  /** publish the Hello World string this will show up at the next time step of an subscribing federates*/
  helicsPublicationPublishString(pub, "Hello, World",&err);
  /** request that helics grant the federate a time of 1.0*/
  currenttime=helicsFederateRequestTime(vfed, 1.0, &err);
  if (err.error_code!=helics_ok)
  {
      fprintf(stderr, "HELICS request time failed:%s\n",err.message);
  }
  else
  {
      fprintf(stdout, "HELICS granted time:%f\n", currenttime);
  }
  /** finalize the federate*/
  helicsFederateFinalize(vfed,&err);
  /** free the memory allocated to the federate*/
  helicsFederateFree(vfed);
  /** close the helics library*/
  helicsCloseLibrary();
  return(0);
}

