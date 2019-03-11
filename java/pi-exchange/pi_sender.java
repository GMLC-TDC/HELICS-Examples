import com.java.helics.helics;
import com.java.helics.*;
import java.util.concurrent.TimeUnit;

public class pi_sender {
	public static void main(String[] args) {
		System.loadLibrary("JNIhelics");

		System.out.println(helics.helicsGetVersion());
		SWIGTYPE_p_void broker1 = helics.helicsCreateBroker("zmq", "broker1", "--federates 2 --loglevel 1");
		if(broker1 == null) {
			return;
		}
		// Check if broker is connected
		int is_connected = helics.helicsBrokerIsConnected(broker1);
		if (is_connected != 1) {
			return;
		}
		SWIGTYPE_p_void fi = helics.helicsCreateFederateInfo();
		String coreInit="--federates=1";
		String fedName="TestA Federate";
		String coreName="zmq";
		double deltat=0.01;
		double currenttime=0.0;
		double value = 0.0;
		double[] val={0.0};
		double grantedtime=0.0;
		
		helics.helicsFederateInfoSetCoreTypeFromString(fi, coreName);
		helics.helicsFederateInfoSetCoreInitString(fi, coreInit);
		helics.helicsFederateInfoSetTimeProperty(fi,
				helics_time_properties.helics_time_property_input_delay.swigValue(), deltat);
		helics.helicsFederateInfoSetIntegerProperty(fi,
				helics_int_properties.helics_int_property_log_level.swigValue(), 1);
		
		SWIGTYPE_p_void vFed = helics.helicsCreateValueFederate(fedName, fi);

		SWIGTYPE_p_void pub = helics.helicsFederateRegisterGlobalPublication(vFed, "testA", helicsConstants.HELICS_DATA_TYPE_DOUBLE,"");

		helics.helicsFederateEnterInitializingMode(vFed);
		helics.helicsFederateEnterExecutingMode(vFed);
        for (int t = 5; t <= 100; t++) {
			grantedtime = helics.helicsFederateRequestTime(vFed, t );
			//System.out.printf("Current time:%f Requested time: %d\n", currenttime, t);
			try {
                TimeUnit.SECONDS.sleep(1);
            }
            catch(InterruptedException e) {
                System.out.println("exception occurred");
            }
			val[0] = val[0] + t*0.5;
			System.out.printf("Publishing: %f\n", val[0]);
            helics.helicsPublicationPublishDouble(pub, val[0]);
			currenttime=grantedtime;
		}

		helics.helicsFederateFinalize(vFed);
		helics.helicsCloseLibrary();
	}
}


