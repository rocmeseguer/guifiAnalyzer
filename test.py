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

    def getZoneCNML(self,zone=None):
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

    def workingElements(self):
        #TODO fix counters from upper elements (for example node counter in zone) OR MAYBE not necessary

        # Can parse zones as indepent since their data are not crossing one another
        # copying list objects with [:]
        # copying dictionary object with .copy()
        #workingZones = self.cnml.getZones()[:]
        # Return a list with zones where all the objects
        # are new
        # import copy
        # copy.deepcopy(zone)
        for zone in self.cnml.getZones():
            # Discard non-working nodes
            zone.nodes = {node.id:node for node in zone.getNodes() if node.status==libcnml.Status.WORKING}

            # From the nodes left discard non-working Devices and Services
            for node in zone.getNodes():
                node.devices = {device.id:device for device in node.getDevices() if device.status==libcnml.Status.WORKING}
                node.services = {service.id:service for service in node.getServices() if service.status==libcnml.Status.WORKING}
                
                # From the nodes and devices left discard non-working Links
                for device in node.getDevices():
                    for interface in device.getInterfaces():
                        interface.links = {link.id:link for link in interface.getLinks() if link.status==libcnml.Status.WORKING}
                    for radio in device.getRadios():
                        for interface in device.getInterfaces():
                            interface.links = {link.id:link for link in interface.getLinks() if link.status==libcnml.Status.WORKING}
                        
        # Fix counters
        
    def getZoneElements(self):
        #if not zoneId:
        #    zoneId = self.rootZoneId
        #root = self.cnml.zones[zoneId]
        #zones = [root] + 
        for zone in self.cnml.getZones():
            print _('Zone Id: '), zone.id
            for node in zone.getNodes():
                self.getNodeElements(node)
                # PRoblem??? One node is not parsed. The planned one...
     
    #def getNodeLinks           

    def getNodeElements(self,node):
        if node is int :
            node = self.cnml.nodes[node]
        deviceIds = [d for d in node.devices]
        serviceIds = [s for s in node.services]
        radioIds = []
        ifaceIds = []
        linkIds = []
        for device in node.getDevices():
            radioIds = radioIds + [r for r in device.radios]
            ifaceIds = ifaceIds + [i for i in device.interfaces]
            for radio in device.getRadios():
                ifaceIds = ifaceIds + [i for i in radio.interfaces]
                for iface in radio.getInterfaces():
                    # Add new links (ignoring duplicates)
                    linkIds = linkIds + [l for l in iface.links if l not in linkIds]
            for iface in device.getInterfaces():

                linkIds = linkIds + [l for l in iface.links if l not in linkIds]
        print "\tNode: %d Devices: %d Services: %d Radios: %d Ifaces: %d Links: %d  " % (node.id, len(deviceIds), len(serviceIds), len(radioIds), len(ifaceIds), len(linkIds))
        return {'devices':deviceIds,'services':serviceIds,'radios':radioIds,'ifaces':ifaceIds, 'links':linkIds}
        #print _('\t\tDevices: '), deviceIds
        #print _('\t\t\tServices: '), serviceIds
        #print _('\t\t\tRadios: '), radioIds
        #print _('\t\t\tInterfaces: '), ifaceIds
        #print _('\t\t\t\tLinks: '), linkIds


if __name__ == "__main__":
    if len(sys.argv) > 1:
        GuifiNet(sys.argv[1])
    else:
        GuifiNet()