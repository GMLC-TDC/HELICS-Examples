from federate import Federate
import helics as h
import random
import time

helicsversion = h.helicsGetVersion()
print("Worker: Helics version = {}".format(helicsversion))

fed = []
n = 5

def check_values_updated(n, fed):
	arr = [False] * n
	check = False
	time = [0] * n
	while not check:
		for i in range(n):
			time[i] = h.helicsFederateRequestTime(fed[i].vfed, 0)		
		for i in range(n):
			if h.helicsInputIsUpdated(fed[i].sub[0]) == 0:
				arr[i] = False
			else:
				arr[i] = True
		if False in arr:
      			check = False
		else:
			check = True
	return time

for i in range(n):
	
	fed.append(Federate())
	fed_name = str("worker" + str(i) + "federate")
	fed[i].create_federate(fed_name)
	fed[i].subscribe("manager")
	pub_name = str('worker' + str(i))
	fed[i].publish(pub_name, "double")

for i in range(n):
	fed[i].start_async()

for i in range(n):
	h.helicsFederateEnterExecutingModeComplete(fed[i].vfed)	
#	print(i, "started")

currenttime = [0] * n

for i in range(n):
	currenttime[i] = h.helicsFederateRequestTime(fed[i].vfed, 0)

it = 0
num_it = 0
while not it == 11:
	currenttime = check_values_updated(n, fed)	

	for i in range(n):
		value = h.helicsInputGetDouble(fed[i].sub[0])
		print("Worker", i, ": Received value =", value ,"at time =", currenttime[i],"from Manager")
		value = value * (i+2)
		time.sleep(random.randrange(2))			
		h.helicsPublicationPublishDouble(fed[i].pub[0], value)
		print("Worker", i, ": Sending value =", value, "at time =", currenttime[i],"to Manager")
		print("-----------------------------------------------------------")
		if i == n - 1:
			it = it + 1
for i in fed:
	i.destroy()

print("federates finalized")
h.helicsCloseLibrary()
