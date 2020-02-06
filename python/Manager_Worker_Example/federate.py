import helics as h

class Federate:
	""" Federate Class """
	def __init__(self, core_type = "zmq", time_delta = 1):
		self.__fedinfo = h.helicsCreateFederateInfo()
		h.helicsFederateInfoSetCoreName(self.__fedinfo, "")
		h.helicsFederateInfoSetCoreTypeFromString(self.__fedinfo, core_type)
		h.helicsFederateInfoSetCoreInitString(self.__fedinfo, "--federates=1")
		h.helicsFederateInfoSetTimeProperty(self.__fedinfo, h.helics_property_time_delta, time_delta)
		self.vfed = ""
		self.pub = []
		self.sub = []		

	def create_federate(self, fed_name):
		self.vfed = h.helicsCreateCombinationFederate(str(fed_name), self.__fedinfo)

	def publish(self, name, data_type):
		self.pub.append(h.helicsFederateRegisterGlobalTypePublication(self.vfed, name, data_type, ""))

	def subscribe(self, target):
		self.sub.append(h.helicsFederateRegisterSubscription(self.vfed, target, ""))

	def destroy(self):
		h.helicsFederateFinalize(self.vfed)
		h.helicsFederateFree(self.vfed)
#		print("Federate: Federate finalized")

	def start_async(self):
		h.helicsFederateEnterExecutingModeAsync(self.vfed)	
	def start(self):
		h.helicsFederateEnterExecutingMode(self.vfed)
