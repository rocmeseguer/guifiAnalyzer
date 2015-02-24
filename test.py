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

from urllib2 import URLError

import gettext
_ = gettext.gettext



class GuifiNet:
    def __init__(self, cnmlFile=None):
        # GuifiAPI
        self.gui = pyGuifiAPI.GuifiAPI('edimoger', '100105a')
        self.allZones = []
        print "Going to auth"
        try:
            self.gui.auth()
        except GuifiApiError, e:
            print e.reason
        print self.gui.is_authenticated()
        print self.gui.authToken

        if not cnmlFile:
            # Load default zone cnml
            print "Download World CNML"
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
            print "Using indicated CNML file"
            self.cnmlFile = cnmlFile

        # CNMLParser
        print "CNML Parser"
        try:
            self.cnmlp = CNMLParser(self.cnmlFile)
            try:
                #self.zonecnmlp = CNMLParser(cnmlFile)
                self.zonecnmlp = self.cnmlp
                for z in self.zonecnmlp.getZones():
                    print _('Zone id:'), z.id
                    print _('Zone Title:'), z.title
                    self.allZones.append((z.id, z.title))
            except IOError:
                print _('Error loading cnml guifiworld zone:'), self.cnmlFile
                self.zonecnmlp = None
        except IOError:
            self.cnmlp = None
            self.cnmlFile = None
            print _('Error opening CNML file')




if __name__ == "__main__":
    if len(sys.argv) > 1:
        GuifiNet(sys.argv[1])
    else:
        GuifiNet()