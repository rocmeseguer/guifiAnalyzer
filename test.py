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

import json

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
        zone = int(raw_input("Select a zone: "))
        print _('Parsing:'), zone
        #self.world = self.getZoneCNML(3671)
        self.zone = self.parseZoneCNML(zone)
        print "Find all link types"
        linkType = {}
        for link in self.zone.getLinks():
            if not linkType[link.type]:
                linkType.update({link.type:1})
            else:
                counter = linkType[link.type]
                linkType.update({})
        print _('Link Types:'), linkType
        print "Find all iface types"
        ifaceType = {}
        for iface in self.zone.getInterfaces():
            if iface.type not in ifaceType:
                ifaceType.append(iface.type)

        print _('IFace Types:'), ifaceType

        


    def createTopoJSON(self):
        nodesFile = os.path.join(os.getcwd(),"topo.js")
        fpTopo = open(nodesFile,"w")
        print>> fpTopo, "var nodes = ["
        for node in self.zone.getNodes():
            entry = {"id": node.id}
            fpTopo.write("%s,\n" % json.dumps(entry))
        print>> fpTopo, "];\n"
        print>> fpTopo, "var edges = ["
        for link in self.zone.getLinks():
            #if link.link_status == "Working" and  
            #entry = { "from": link.nodeA.id, "to": link.nodeB.id},
            #print _('The entry is: '), entry
            #fpTopo.write("%s,\n" % json.dumps(entry))
            print _('Link type'), link.type
        print>> fpTopo, "];"
        fpTopo.close()






    #     if not cnmlFile:
    #         # Load default zone cnml
    #         print "Download World CNML"
    #         try:
    #             fp = self.gui.downloadCNML(GUIFI_NET_WORLD_ZONE_ID, 'zones')
    #             filename = os.path.join(os.getcwd(),'cnml',str(GUIFI_NET_WORLD_ZONE_ID))
    #             with open(filename, 'w') as zonefile:
    #                 zonefile.write(fp.read())
    #             print _('Zone saved successfully to'), filename
    #             self.cnmlFile = filename
    #         except URLError, e:
    #             print _('Error accessing to the Internet:'), str(e.reason)

    #     if cnmlFile:
    #         print "Using indicated CNML file"
    #         self.cnmlFile = cnmlFile


    # def saveZones(self):
    #     # CNMLParser
    #     print "CNML Parser"
    #     try:
    #         self.cnmlp = CNMLParser(self.cnmlFile)
    #         try:
    #             #self.zonecnmlp = CNMLParser(cnmlFile)
    #             self.zonecnmlp = self.cnmlp
    #             for z in self.zonecnmlp.getZones():
    #                 #print _('Zone id:'), z.id
    #                 #print _('Zone Title:'), z.title
    #                 self.allZones.append((z.id, z.title))
    #         except IOError:
    #             print _('Error loading cnml guifiworld zone:'), self.cnmlFile
    #             self.zonecnmlp = None
    #     except IOError:
    #         self.cnmlp = None
    #         self.cnmlFile = None
    #         print _('Error opening CNML file')


    def parseZoneCNML(self,zone):
        zonefile = os.path.join(os.getcwd(),'cnml',str(zone))
        if not os.path.isfile(zonefile):
            print "Cannot find zone locally. Will download"
            zonefile = self.getZoneCNML(zone)

        try:
            return CNMLParser(zonefile)
        except  IOError:
            print _('Error opening CNML file: ' ), zonefile

    def getZoneCNML(self,zone):
        # Download zone cnml and get links
        print "Get links and their nodes of a zone"
        if  not zone:
            zone = raw_input("Select a zone: ")
        try:
            fp = self.gui.downloadCNML(int(zone), 'detail')
            filename = os.path.join(os.getcwd(),'cnml',str(zone))
            with open(filename, 'w') as zonefile:
                zonefile.write(fp.read())
            print _('Zone saved successfully to'), filename
            return filename
        except URLError, e:
            print _('Error accessing to the Internet:'), str(e.reason)




        # # Find the relevant links
        # print "Find the relevant links"
        # try:
        #     zonecnmlp = CNMLParser(zonefile)
        #     try:
        #         for z in zonecnmlp.getLinks():
        #             print "Found a link"
        #             print _('Link id:'), z.id
        #             print _('Node A:'), z.nodeA
        #             print _('Node B:'), z.nodeB
        #     except IOError:
        #         print _('Error loading cnml guifiworld zone:'), self.cnmlFile
        # except IOError:
        #     print _('Error opening CNML file')


if __name__ == "__main__":
    if len(sys.argv) > 1:
        GuifiNet(sys.argv[1])
    else:
        GuifiNet()