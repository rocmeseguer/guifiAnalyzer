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
import copy

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
            parent = self.getParentNode(link) # ERROR not working cause of logical error descired down
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

    # Careful for Links: If there is a node B it will return this as Id
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

    def getZoneWorking(self,zoneIn):
        #TODO fix counters from upper elements (for example node counter in zone) OR MAYBE not necessary

        # Can parse zones as indepent since their data are not crossing one another

        # Since we are only deleting elements from the dictionary
        # we just have to deepcopy the zone object
        # If we were modifying the attributes of other objects linked
        # to zone (like nodes) we should deepcopy them also
        zone = copy.deepcopy(zoneIn)
        # Discard non-working nodes
        nodes = {node.id:copy.deepcopy(node) for node in zone.getNodes() if node.status==libcnml.Status.WORKING}
        zone.nodes = nodes
        # From the nodes left discard non-working Devices and Services
        for node in zone.getNodes():
            node.devices = {device.id:copy.deepcopy(device) for device in node.getDevices() if device.status==libcnml.Status.WORKING}
            node.services = {service.id:copy.deepcopy(service) for service in node.getServices() if service.status==libcnml.Status.WORKING}
            # From the nodes and devices left discard non-working Links
            for device in node.getDevices():
                device.interfaces = {iface.id:copy.deepcopy(iface) for iface in device.getInterfaces()}
                device.radios = {(device.id,radio.id):copy.deepcopy(radio) for radio in device.getRadios()}
                for interface in device.getInterfaces():
                    interface.links = {link.id:copy.deepcopy(link) for link in interface.getLinks() if link.status==libcnml.Status.WORKING}
                    # Remove links that reach outside the zone
                    interface.links = {link.id:link for link in  interface.getLinks()  if isinstance(link.nodeB, libcnml.libcnml.CNMLNode)}
                    # Remove self-links
                    interface.links = {link.id:link for link in  interface.getLinks()  if link.nodeB.id != link.nodeA.id}
                for radio in device.getRadios():
                    radio.interfaces = {iface.id:copy.deepcopy(iface) for iface in radio.getInterfaces()}
                    for interface in radio.getInterfaces():
                        interface.links = {link.id:copy.deepcopy(link) for link in interface.getLinks() if link.status==libcnml.Status.WORKING}
                        # Remove links that reach outside the zone
                        interface.links = {link.id:link for link in  interface.getLinks()  if isinstance(link.nodeB, libcnml.libcnml.CNMLNode)}
                        # Remove self-links
                        #interface.links = {link.id:link for link in  interface.getLinks()  if link.nodeB.id != node.id}
                        interface.links = {link.id:link for link in  interface.getLinks()  if link.nodeB.id != link.nodeA.id}
        # Fix counters
        return zone


    def getZoneElements(self, zone):
        #if not zoneId:
        #    zoneId = self.rootZoneId
        #root = self.cnml.zones[zoneId]
        #zones = [root] +
        print _('Zone Id: '), zone.id
        result = {}
        for node in zone.getNodes():
            elements  = self.getNodeElements(node)
            #print "\tNode: %d Devices: %d Services: %d Radios: %d Ifaces: %d Links: %d  " % (node.id, \
            #    len(elements['devices']), len(elements['services']), len(elements['radios']), len(elements['ifaces']),\
            #    len(elements['links']))
            result[node.id] = {'devices':elements['devices'],'services':elements['services'],\
                'radios':elements['radios'],'ifaces':elements['ifaces'], 'links':elements['links']}

        return result
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
        print "\tNode: %d Devices: %d Services: %d Radios: %d Ifaces: %d Links: %d  " % (node.id, len(deviceIds),\
           len(serviceIds), len(radioIds), len(ifaceIds), len(linkIds))
        print _('\t\tDevices: '), deviceIds
        print _('\t\tServices: '), serviceIds
        print _('\t\tRadios: '), radioIds
        print _('\t\tInterfaces: '), ifaceIds
        print _('\t\tLinks: '), linkIds
        return {'devices':deviceIds,'services':serviceIds,'radios':radioIds,'ifaces':ifaceIds, 'links':linkIds}

    #def prettyPrintNode(self,node):

    def nodeToDict(self,node):
        result = {}
        for device in node.getDevices():
            result[('device',device)] = {}
            for interface in device.getInterfaces():
                result[('device',device)][('interface',interface)]  = {}
                for link in interface.getLinks():
                    result[('device',device)][('interface',interface)]['link',link] = {}
            for radio in device.getRadios():
                result[('device',device)]['radio',radio] = {}
                for interface in radio.getInterfaces():
                    result[('device',device)]['radio',radio][('interface',interface)] = {}
                    for link in interface.getLinks():
                        result[('device',device)]['radio',radio][('interface',interface)]['link',link] = {}
        return result

    def getZoneLinks(self,zone):
        links = []
        for node in zone.getNodes():
            for device in node.getDevices():
                for radio in device.getRadios():
                    for iface in radio.getInterfaces():
                        newLinks = [l for l in iface.getLinks() if l not in links]
                        links.extend(newLinks)
                for iface in device.getInterfaces():
                    newLinks = [l for l in iface.getLinks() if l not in links]
                    links.extend(newLinks)
        return links



if __name__ == "__main__":
    if len(sys.argv) > 1:
        GuifiNet(sys.argv[1])
    else:
        GuifiNet()

### Testing:


def test1():
        #reload(test);
        g = GuifiNet(50962);
        #zone = g.cnml.getZones()[0];
        for zone in g.cnml.getZones():
            g.getZoneElements(zone);
            print "Working"
            zo = g.getZoneWorking(zone);
            g.getZoneElements(zo);
        return (zone,zo)
       # linksZone = g.getZoneLinks(zone);
        #linksZo = g.getZoneLinks(zo);
        #linksZoneNW = [l.id for l in linksZone if l.status != libcnml.Status.WORKING]
        #linksZoNW = [l.id for l in linksZo if l.status != libcnml.Status.WORKING]
        #linksZoneW = [l.id for l in linksZone if l.status == libcnml.Status.WORKING]
        #linksZoW = [l.id for l in linksZo if l.status == libcnml.Status.WORKING]
        #print linksZoneNW
        #print linksZoNW
        #print len(set(linksZoW))
        #print len(set(linksZoNW))
        #print len(set(linksZoneW))
        #print len(set(linksZoneNW))



## Select Working Objects:
#reload(test); g = test.GuifiNet(23918); zone = g.cnml.getZones()[0]; zo = g.getZoneWorking(zone); g.getZoneElements(zone); g.getZoneElements(zo); linksZone = g.getZoneLinks(zone); linksZo = g.getZoneLinks(zo);