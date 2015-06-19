#!/usr/bin/env python
#
#test.py

#TODO make dictionary list of tuples

import os
import sys
#os.chdir(os.path.dirname(os.path.abspath(__file__)))
#sys.path.append('lib')
#sys.path.append('lib/libcnml')
#sys.path.append('lib/pyGuifiAPI')

#import libcnml
from lib.libcnml import logger
from lib import libcnml
import logging

# Change format of logger
logger.setLevel(logging.CRITICAL)

from lib.pyGuifiAPI import *
from lib.pyGuifiAPI.error import GuifiApiError

#from configmanager import GuifinetStudioConfig

from utils import *

from urllib2 import URLError

import gettext
_ = gettext.gettext

import json
import operator
import copy


from cnmlUtils import *


# Where to put that?
cnmlDirectory = "cnml"
if not os.path.exists(cnmlDirectory):
    os.makedirs(cnmlDirectory)


# Helper function
def flatten(lis):
    """Given a list, possibly nested to any level, return it flattened."""
    new_lis = []
    for item in lis:
        if type(item) == type([]):
            if item == [] : pass
            new_lis.extend(flatten(item))
        else:
            new_lis.append(item)
    return new_lis

class CNMLWrapper(object):
    def __init__(self, rootZoneId=None):
        # GuifiAPI
        self.conn = authenticate()
        if rootZoneId:
            self.rootZoneId = int(rootZoneId)
        else:
            self.rootZoneId = int(raw_input("Select a zone: "))
        print _('Parsing:'), rootZoneId
        #self.world = getCNMLZone(3671)
        self.cnml = parseCNMLZone(self.rootZoneId,self.conn)
        self.zone = self.cnml.zones[self.rootZoneId]
        self.guifizone = GuifiZone(self.zone)

        self.zones = {}
        self.nodes = {}
        self.devices = {}
        self.services = {}
        self.radios = {}
        self.ifaces = {}
        self.links = {}
        self.totalnodes = {}
        self.totaldevices = {}
        self.totalservices = {}
        self.totalradios = {}
        self.totalifaces = {}
        self.totallinks = {}
        temp = flatten((self.guifizone.allsubzones).values() + [self.guifizone])
        for zone in temp:
            self.zones.update({zone.zone.id:zone})
            self.nodes.update(zone.nodes)
            self.devices.update(zone.devices)
            self.services.update(zone.services)
            self.radios.update(zone.radios)
            self.ifaces.update(zone.ifaces)
            self.links.update(zone.links)
            self.totalnodes.update(zone.totalnodes)
            self.totaldevices.update(zone.totaldevices)
            self.totalservices.update(zone.totalservices)
            self.totalradios.update(zone.totalradios)
            self.totalifaces.update(zone.totalifaces)
            self.totallinks.update(zone.totallinks)

        logger.info('Total zones: %s',len(self.zones))
        logger.info('Total nodes:  %s',len(self.totalnodes))
        logger.info('Total links:  %s',len(self.totallinks))
        logger.info('Working nodes:  %s',len(self.nodes))
        logger.info('Working links:  %s',len(self.links))
        if self.totallinks and self.totalnodes:
            logger.info('Working nodes per total nodes: %s ',float(len(self.nodes))/float(len(self.totalnodes)))
            logger.info('Total links per total nodes: %s ',float(len(self.totallinks))/float(len(self.totalnodes)))
            if self.nodes:
                logger.info('Working links per working nodes: %s ',float(len(self.links))/float(len(self.nodes)))
            logger.info('Working links per total links : %s ',float(len(self.links))/float(len(self.totallinks)))
            nonworklinks= [i for i in self.totallinks.values() if i.status != libcnml.Status.WORKING]
            logger.info('Non Working (status) links: %s (%s percent of total links)',len(nonworklinks),float(len(nonworklinks))/float(len(self.totallinks)) )
            unparsedlinks= [i for i in self.totallinks.values() if (not i.nodeB) and i.status == libcnml.Status.WORKING]
            logger.info('Unparsed Working links: %s (%s percent of total links)',len(unparsedlinks),float(len(unparsedlinks))/float(len(self.totallinks)) )
            selflinks= [i for i in self.totallinks.values() if i.nodeA == i.nodeB and i.status==libcnml.Status.WORKING]
            logger.info('Self links: %s (%s percent of total links)',len(selflinks),float(len(selflinks))/float(len(self.totallinks)) )
            cablelinks= [i for i in self.totallinks.values() if i.type == "cable" and i.status==libcnml.Status.WORKING]
            logger.info('Cable links: %s (%s percent of total links)',len(cablelinks),float(len(cablelinks))/float(len(self.totallinks)) )
        #TODO check if there can be a working link inside non-working node or devices(should be prohibited in
        #    links but not in totallinks)

        #Todo Fix broken links? The ones not recognized cause node in other zone
    def findAttributeTypes(self):
        """
        List different types of components in the loaded CNML
        """
        print _('Select type of attribute:')
        attr = int(raw_input("Enter: 1 for devices, 2 for ifaces, 3 for links or 4 for Services: "))
        if  attr == 1 :
            objects = self.devices.values()
            print "Find all device types"
        elif attr == 2 :
            objects = self.ifaces.values()
            print "Find all Interface types"
        elif attr == 3 :
            objects = self.links.values()
            print "Find all link types"
        elif attr == 4 :
            objects = self.services.values()
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



class GuifiZone(object):
    def __init__(self, zone):
        self.zone = zone
        self.workingZone = self.getCNMLZoneWorking(self.zone)
        self.nodes = {}
        self.devices = {}
        self.services = {}
        self.radios = {}
        self.ifaces = {}
        self.links = {}
        self.totalnodes = {}
        self.totaldevices = {}
        self.totalservices = {}
        self.totalradios = {}
        self.totalifaces = {}
        self.totallinks = {}
        self.unparsedlinks = []
        # Set all the empty dictionaries
        self.setZoneElements()
        logger.info('Total %s (%s) nodes:  %s',self.zone.id,self.zone.title,len(self.totalnodes))
        logger.info('Total %s (%s) links:  %s',self.zone.id,self.zone.title,len(self.totallinks))
        logger.info('Working %s (%s) nodes:  %s',self.zone.id,self.zone.title,len(self.nodes))
        logger.info('Working %s (%s) links:  %s',self.zone.id,self.zone.title,len(self.links))
        if self.totallinks and self.totalnodes:
            logger.info('Working nodes per total nodes: %s ',float(len(self.nodes))/float(len(self.totalnodes)))
            logger.info('Total links per total node: %s ',float(len(self.totallinks))/float(len(self.totalnodes)))
            if self.nodes:
                logger.info('Working links per working nodes: %s ',float(len(self.links))/float(len(self.nodes)))
            logger.info('Working links per total links : %s ',float(len(self.links))/float(len(self.totallinks)))
            nonworklinks= [i for i in self.totallinks.values() if i.status != libcnml.Status.WORKING]
            logger.info('Non Working (status) links: %s (%s percent of total links)',len(nonworklinks),float(len(nonworklinks))/float(len(self.totallinks)) )
            self.unparsedlinks= [i for i in self.totallinks.values() if (not i.nodeB) and i.status == libcnml.Status.WORKING]
            logger.info('Unparsed Working links: %s (%s percent of total links)',len(self.unparsedlinks),float(len(self.unparsedlinks))/float(len(self.totallinks)) )
            selflinks= [i for i in self.totallinks.values() if i.nodeA == i.nodeB and i.status==libcnml.Status.WORKING]
            logger.info('Self links: %s (%s percent of total links)',len(selflinks),float(len(selflinks))/float(len(self.totallinks)) )
            cablelinks= [i for i in self.totallinks.values() if i.type == "cable" and i.status==libcnml.Status.WORKING]
            logger.info('Cable links: %s (%s percent of total links)',len(cablelinks),float(len(cablelinks))/float(len(self.totallinks)))

        #self.subzones = self.zone.subzones
        self.subzones = {}
        self.setSubZones()
        self.allsubzones = self.getAllSubZones()

        logger.info('%s subzones of %s (%s): %s',len(self.allsubzones),self.zone.id,self.zone.title,self.allsubzones)
        #self.allworkingsubzones = map(self.getCNMLZoneWorking,self.allsubzones)
        #logger.info('=== Subzones Info ===')
        #for zone in self.allworkingsubzones:
        #    logger.info('Total %s (%s) nodes:  %s',self.zone.id,self.zone.title,len(self.totalnodes))
        #    logger.info('Total %s (%s) links:  %s',self.zone.id,self.zone.title,len(self.totallinks))
        #    logger.info('Working %s (%s) nodes:  %s',self.zone.id,self.zone.title,len(self.nodes))
        #    logger.info('Working %s (%s) links:  %s',self.zone.id,self.zone.title,len(self.links))

    def getAllSubZones(self):
        temp = flatten(self.getAllSubZonesHelper(self))
        return {x.zone.id:x for x in temp if x != []}

    @staticmethod
    def getAllSubZonesHelper(guifizone):
        subzones = guifizone.subzones.values()
        if subzones == []:
            return []
        else:
            #print subzones
            #return subzones.update({x.getAllSubZones() for x in subzones.values()})
            return subzones+[x.getAllSubZonesHelper(x) for x in subzones]

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
        zone = cnmlObjectCopy(zoneIn)
        # Discard non-working nodes
        nodes = {node.id:cnmlObjectCopy(node) for node in zone.getNodes() if node.status==libcnml.Status.WORKING}
        zone.nodes = nodes

        # From the nodes left discard non-working Devices and Services
        for node in zone.getNodes():
            links=0
            node.devices = {device.id:cnmlObjectCopy(device) for device in node.getDevices() if device.status==libcnml.Status.WORKING}
            node.services = {service.id:cnmlObjectCopy(service) for service in node.getServices() if service.status==libcnml.Status.WORKING}
            # From the nodes and devices left discard non-working Links
            for device in node.getDevices():
                device.interfaces = {iface.id:cnmlObjectCopy(iface) for iface in device.getInterfaces()}
                device.radios = {(device.id,radio.id):cnmlObjectCopy(radio) for radio in device.getRadios()}
                for interface in device.getInterfaces():
                    interface.links = {link.id:cnmlObjectCopy(link) for link in interface.getLinks() if link.status==libcnml.Status.WORKING}
                    # Remove links that reach outside the zone
                    interface.links = {link.id:link for link in  interface.getLinks()  if isinstance(link.nodeB, libcnml.libcnml.CNMLNode)}
                    # Remove self-links
                    interface.links = {link.id:link for link in  interface.getLinks()  if link.nodeB.id != link.nodeA.id}
                    links = links + len(interface.links)
                for radio in device.getRadios():
                    radio.interfaces = {iface.id:cnmlObjectCopy(iface) for iface in radio.getInterfaces()}
                    for interface in radio.getInterfaces():
                        interface.links = {link.id:cnmlObjectCopy(link) for link in interface.getLinks() if link.status==libcnml.Status.WORKING}
                        # Remove links that reach outside the zone
                        interface.links = {link.id:link for link in  interface.getLinks()  if isinstance(link.nodeB, libcnml.libcnml.CNMLNode)}
                        # Remove self-links
                        #interface.links = {link.id:link for link in  interface.getLinks()  if link.nodeB.id != node.id}
                        interface.links = {link.id:link for link in  interface.getLinks()  if link.nodeB.id != link.nodeA.id}
                        links = links + len(interface.links)
            node.totalLinks =links
        # Fix counters
        return zone

    def setZoneElements(self):
        """
        Set local dictionaries containing all total elements and all working elements
        """
        zone = self.getZoneElements(self.zone)
        wzone = self.getZoneElements(self.workingZone)
        self.nodes = wzone['nodes']
        self.devices = wzone['devices']
        self.services = wzone['services']
        self.radios = wzone['radios']
        self.ifaces = wzone['ifaces']
        self.links = wzone['links']
        self.totalnodes = zone['nodes']
        self.totaldevices = zone['devices']
        self.totalservices = zone['services']
        self.totalradios = zone['radios']
        self.totalifaces = zone['ifaces']
        self.totallinks = zone['links']




    def getZoneElements(self, zone):
        """
        Returns a dictionary of lists that contain the 'devices' the 'services' the 'radios' the 'ifaces' and the 'links'
        contained in the zone
        """
        print _('Zone Id: '), zone.id
        nodes = {}
        devices = {}
        services = {}
        radios = {}
        ifaces = {}
        links = {}
        for node in zone.getNodes():
            elements  = self.getNodeElements(node)
            #print "\tNode: %d Devices: %d Services: %d Radios: %d Ifaces: %d Links: %d  " % (node.id, \
            #    len(elements['devices']), len(elements['services']), len(elements['radios']), len(elements['ifaces']),\
            #    len(elements['links']))
            nodes.update({node.id:node})
            devices.update(elements['devices'])
            services.update(elements['services'])
            radios.update(elements['radios'])
            ifaces.update(elements['ifaces'])
            links.update(elements['links'])
        #return {'devices':devices,'services':services,'radios':radios,'ifaces':ifaces, 'links':links}

        return {'nodes':nodes,'devices':devices,'services':services,'radios':radios,'ifaces':ifaces, 'links':links}
         # PRoblem??? One node is not parsed. The planned one...

    def getNodeElements(self,node):
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
                        links.update({link:iface.links[link]})
            for iface in device.getInterfaces():
                temp = [l for l in iface.links if l not in linkIds]
                linkIds = linkIds + temp
                for link in temp:
                        links.update({link:iface.links[link]})
        #print "\t(Node: %d | Status: %s) \tDevices: %d Services: %d Radios: %d Ifaces: %d Links: %d  " % (node.id, node.status, len(deviceIds),\
        #   len(serviceIds), len(radioIds), len(ifaceIds), len(linkIds))
        devStats = [ (i,devices[i].status) for i in deviceIds ]
        #print _('\t\tDevices: '), devStats
        servStats = [ (i,services[i].status) for i in serviceIds ]
        #print _('\t\tServices: '), servStats
        #print _('\t\tRadios: '), radioIds
        #print _('\t\tInterfaces: '), ifaceIds
        linkStats = [ (i,links[i].status) for i in linkIds ]
        #print _('\t\tLinks: '), linkStats
        #return {'devices':deviceIds,'services':serviceIds,'radios':radioIds,'ifaces':ifaceIds, 'links':linkIds}
        return {'devices':devices,'services':services,'radios':radios,'ifaces':ifaces, 'links':links}

    def setSubZones(self):
       for zone in self.zone.subzones.values():
            self.subzones.update({zone.id:GuifiZone(zone)})

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
            return self.nodes[node]
        return node

    # ToDo  Check why not working properly
    def createTopoJSON(self):
        nodesFile = os.path.join(os.getcwd(),"topo.js")
        fpTopo = open(nodesFile,"w")
        print>> fpTopo, "var nodes = ["
        for node in self.nodes.values():
            entry = {"id": node.id}
            fpTopo.write("%s,\n" % json.dumps(entry))
        print>> fpTopo, "];\n"
        print>> fpTopo, "var edges = ["
        for link in self.nodes.values():
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
        CNMLWrapper(sys.argv[1])
    else:
        CNMLWrapper()

#######################################################################
###                                 Testing                         ###
#######################################################################

#TODO test with other small zones to check
#TODO create dictionaries with all the working elements (like dics of CNMLParser)



def testWZone(root=8076):
        #reload(test);
        #root = 2436
        #root = 8076
        g = CNMLWrapper(root)
        #zones = (g.subzones).values()
        #zones.append(g)
        #for s in flatten(getAllSubZones(g)):
            #logger.info(' %s (%s)',s.rootZoneId,s.zone.title)
        #g.findAttributeTypes()
        return g
        for s in g.zones.values():
            logger.info(' %s (%s)',s.zone.id,s.zone.title)
        #u = (g.zones[38445]).unparsedlinks
        for z in g.zones.values():
            u = z.unparsedlinks
            if u:
                logger.info('Zone Unparsed Links %s %s',z.zone.id,z.zone.title)
                for link in u:
                    if link.nodeA not in g.nodes:
                        if link.nodeA not in g.totalnodes:
                            logger.warning('Link: %s NodeA: %s is not in parsed CNML', link.id, link.nodeA)
                            continue
                        else:
                            logger.warning('Link: %s  NodeA: %s is in not in WORKING mode !Weir since link status is %s', link.id, link.nodeA, link.status)
                            continue

                    if getParentCNMLNode(link).id not in g.nodes:
                        logger.warning('Link: %s  ParentNode: %s is not WORKING mode !Weird since link status is %s', link.id, link.nodeA, link.status)
                        continue

                    #logger.info('PArsing link with id: %s',link.id)
                    #try:
                    #    nodeA = g.nodes[link.nodeA]
                    #except:
                    #    try:
                    #        nodeA = g.totalnodes[link.nodeA]
                    #    except:
                    #        logger.warning('Link %s : NodeA: %s is in another zone', link.id, link.nodeA)
                    #        continue
                    #    logger.warning('Link %s : NodeA: %s is in not in WORKING mode', link.id, link.nodeA)
                    #    continue
                    logger.info('Unparsed link %s Status: %s Type: %s Link.nodeA: %s NodeAZone: %s Link parent Node: %s Parent Node Zone %s',
                                link.id, link.status, link.type, link.nodeA, (g.nodes[link.nodeA]).parentZone.id, getParentCNMLNode(link).id, (g.nodes[getParentCNMLNode(link).id]).parentZone.id)


        #g = GuifiNet(23918);
        #zone = g.cnml.getZones()[0];
        #for zone in g.cnml.getZones():
         #   g.getZoneElements(zone);
            #logger.debug("Working Elements:")
            #zo = g.getCNMLZoneWorking(zone);
            #g.getZoneElements(zo);
        #return (zone,zo)
        #return g
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
