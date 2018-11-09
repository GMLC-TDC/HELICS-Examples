import com.java.helics.helics;
import com.java.helics.*;
import java.util.concurrent.TimeUnit;

public class pi_receiver {
	public static void main(String[] args) {
		System.loadLibrary("JNIhelics");
		//System.loadLibrary("helicsSharedLib");

		System.out.println(helics.helicsGetVersion());
		System.out.println("pi_receiver_java");
		SWIGTYPE_p_void fi = helics.helicsCreateFederateInfo();
		String coreInit="--federates=1";
		String fedName="TestB Federate";
		String coreName="zmq";
		double deltat=0.01;
		double currenttime=0.0;
		double value = 0.0;
		double val = 0.0;
		double[] grantedtime={0.0};
		helics.helicsFederateInfoSetCoreName(fi, fedName);
		helics.helicsFederateInfoSetCoreTypeFromString(fi, coreName);
		helics.helicsFederateInfoSetCoreInitString(fi, coreInit);

		helics.helicsFederateInfoSetTimeProperty(fi,
				helics_time_properties.helics_time_property_input_delay.swigValue(), deltat);
		helics.helicsFederateInfoSetIntegerProperty(fi,
				helics_int_properties.helics_int_property_log_level.swigValue(), 1);
		//helics.helicsFederateInfoFree(fi);
		
		SWIGTYPE_p_void vFed = helics.helicsCreateValueFederate(fedName, fi);

		SWIGTYPE_p_void sub = helics.helicsFederateRegisterSubscription(vFed, "testA", "");

		helics.helicsFederateEnterInitializingMode(vFed);
		helics.helicsFederateEnterExecutingMode(vFed);
		currenttime = helics.helicsFederateRequestTime(vFed, 100);

		int isupdated = helics.helicsInputIsUpdated(sub);

		while(currenttime <= 100) {
			currenttime = helics.helicsFederateRequestTime(vFed, 100);
//			try {
//                TimeUnit.SECONDS.sleep(1);
//            }
//            catch(InterruptedException e) {
//                System.out.println("exception occurred");
//            }
            isupdated = helics.helicsInputIsUpdated(sub);
			if(isupdated==1) {
			      /* NOTE: The value sent by sender at time t is received by receiver at time t+deltat */
				  val = helics.helicsInputGetDouble(sub);
				  System.out.printf("PI RECEIVER: Received value = %4.3f at time %3.2f from PI SENDER\n",val,currenttime);
			}
		}
		helics.helicsFederateFinalize(vFed);
		helics.helicsCloseLibrary();
	}
}

