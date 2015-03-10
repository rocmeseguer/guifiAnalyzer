#!/usr/bin/env python
#
#test.py

import os
import sys
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.append('lib')
#sys.path.append('lib/libcnml')
sys.path.append('lib/pyGuifiAPI')

import libcnml
import logging
libcnml.logger.setLevel(logging.DEBUG)

import pyGuifiAPI
from pyGuifiAPI.error import GuifiApiError

#from configmanager import GuifinetStudioConfig

from utils import *

from urllib2 import URLError

import gettext
_ = gettext.gettext

import json
import operator

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
        #for n in self.zone.nodes:
        #    print self.zone.nodes[n].status
        self.zone.nodes =  {i: self.zone.nodes[i] for i in self.zone.nodes if self.zone.nodes[i].status == libcnml.Status.WORKING}


    def dump(self,obj):
        for attr in dir(obj):
            print "obj.%s = %s" % (attr, getattr(obj, attr))


    def parseZoneCNML(self,zone):
        zonefile = os.path.join(os.getcwd(),'cnml',str(zone))
        if not os.path.isfile(zonefile):
            print "Cannot find zone locally. Will download"
            zonefile = self.getZoneCNML(zone)

        try:
            return libcnml.CNMLParser(zonefile)
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

    def findAttributeTypes(self):
        print _('Select type of attribute:')
        attr = int(raw_input("Enter: 1 for devices, 2 for ifaces, 3 for links or 4 for Services: "))
        if  attr == 1 :
            objects = self.zone.getDevices()
            print "Find all device types"
        elif attr == 2 :
            objects = self.zone.getInterfaces()
            print "Find all Interface types"
        elif attr == 3 :
            objects = self.zone.getLinks()
            print "Find all link types"
        elif attr == 4 :
            objects = self.zone.getServices()
            print "Find all service types"
        else :
            print _('Wrong Input')
            return

        types = {}
        for obj in objects:
            if obj.type not in types:
                types.update({obj.type:1})
            else:
                counter = types[obj.type] + 1
                types.update({obj.type:counter})
        print _('Different Types: '), len(types)
        sortedTypes = sorted(types.iteritems(), key=operator.itemgetter(1))
        print _('Types: '), sortedTypes
        print _('Total Number: '), len(objects)


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
            print _('Link id'), link.id
            print _('Link type'), link.type
            entry = { "from": link.nodeA.id, "to": link.nodeB.id}
            print _('The entry is: '), entry
            fpTopo.write("%s,\n" % json.dumps(entry))
            
        print>> fpTopo, "];"
        fpTopo.close()


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