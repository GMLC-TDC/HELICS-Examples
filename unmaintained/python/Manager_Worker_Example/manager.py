from federate import Federate
import helics as h

def check_values_returned(n, a):
	arr = [False] * n
	check = False
	while not check:
		for i in range(n):
			if h.helicsInputIsUpdated(a.sub[i]) == 0:
				arr[i] = False
			else:
				arr[i] = True
		if False in arr:
			time = h.helicsFederateRequestTime(a.vfed, 0)
			check = False
		else:
			check = True
	return time	

helicsversion = h.helicsGetVersion()
print("Manager: Helics version = {}".format(helicsversion))

n = 5

a = Federate()
a.create_federate("Manager federate")
a.publish("manager", "double")

for i in range(n):
	a.subscribe(str("worker" + str(i)))
a.start()

print("Manager: Entering execution mode")
currenttime = -1
for time_s in range(11):
	currenttime = h.helicsFederateRequestTime(a.vfed, time_s)
	val = time_s + 1
	h.helicsPublicationPublishDouble(a.pub[0], val)
	print("Manager: Sending value =" ,val, "at time =", currenttime , " to Workers")
	print("Manager waiting for workers to send value back")
	currenttime = check_values_returned(n, a)
	for i in range(n):
		val = h.helicsInputGetDouble(a.sub[i])
		print("Manager: Received value =", val," at time =", currenttime, " from Worker", i)
	print("---------------------------------------------------------------------------")
a.destroy()
print("federates finalized")
h.helicsCloseLibrary()
