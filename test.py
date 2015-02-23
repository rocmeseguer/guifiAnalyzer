#!/usr/bin/env python
#
#test.py

import os
import sys
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.append('lib')
sys.path.append('lib/libcnml')
sys.path.append('lib/pyGuifiAPI')

from libcnml import CNMLParser, Status
import pyGuifiAPI
from pyGuifiAPI.error import GuifiApiError

#from configmanager import GuifinetStudioConfig

from utils import *


class GuifiNet:
	def __init__(self, cnmlFile=None):
		# GuifiAPI
		self.gui = pyGuifiAPI.GuifiAPI('edimoger', '100105a')
		print "Going to auth"
		try:
			gui.auth()
		except GuifiApiError, e:
			print e.reason
		print self.gui.is_authenticated()
		print self.gui.authToken

		if not cnmlFile:
			# Load default zone cnml
			try:
				fp = self.gui.downloadCNML(GUIFI_NET_WORLD_ZONE_ID, 'zones')
				filename = os.path.join(os.getcwd(),'cnml','GUIFI_NET_WORLD_ZONE_ID')
				with open(filename, 'w') as zonefile:
					zonefile.write(fp.read())
				print _('Zone saved successfully to'), filename
				self.cnmlFile = filename
			except URLError, e:
				print _('Error accessing to the Internet:'), str(e.reason)

        if cnmlFile:
        # CNMLParser
            try:
                self.cnmlp = CNMLParser(cnmlFile)
                self.cnmlFile = cnmlFile
            except IOError:
                self.cnmlp = None
                self.cnmlFile = None
                print _('Error opening CNML file')

        try:
            #self.zonecnmlp = CNMLParser(cnmlFile)
            self.zonecnmlp = cnmlp
            for z in self.zonecnmlp.getZones():
            	print _('Zone id:'), z.id
            	print _('Zone Title:'), z.title
                self.allZones.append((z.id, z.title))
        except IOError:
            print _('Error loading cnml guifiworld zone:'), cnmlFile
            self.zonecnmlp = None


if __name__ == "__main__":
    if len(sys.argv) > 1:
        GuifiNet(sys.argv[1])
    else:
        GuifiNet()