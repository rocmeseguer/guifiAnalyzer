#exceptions.py

class NoWorkingIPError(Exception):
	def __init__(self, service, ipBlackList):
		self.service = service
		self.ipBlackList = ipBlackList
	def __str__(self):
		msg = "No working ip found for service " + str(self.service.id)
		return repr(msg)


class ServerMisconfiguredError(Exception):
	def __init__(self, service):
		self.service = service
	def __str__(self):
		msg = "Service " + str(self.service.id) + " is misconfigured!"
		return repr(msg)


class NoCNMLServerError(Exception):
	def __init__(self, device):
		self.device = device
	def __str__(self):
		msg = "Cannot find Graph server in CNML for device "+ str(self.device.id) +", or graphServer not in WORKING status " 
		return repr(msg)