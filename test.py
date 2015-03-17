#!/usr/bin/env python
#
#test.py

import os
import sys
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.append('lib')
sys.path.append('lib/libcnml')
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
    def __init__(self, rootZoneId=None):
        # GuifiAPI
        libcnml.logger.info("Starting process")
        libcnml.logger.debug("Starting debug")
        libcnml.logger.warning("Starting warn")
        self.gui = pyGuifiAPI.GuifiAPI('edimoger', '100105a')
        self.allZones = []
        print "Going to auth"
        try:
            self.gui.auth()
        except GuifiApiError, e:
            print e.reason
        print self.gui.is_authenticated()
        print self.gui.authToken
        if rootZoneId:
            self.rootZoneId = int(rootZoneId)
        else:
            self.rootZoneId = int(raw_input("Select a zone: "))
        print _('Parsing:'), rootZoneId
        #self.world = self.getZoneCNML(3671)
        self.cnml = self.parseZoneCNML(rootZoneId)
        self.rootZone = self.cnml.zones[rootZoneId]
        #for n in self.cnml.nodes:
        #    print self.cnml.nodes[n].status
        print _('Total nodes: '),  len(self.cnml.nodes)
        print _('Total devices: '),  len(self.cnml.devices)
        print _('Total links: '),  len(self.cnml.links)
        #TODO fix using only working nodes
       # self.cnml.nodes =  {i: self.cnml.nodes[i] for i in self.cnml.nodes if self.cnml.nodes[i].status == libcnml.Status.WORKING}
        #print "After keeping only working nodes"
        #print _('Total nodes: '),  len(self.cnml.nodes)
        #print _('Total devices: '),  len(self.cnml.getDevices())
        #print _('Total links: '),  len(self.cnml.getLinks())

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
            objects = self.cnml.getDevices()
            print "Find all device types"
        elif attr == 2 :
            objects = self.cnml.getInterfaces()
            print "Find all Interface types"
        elif attr == 3 :
            objects = self.cnml.getLinks()
            print "Find all link types"
        elif attr == 4 :
            objects = self.cnml.getServices()
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


    # ToDo  Check why not working properly
    def createTopoJSON(self):
        nodesFile = os.path.join(os.getcwd(),"topo.js")
        fpTopo = open(nodesFile,"w")
        print>> fpTopo, "var nodes = ["
        for node in self.cnml.getNodes():
            entry = {"id": node.id}
            fpTopo.write("%s,\n" % json.dumps(entry))
        print>> fpTopo, "];\n"
        print>> fpTopo, "var edges = ["
        for link in self.cnml.getLinks():
            #if link.link_status == "Working" and
            parent = self.getParentNode(link)
            print ('Link of node:'), parent.id
            print _('Link id'), link.id
            print _('Link type'), link.type
            if not link.nodeB:
                print _('Link to node outside the zone or not proper CNML data. Ignoring. Link id:'), link.id
                continue
            if parent.id == link.nodeB.id :
                print _('Link to self. Ignoring. Link id:'), link.id
                continue
            entry = { "from": link.nodeA.id, "to": link.nodeB.id}
            print _('The entry is: '), entry
            fpTopo.write("%s,\n" % json.dumps(entry))

        print>> fpTopo, "];"
        fpTopo.close()


    def getParentNode(self, comp):
        if type(comp) is libcnml.libcnml.CNMLLink :
            return self.getParentNode(comp.parentInterface)
        elif type(comp) is libcnml.libcnml.CNMLInterface :
            return self.getParentNode(comp.parentRadio)
        elif type(comp) is libcnml.libcnml.CNMLRadio :
            return self.getParentNode(comp.parentDevice)
        elif type(comp) is libcnml.libcnml.CNMLDevice :
            return self.getParentNode(comp.parentNode)
        elif type(comp) is libcnml.libcnml.CNMLNode :
            return comp
        else :
            return None

    def zoneWorking(self,zoneId):
        if not zoneId:
            zoneId = self.rootZoneId
        zone = self.cnml.zones[zoneId]

        # Discard non-working nodes
        zone.nodes = {{node.id}:node for node in zone.nodes if nodes}

        # From the nodes left discard non-working Devices


        # From the nodes and  devices left discard non-working Services


        # From the nodes and  devices left discard non-working Links


if __name__ == "__main__":
    if len(sys.argv) > 1:
        GuifiNet(sys.argv[1])
    else:
        GuifiNet()