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
from libcnml import logger as logger
import logging

# Change format of logger
logger.setLevel(logging.DEBUG)

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

from cnmlUtils import *

class GuifiNet(object):
    def __init__(self, rootZoneId=None):
        # GuifiAPI
        self.conn = authenticate()
        if rootZoneId:
            self.rootZoneId = int(rootZoneId)
        else:
            self.rootZoneId = int(raw_input("Select a zone: "))
        print _('Parsing:'), rootZoneId
        #self.world = getCNMLZone(3671)
        self.cnml = parseCNMLZone(rootZoneId,self.conn)
        self.zone = self.cnml.zones[rootZoneId]
        self.workingZone = self.getCNMLZoneWorking(self.zone)
        #for n in self.cnml.nodes:
        #    print self.cnml.nodes[n].status
        temp = self.getZoneElements(self.workingZone)
        #self.nodes = {temp['nodes']}
        #TODO the rest
        self.devices = {}
        self.services = {}
        self.radios = {}
        self.ifaces = {}
        self.links = {}
        logger.info('Zone nodes:  %s',len(self.cnml.nodes))
        logger.info('Zone devices:  %s', len(self.cnml.devices))
        logger.info('Zone links:  %s',len(self.cnml.links))
        #TODO fix using only working nodes
       # self.cnml.nodes =  {i: self.cnml.nodes[i] for i in self.cnml.nodes if self.cnml.nodes[i].status == libcnml.Status.WORKING}
        #print "After keeping only working nodes"
        #print _('Total nodes: '),  len(self.cnml.nodes)
        #print _('Total devices: '),  len(self.cnml.getDevices())
        #print _('Total links: '),  len(self.cnml.getLinks())

    def findAttributeTypes(self):
        """
        List different types of components in the loaded CNML
        """
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

    def getCNMLZoneWorking(self,zoneIn):
        """
        From input a CNMLZone object return a new CNMLZone object that  contains only working elements
        """
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
        """
        Returns a dictionary of lists that contain the 'devices' the 'services' the 'radios' the 'ifaces' and the 'links'
        contained in the zone
        """
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
        """
        Get all the elements of a node
        """
        node = self.getNode(node)
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
        print "\t(Node: %d | Status: %s) \tDevices: %d Services: %d Radios: %d Ifaces: %d Links: %d  " % (node.id, node.status, len(deviceIds),\
           len(serviceIds), len(radioIds), len(ifaceIds), len(linkIds))
        devStats = [ (i,(self.cnml.devices[i]).status) for i in deviceIds ]
        print _('\t\tDevices: '), devStats
        servStats = [ (i,(self.cnml.services[i]).status) for i in serviceIds ]
        print _('\t\tServices: '), servStats
        print _('\t\tRadios: '), radioIds
        print _('\t\tInterfaces: '), ifaceIds
        linkStats = [ (i,(self.cnml.links[i]).status) for i in linkIds ]
        print _('\t\tLinks: '), linkStats
        return {'devices':deviceIds,'services':serviceIds,'radios':radioIds,'ifaces':ifaceIds, 'links':linkIds}

    def getZoneElements1(self, zone):
        """
        Returns a dictionary of lists that contain the 'devices' the 'services' the 'radios' the 'ifaces' and the 'links'
        contained in the zone
        """
        #if not zoneId:
        #    zoneId = self.rootZoneId
        #root = self.cnml.zones[zoneId]
        #zones = [root] +
        print _('Zone Id: '), zone.id
        nodes = {}
        devices = {}
        services = {}
        radios = {}
        ifaces = {}
        links = {}
        for node in zone.getNodes():
            elements  = self.getNodeElements1(node)
            #print "\tNode: %d Devices: %d Services: %d Radios: %d Ifaces: %d Links: %d  " % (node.id, \
            #    len(elements['devices']), len(elements['services']), len(elements['radios']), len(elements['ifaces']),\
            #    len(elements['links']))
            nodes.update({node.id:node})
            devices.update(elements['devices'])
            services.update(elements['services'])
            radios.update(elements['radios'])
            ifaces.update(elements['ifaces'])
            links.update(elements['links'])

        return {'devices':devices,'services':services,'radios':radios,'ifaces':ifaces, 'links':links}
         # PRoblem??? One node is not parsed. The planned one...

    def getNodeElements1(self,node):
        """
        Get all the elements of a node
        """
        node = self.getNode(node)
        devices = node.devices
        deviceIds = [d for d in node.devices]
        services = node.services
        serviceIds = [s for s in node.services]
        radios = {}
        radioIds = []
        ifaces = {}
        ifaceIds = []
        links = {}
        linkIds = []
        for device in node.getDevices():
            radios.update(device.radios)
            radioIds = radioIds + [r for r in device.radios]
            ifaces.update(device.interfaces)
            ifaceIds = ifaceIds + [i for i in device.interfaces]
            for radio in device.getRadios():
                ifaces.update(radio.interfaces)
                ifaceIds = ifaceIds + [i for i in radio.interfaces]
                for iface in radio.getInterfaces():
                    # Add new links (ignoring duplicates)
                    temp = [l for l in iface.links if l not in linkIds]
                    linkIds = linkIds + temp
                    for link in temp:
                        links.update(iface.links[link])
            for iface in device.getInterfaces():
                temp = [l for l in iface.links if l not in linkIds]
                linkIds = linkIds + temp
                for link in temp:
                        links.update(iface.links[link])
        print "\t(Node: %d | Status: %s) \tDevices: %d Services: %d Radios: %d Ifaces: %d Links: %d  " % (node.id, node.status, len(deviceIds),\
           len(serviceIds), len(radioIds), len(ifaceIds), len(linkIds))
        devStats = [ (i,(self.cnml.devices[i]).status) for i in deviceIds ]
        print _('\t\tDevices: '), devStats
        servStats = [ (i,(self.cnml.services[i]).status) for i in serviceIds ]
        print _('\t\tServices: '), servStats
        print _('\t\tRadios: '), radioIds
        print _('\t\tInterfaces: '), ifaceIds
        linkStats = [ (i,(self.cnml.links[i]).status) for i in linkIds ]
        print _('\t\tLinks: '), linkStats
        #return {'devices':deviceIds,'services':serviceIds,'radios':radioIds,'ifaces':ifaceIds, 'links':linkIds}
        return {'devices':devices,'services':services,'radios':radios,'ifaces':ifaces, 'links':links}


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



    def getNode(self, node):
        """
        Return CNMLNode object
        """
        if node is int :
            return self.cnml.nodes[node]
        return node

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
            parent = getParentCNMLNode(link) # ERROR not working cause of logical error descired down
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

if __name__ == "__main__":
    if len(sys.argv) > 1:
        GuifiNet(sys.argv[1])
    else:
        GuifiNet()

#######################################################################
###                                 Testing                         ###
#######################################################################

#TODO test with other small zones to check
#TODO create dictionaries with all the working elements (like dics of CNMLParser)

def testWZone():
        #reload(test);
        g = GuifiNet(50962);
        #g = GuifiNet(23918);
        #zone = g.cnml.getZones()[0];
        for zone in g.cnml.getZones():
            g.getZoneElements(zone);
            logger.debug("Working Elements:")
            zo = g.getCNMLZoneWorking(zone);
            g.getZoneElements(zo);
        #return (zone,zo)
        return g
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
#reload(test); g = test.GuifiNet(23918); zone = g.cnml.getZones()[0]; zo = g.getCNMLZoneWorking(zone); g.getZoneElements(zone); g.getZoneElements(zo); linksZone = g.getZoneLinks(zone); linksZo = g.getZoneLinks(zo);
