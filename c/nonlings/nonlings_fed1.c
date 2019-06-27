/*
Copyright © 2017-2018,
Battelle Memorial Institute; Lawrence Livermore National Security, LLC; Alliance for Sustainable Energy, LLC
All rights reserved. See LICENSE file and DISCLAIMER for more details.
*/

/*
   Example from http://mathfaculty.fullerton.edu/mathews//n2003/newtonsystem/newtonsystemproof.pdf.
*/
#include <helics/shared_api_library/ValueFederate.h>
#include <math.h>
#include <stdio.h>

/* This solves the system being simulated by this simulator. It takes in the coupling variable
   y and returns the state variable x and the converged status conv
*/
void run_sim1(double y,double tol,double *xout,int *converged)
{
  double x = *xout;
  int newt_conv = 0, max_iter = 10, iter = 0;
  /* Solve the equation using Newton */
  while (!newt_conv && iter < max_iter) {
      double J1;
    /* Function value */
    double f1 = x * x - 2 * x - y + 0.5;

    /* Convergence check */
    if (fabs (f1) < tol) {
      newt_conv = 1;
      break;
    }
    iter++;

    /* Jacobian */
    J1 = 2 * x - 2;

    /* Update */
    x = x - f1 / J1;
  }
  *converged = newt_conv;
  *xout = x;
}

int main ()
{
    helics_federate_info fedinfo;
    const char *helicsversion;
    helics_broker broker;
    const char *initstring = "-f 2 --name=mainbroker";
    const char *fedinitstring = "--broker=mainbroker --federates=1";
    int isconnected;
    double deltat = 0.01;
    helics_federate vfed;
    helics_publication pub;
    helics_input sub;
    int converged;
    int actualStringSize;
    char sendbuf[100],recvbuf[100];
        double x = 0.0, y = 1.0, xprv=100;
    helics_time currenttime = 0.0;
    helics_iteration_result currenttimeiter=helics_iteration_result_iterating;
    double tol = 1E-8;
    int my_conv=0,other_conv; /* Global and local convergence */
    int helics_iter = 0;
	helics_error err = helicsErrorInitialize();

    helicsversion = helicsGetVersion ();

    printf (" Helics version = %s\n", helicsversion);

    /* Create broker */
    broker = helicsCreateBroker ("zmq", "", initstring,&err);

    isconnected = helicsBrokerIsConnected (broker);

    if (isconnected) {
      printf (" Broker created and connected\n");
    }

    /* Create Federate Info object that describes the federate properties */
    fedinfo = helicsCreateFederateInfo ();


    /* Set core type from string */
     helicsFederateInfoSetCoreTypeFromString (fedinfo, "zmq",&err);

    /* Federate init string */
     helicsFederateInfoSetCoreInitString (fedinfo, fedinitstring,&err);

	 /* Set one second message interval */
	 helicsFederateInfoSetTimeProperty(fedinfo, helics_property_time_period, deltat, &err);
	 helicsFederateInfoSetIntegerProperty(fedinfo, helics_property_int_max_iterations, 100, &err);

    /*status = helicsFederateInfoSetLoggingLevel (fedinfo, 5); */

    /* Create value federate */
    vfed = helicsCreateValueFederate ("TestA Federate",fedinfo,&err);
    printf (" Value federate created\n");

    /* Register the publication */
    pub = helicsFederateRegisterGlobalTypePublication (vfed, "testA", "string", "",&err);
    printf (" Publication registered\n");

    /* Register the subscription */
    sub = helicsFederateRegisterSubscription (vfed, "testB", "",&err);
    printf (" Subscription registered\n");

    /* Enter initialization mode */
    helicsFederateEnterInitializingMode (vfed,&err);
    if (err.error_code == helics_ok) {
      printf(" Entered initialization mode\n");
    } else {
      return (err.error_code);
    }

    snprintf(sendbuf,100,"%18.16f,%d",x,my_conv);
    helicsPublicationPublishString(pub, sendbuf,&err);
    /* Enter execution mode */
    helicsFederateEnterExecutingMode (vfed,&err);
    if (err.error_code == helics_ok) {
      printf(" Entered execution mode\n");
    } else {
      return (err.error_code);
    }

    fflush (NULL);


    while (currenttimeiter == helics_iteration_result_iterating) {
        int global_conv;
      helicsInputGetString(sub, recvbuf,100, &actualStringSize,&err);
      sscanf(recvbuf,"%lf,%d",&y,&other_conv);

      /* Check for global convergence */
      global_conv = my_conv&other_conv;

      if(global_conv) {
		  currenttime=helicsFederateRequestTimeIterative(vfed, currenttime, helics_iteration_request_no_iteration,&currenttimeiter,&err);
      } else {

	/* Solve the system of equations for this federate */
	run_sim1(y,tol,&x,&converged);

	++helics_iter;
	printf("Fed1: Current time %4.3f iteration %d x=%f, y=%f\n",currenttime,helics_iter, x, y);

	if ((fabs(x-xprv)>tol)) {
	  my_conv = 0;
	  printf("Fed1: publishing new x\n");
	} else {
	  my_conv = 1;
	  printf("Fed1: converged\n");
	}

	snprintf(sendbuf,100,"%18.16f,%d",x,my_conv);
	helicsPublicationPublishString(pub, sendbuf,&err);

	fflush(NULL);

	currenttime=helicsFederateRequestTimeIterative(vfed, currenttime, helics_iteration_request_force_iteration,&currenttimeiter,&err);
	xprv = x;
      }
    }

    helicsFederateFinalize(vfed,&err);
    printf ("NLIN1: Federate finalized\n");
    fflush (NULL);
    helicsFederateFree (vfed);
	helicsBrokerWaitForDisconnect(broker, -1, &err);
    
    helicsBrokerFree(broker);
    printf ("NLIN1: Broker disconnected\n");
    helicsCloseLibrary ();
    printf ("NLIN1: Library closed\n");
    fflush (NULL);
    return (0);
}

