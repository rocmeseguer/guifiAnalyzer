#!/usr/bin/env python
#
# graphinfo.py


# Pordria pretender que yo soy un servidor de graficas?

import os
import sys

# For storing dicts in sqlite3
from ..lib.sqlitedict.sqlitedict import SqliteDict

from ..guifiwrapper.guifiwrapper import *
from ..guifiwrapper.cnmlUtils import *
from snpservicesClient import *

import urllib2
import csv
from netaddr import IPNetwork, IPAddress
import sys

from enum import Enum

root = 8346
g = CNMLWrapper(root)

misDevices = []
wtfDevices = []


#  Example usage of sqlitedict:
#
#dbName = "./" + "graphinfo" + "_" + str(root) + ".sqlite"
#tableName = 'links'
#devices = SqliteDict(
#    filename=dbName,
#    tablename='devices',
#    flag='n',
#    autocommit=False)
# for k,v in g.devices.iteritems():
#    devices[k] = {"node":v.parentNode.id}
# devices.commit()
# devices.close()


def getDeviceGraphService(device, node=None,blacklist=[]):

    # Get info from device
    if device.graphserverId:
        serviceId = device.graphserverId
    else:
        # Prepare to search in other locations
        if not node:
            node = getParentCNMLNode(device)
        zone = node.parentZone
        # Get info from node
        if node.graphserverId:
            #logger.debug("In 1")
            serviceId = node.graphserverId
        # Get info from zone
        elif zone.graphserverId:
            #logger.debug("In 2")
            serviceId = zone.graphserverId
        # search in parentzones
        else:
            while zone.parentzone:
                #logger.debug("In 3")
                zone = g.zones[zone.parentzone]
                if zone.zone.graphserverId:
                    serviceId = zone.zone.graphserverId
                    break
            # Nothing found
                raise EnvironmentError(
                    "CNML Error: Graphserver of node not found")
            # return None
    try:
        service = g.services[serviceId]
    except KeyError as err:
        raise EnvironmentError(
            "Graph service not working or not in the parsed CNML")
    #logger.info("Graphserver of device %s is: %s" % (device.id, serviceId))
    return service


def getGraphServiceIP(graphService, ipBlacklist=[]):
    device = graphService.parentDevice
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
            #logger.error(
            #    "Could not find ip of graphserver %s with parent device %s" %
            #    (graphService.id, device.id))
            raise EnvironmentError("Could not find ip of graphserver")
    return ip


def getGraphData(graphService, device):
    try:
        ip = getGraphServiceIP(graphService)
    except EnvironmentError as err:
        raise EnvironmentError(err.message)
    #service = "stats"
    #url = "http://"+str(ip)+"/snpservices/index.php?call="+service+"&devices="+str(device.id)
    #logger.info("SNPServices request to graph server: %s",url)
    #req = urllib2.Request(url)
    try:
        # response=urllib2.urlopen(req,timeout=3)
        #data = response.read()
        data = snpRequest(
            ip,
            command="stats",
            args={
                "devices": [
                    device.id]},
            debug=False,
            timeout=3)
        return data
    except URLError as e:
        ipBlacklist.append(ip)
        #logger.error(e.reason)
        return getGraphData(graphService, device)


# Want a blaclist to return or not?
def checkGraphServer(graphService, device, ipBlacklist):
    try:
        ip = getGraphServiceIP(graphService,ipBlacklist)
    except EnvironmentError as err:
        # No more IPs
        raise EnvironmentError(err.message)
    try:
        data = snpRequest(
            ip,
            command="stats",
            args={
                "devices": [
                    device.id]},
            debug=False,
            timeout=3)
        data = data.rstrip()
        if data == str(device.id)+"|0,0,0.00,0,,,0":
            #Server does not handle the node
            #pass # Do something
            #raise EnvironmentError("GraphServer does not contain node stats")
            devices = graphServerDevices(graphService)
            if device.id in devices:
                logger.error("Misconfigured device %s" % (device.id))
                misDevices.append(device)
            else:
                logger.error("VAYA PUTA MIERDA device %s" % (device.id))
                wtfDevices.append(device)
            return None
        return ip
    except URLError as e:
        ipBlacklist.append(ip)
        logger.error(e.reason)
        return checkGraphServer(graphService, device, ipBlacklist)

def pingGraphServer(graphService):
    try:
        ip = getGraphServiceIP(graphService)
    except EnvironmentError as err:
        return False
    try:
        snpRequest(ip, command="help", debug=False, timeout=3)
        return ip
    except URLError as e:
        ipBlacklist.append(ip)
        logger.error(e.reason)
        return pingGraphServer(graphService)


def checkGuifiSubnet(ip):
    return IPAddress(ip) in IPNetwork("10.0.0.0/8")


def graphServerDevices(service):
    url = "http://snpservices.guifi.net/snpservices/graphs/cnml2mrtgcsv.php?cp&server=" + \
        str(service.id)
    #logger.info(
    #    "Request to guifi.net: Find nodes monitored by %s", str(
    #        service.id))
    req = urllib2.Request(url)
    try:
        response = urllib2.urlopen(req)
        data = csv.reader(response)
        devices = []
        for line in data:
            devices.append(int(line[0]))
    except URLError as e:
        pass
        #print e.reason
    return devices


# device=g.devices[2737]
#service = getDeviceGraphService(device)
#nodes = graphServerNodes(service)
# print nodes
#service = getDeviceGraphService(device)
# print service
#data = getGraphData(service,device)
# print data


def  storeDict2Table(dictionary,table):
    for k,v in dictionary.iteritems():
        table[k] = v
    table.commit()

if __name__ == "__main__":
    if True:
        enumNode = {0:'nodeA',1:'nodeB'}
        enumDevice = {0:'deviceA',1:'deviceB'}
        enumGraphServer = {0:'graphServerA',1:'graphServerB'}
        links = {}
        devices = {}
        graphServers = {}
        for link in g.links.values():
            #logger.info("LINK: %s" % link.id)
            links[link.id]= {'nodeA':link.nodeA.id,
                            'nodeB':link.nodeB.id}
            for index,device in enumerate([link.deviceA, link.deviceB]):
                if device.id not in devices:
                    #logger.info("\tDEVICE: %s" % (device.id))
                    devices[device.id] = {'link':link.id}
                    try:
                        service = getDeviceGraphService(device)
                        # Using enum to avoid if else
                        links[link.id][enumDevice[index]] = device.id
                        links[link.id][enumGraphServer[index]] = service.id
                        #if device == link.deviceA:
                        #    links[link.id]['deviceA'] = device.id
                        #    links[link.id]['graphServerA'] = service.id
                        #else:
                        #    links[link.id]['deviceB'] = device.id
                        #    links[link.id]['graphServerB'] = service.id
                        devices[device.id]['graphServer'] = service.id
                    except EnvironmentError as error:
                        #logger.error("\tCould not find graphserver of device %s" % (device.id))
                        # Using enum to avoid if else
                        links[link.id][enumDevice[index]] = device.id
                        links[link.id][enumGraphServer[index]] = service.id
                        #if device == link.deviceA:
                        #    links[link.id]['deviceA'] = device.id
                        #    links[link.id]['graphServerA'] = None
                        #else:
                        #    links[link.id]['deviceB'] = device.id
                        #    links[link.id]['graphServerB'] = None
                        devices[device.id]['graphServer'] = None
                        continue
                        #sys.exit(1)
                    if service.id not in graphServers:
                        try:
                            ipBlacklist = []
                            ip = checkGraphServer(service,device, ipBlacklist)
                            if ip:
                                graphServers[service.id] = ip
                            else:
                                # Anyway ip value here is None
                                # Just writting explicitly for clarity
                                graphServers[service.id] = None
                            #if not ip:
                                # The ip was found but no data for this device on this graphserver
                        except EnvironmentError as error:
                            #logger.error("\tCould not find working IP of graphserver %s of device %s\n Error: %s" % (service.id,device.id,error))
                            continue
                            #sys.exit(1)
                        #logger.info("\tThe ip %s of graphserver %s is correct for the device %s" % (ip,service.id,device.id))
        logger.info("# of Misconfigured Devices:%s" % (len(misDevices)))
        logger.info("# of Fucked Devices:%s" % (len(wtfDevices)))



    if False:
        # Normal use
        for link in g.links.values():
            logger.info("LINK: %s" % link.id)
            for device in [link.deviceA, link.deviceB]:
                logger.info("\tDEVICE: %s" % (device.id))
                try:
                    service = getDeviceGraphService(device)
                except EnvironmentError as error:
                    logger.error(error)
                    sys.exit(1)
                try:
                    stats = getGraphData(service, device)
                except EnvironmentError as error:
                    logger.error(error)
                    sys.exit(1)
                logger.info("\tSTATS: %s " % (stats))
                #ip = checkGraphServer(g.services[25337],)
    if False:
        links = {}
        devices = {}
        graphServers = {}
        for link in g.links.values():
                logger.info("LINK: %s" % link.id)
                links[link.id]= {'nodeA':link.nodeA.id,
                            'nodeB':link.nodeB.id}
                for device in [link.deviceA, link.deviceB]:
                    logger.info("\tDEVICE: %s" % (device.id))
                    devices[device.id] = {'link':link.id}
                    # Get GraphServer
                    try:
                        service = getDeviceGraphService(device)
                        if device == link.deviceA:
                            links[link.id]['deviceA'] = device.id
                            links[link.id]['graphServerA'] = service.id
                        else:
                            links[link.id]['deviceB'] = device.id
                            links[link.id]['graphServerB'] = service.id
                        devices[device.id]['graphServer'] = service.id
                    except EnvironmentError as error:
                        # corresponding GraphService  not found
                        logger.error(error)
                        if device == link.deviceA:
                            links[link.id]['deviceA'] = device.id
                            links[link.id]['graphServerA'] = None
                        else:
                            links[link.id]['deviceB'] = device.id
                            links[link.id]['graphServerB'] = None
                        devices[device.id]['graphServer'] = None
                        continue
                    # Check GraphServer is working and correct
                    try:
                        # We want to check the following stuff:
                        # 1)Working IP (maybe also log non-working ones)
                        # 2)that node is monitored by this server
                        # 3)maybe store info for graph servers already checked ;-)
                        stats = checkGraphServer(service, device)
                    except EnvironmentError as error:
                        # IP of graphservice not found
                        logger.error(error)
                        sys.exit(1)
                    logger.info("\tSTATS: %s " % (stats))
        # Whats stored in  dictionaries now copy to sqlitedict
        # Initialize db and tables
        db = "./" + "graphinfo" + "_" + str(root) + ".sqlite"
        linksTable = SqliteDict(
            filename=db,
            tablename='links',
            # create new db file if not exists and rewrite if exists
            flag='n',
            autocommit=False)
        devicesTable = SqliteDict(
            filename=db,
            tablename='devices',
            # rewrite only table
            flag='w',
            autocommit=False)
        graphServersTable = SqliteDict(
            filename=db,
            tablename='graphServers',
            # rewrite only table
            flag='w',
            autocommit=False)
        # Copy data from dictionaries
        for k,v in links.iteritems():
            linksTable[k] = v
        linksTable.commit()
        linksTable.close()
        for k,v in devices.iteritems():
            devicesTable[k] = v
        devicesTable.commit()
        devicesTable.close()
        for k,v in graphServers.iteritems():
            graphServersTable[k] = v
        graphServersTable.commit()
        graphServersTable.close()


# In the next file of getting graph info store separately device data
# and then calculate separate link usage or throuput or whatever



# for k,v in g.devices.iteritems():
#    devices[k] = {"node":v.parentNode.id}
# devices.commit()
# devices.close()

# Get list of nodes
# associate links with couples of devices
# find how to get link info from devices
# for each device:
#   ask info from his graph server
# parse and store the info (find a proper way to do that)
# test if that works in
