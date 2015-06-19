#!/usr/bin/env python
#
#snpservicesClient.py

import urllib2
import sys


commands = ["help","version","phpinfo","serverinfo"]
services = ["availability","example","graph","liveping","livetraceroute","stats"]



def snpRequest(ip,command="help",args={},debug=False, timeout = 3):
	"""
	Request to snpservices server

	args: dictionary {"arg1":[val1],"arg2":[val2,val3]}

	Throws URLError exception
	"""
	if command not in commands and command not in services:
		print("Wrong request arguments")
		return -1
	else:
		base = "http://"+str(ip)+"/snpservices/index.php?call="+command
		# Add arguments
		arguments = ""
		for arg in args:
			arguments += "&"+str(arg)
			if args[arg] :
				arguments += "="
				for i in args[arg]:
					if i == args[arg][-1] :
						print i
						arguments += str(i)
					else:
						#print i
						arguments += str(i)+","
		# Make request				
		url = base + arguments
		print("SNPServices request to graph server: %s"%url)
		req = urllib2.Request(url)
		response=urllib2.urlopen(req,timeout=timeout)
		data = response.read()
		return data
	        