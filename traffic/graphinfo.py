#!/usr/bin/env python
#
#graphinfo.py


# Pordria pretender que yo soy un servidor de graficas?

import os
import sys
#os.chdir(os.path.dirname(os.path.abspath(__file__)))
#sys.path.append('lib')
# For storing dicts in sqlite3
#sys.path.append('lib/sqlitedict')
#from ..lib.sqlitedict import SqliteDict
#from ..lib.sqlitedict import SqliteDict
#from ..lib.sqlitedict import sqlitedict
from ..lib.sqlitedict.sqlitedict import SqliteDict


from ..guifiwrapper.guifiwrapper import *
from ..guifiwrapper.cnmlUtils import *
from snpservicesClient import *

import urllib2
import csv
from netaddr import IPNetwork, IPAddress
import sys



root = 8346
g = CNMLWrapper(root)

ipBlacklist = []


dbName = "./"+"graphinfo"+"_"+str(root)+".sqlite"
devices = SqliteDict(filename=dbName, tablename='devices', flag='n',autocommit=False)
#for k,v in g.devices.iteritems():
#    devices[k] = {"node":v.parentNode.id}
#devices.commit()
#devices.close()


def getDeviceGraphService(device,node=None):

    #Get info from device
    if device.graphserverId:
        serviceId = device.graphserverId
    else:
        # Prepare to search in other locations
        if not node:
            node = getParentCNMLNode(device)
        zone = node.parentZone
        # Get info from node
        if node.graphserverId:
            logger.debug("In 1")
            serviceId = node.graphserverId
        # Get info from zone
        elif zone.graphserverId:
            logger.debug("In 2")
            serviceId = zone.graphserverId
        # search in parentzones
        else:
            while zone.parentzone:
                logger.debug("In 3")
                zone = g.zones[zone.parentzone]
                if zone.zone.graphserverId:
                    serviceId = zone.zone.graphserverId
                    break
            #Nothing found
                raise EnvironmentError("CNML Error: Graphserver of node not found")
            #return None
    try:
        service = g.services[serviceId]
    except KeyError as err:
        raise EnvironmentError("Graph service not working or not in the parsed CNML")
    return service


def getGraphServiceIP(graphService):
    device = service.parentDevice
    ip = None
    for iface in device.interfaces.values():
        if iface.ipv4 and checkGuifiSubnet(iface.ipv4) and \
        iface.ipv4 not in ipBlacklist:
            ip = iface.ipv4
            break
    if not ip:
        # Ip's are not always in the same device
        # So search also other devices of same node
        # IS that correct?
        node = device.parentNode
        for dev in node.devices.values():
            for iface in dev.interfaces.values():
                if iface.ipv4 and checkGuifiSubnet(iface.ipv4) and \
                iface.ipv4 not in ipBlacklist:
                    ip = iface.ipv4
                    break
            if ip:
                break
        if not ip:
            logger.error("Could not find ip of graphserver %s with parent device %s" % (service.id,device.id))
            raise EnvironmentError("Could not find ip of graphserver")
    return ip



def getGraphData(graphService,device):
    try:
        ip = getGraphServiceIP(graphService)
    except EnvironmentError as err:
        raise EnvironmentError(err.message)
    #service = "stats"
    #url = "http://"+str(ip)+"/snpservices/index.php?call="+service+"&devices="+str(device.id)
    #logger.info("SNPServices request to graph server: %s",url)
    #req = urllib2.Request(url)
    try:
        #response=urllib2.urlopen(req,timeout=3)
        #data = response.read()
        data = snpRequest(ip,command="stats",args={"devices":[device.id]},debug=False, timeout=3)
        return data
    except URLError as e:
        ipBlacklist.append(ip)
        logger.error(e.reason)
        return getGraphData(graphService,device)

def pingGraphServer(graphService):
    try:
        ip = getGraphServiceIP(graphService)
    except EnvironmentError as err:
        raise EnvironmentError(err.message)
    #service = "stats"
    #url = "http://"+str(ip)+"/snpservices/index.php?call="+service+"&devices="+str(device.id)
    #logger.info("SNPServices request to graph server: %s",url)
    #req = urllib2.Request(url)
    try:
        snpRequest(ip,command="help",debug=False, timeout=3)
    except URLError as e:
        ipBlacklist.append(ip)
        logger.error(e.reason)
        return getGraphData(graphService,device)

def checkGuifiSubnet(ip):
    return IPAddress(ip) in IPNetwork("10.0.0.0/8")



def graphServerNodes(serviceId):
    url = "http://snpservices.guifi.net/snpservices/graphs/cnml2mrtgcsv.php?cp&server="+str(service.id)
    logger.info("Request to guifi.net: Find nodes monitored by %s",str(service.id))
    req = urllib2.Request(url)
    try:
        response=urllib2.urlopen(req)
        data = csv.reader(response)
        nodes = []
        for line in data:
            nodes.append(int(line[0]))
    except URLError as e:
        print e.reason
    return nodes


#device=g.devices[2737]
#service = getDeviceGraphService(device)
#nodes = graphServerNodes(service)
#print nodes
#service = getDeviceGraphService(device)
#print service
#data = getGraphData(service,device)
#print data

if __name__ == "__main__":
    for link in g.links.values():
        logger.info("LINK: %s" % link.id)
        for device in [link.deviceA,link.deviceB]:
            logger.info("\tDEVICE: %s" % (device.id))
            try:
                service = getDeviceGraphService(device)
            except EnvironmentError as error:
                logger.error(error)
                sys.exit(1)
            try:
                stats = getGraphData(service,device)
            except EnvironmentError as error:
                logger.error(error)
                sys.exit(1)
            logger.info("\tSTATS: %s " % (stats))





# Get list of nodes
# associate links with couples of devices
# find how to get link info from devices
# for each device:
#   ask info from his graph server
#parse and store the info (find a proper way to do that)
# test if that works in
