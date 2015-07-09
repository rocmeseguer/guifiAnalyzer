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
import socket
import csv
from netaddr import IPNetwork, IPAddress
import sys

from collections import Counter


from ..lib.pyGuifiAPI import *
from ..lib.pyGuifiAPI.error import GuifiApiError
import urllib
import re

from exceptions import *

#prepare regular expresion
r = re.compile('http:\/\/([^\/]*).*')

#root = 8346 #Lucanes
#root = 2444 #Osona
root = 18668 #Castello
g = CNMLWrapper(root)
#Get connection object form guifiwrapper
conn = g.conn

misDevices = []
wtfDevices = []


#  Store Example usage of sqlitedict:
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

#  Read Example usages of sqlitedict


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
                raise NoCNMLServerError(device)
            # return None
    try:
        service = g.services[serviceId]
    except KeyError as err:
        #Graph service not working or not in the parsed CNML
        raise NoCNMLServerError(device)
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


def getServiceUrlApi(graphService):
    try:
        # Detect if a url already has been checked
        data = {'command':'guifi.service.get','service_id':graphService.id}
        params = urllib.urlencode(data)
        (codenum, response) = conn.sendRequest(params)
        if codenum == constants.ANSWER_GOOD:
           url = response['service']['var']['url']
           url = r.match(url).group(1)
           return url
        else:
            extra = response['extra'] if 'extra' in response else None
            raise GuifiApiError(response['str'], response['code'], extra)
    except URLError as e:
        raise EnvironmentError("Guifi web not replying, %s" % e)



# def checkDeviceGraph(url, device):
#     data = snpRequest(
#         url,
#         command="stats",
#         args={
#             "devices": [
#                 device.id]},
#         debug=False,
#         timeout=3)
#     data = data.rstrip()
#     #return data
#     if data == str(device.id)+"|0,0,0.00,0,,,0":
#         #Check if server is responsible for the nodes
#         devices = graphServerDevices(graphService)
#         if device.id in devices:
#             # If yes, then it means that the node locally is misconfigured
#             logger.error("Misconfigured device %s" % (device.id))
#             misDevices.append(device)
#         else:
#             logger.error("VAYA PUTA MIERDA device %s" % (device.id))
#             wtfDevices.append(device)
#         return None
#     return

#def checkGraphData(data,device)



# Want a blacklist to return or not?
def checkGraphServer(graphService, device, ipBlacklist, checkedUrl=False):
    try:
        ip = getGraphServiceIP(graphService,ipBlacklist)
        print ip
    except EnvironmentError as e:
        # No more IPs from CNML, try to get url from Guifi web
        try:
            # If not already check url
            if not checkedUrl:
                checkedUrl = True
                ip = getServiceUrlApi(graphService)
            # Else no IP, no URL -> raise the error
            else :
                raise NoWorkingIPError(graphService, ipBlacklist)
        except EnvironmentError as e:
            raise NoWorkingIPError(graphService, ipBlacklist)
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
        if data:
            return ip
    except URLError as e:
        if hasattr(e, 'reason'):
            ipBlacklist.append(ip)
            logger.error('Failed to reach server')
            logger.error(e.reason)
            #global counters here
        elif hasattr(e,'code'):
            logger.error('Server not configured correctly')
            logger.error('Error code:', e.code)
            raise ServerMisconfiguredError(graphService)
        return checkGraphServer(graphService, device, ipBlacklist, checkedUrl)
    except socket.timeout:
        ipBlacklist.append(ip)
        return checkGraphServer(graphService, device, ipBlacklist, checkedUrl)


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


def prepareDirs():
    """
    Create result dirs
    """
    dirs = []
    basedir = os.path.join(os.getcwd(), 'guifiAnalyzerOut')
    dirs.append(basedir)
    packagedir = os.path.join(basedir, 'traffic')
    dirs.append(packagedir)
    zonedir = os.path.join(packagedir, str(root))
    dirs.append(zonedir)
    for d in dirs:
        if not os.path.exists(d):
            os.makedirs(d)
    return zonedir

def initStorage(directory):
    """
    Initialize db and tables
    """
    #db = "./" + "graphinfo" + "_" + str(root) + ".sqlite"
    db = os.path.join(directory,"data.sqld")
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
    return (linksTable,devicesTable,graphServersTable)

def closeStorage(tables):
    for t in tables:
        t.close()

def  storeDict2Table(dictionary,table):
    for k,v in dictionary.iteritems():
        table[k] = v
    table.commit()

#def main():
enumDevice = {0:'deviceA',1:'deviceB'}
enumGraphServer = {0:'graphServerA',1:'graphServerB'}
links = {}
devices = {}
graphServers = {}
for link in g.links.values():
    logger.info("LINK: %s" % link.id)
    links[link.id]= {'nodeA':link.nodeA.id,
                    'nodeB':link.nodeB.id}
    for index,device in enumerate([link.deviceA, link.deviceB]):
        logger.info("\tDEVICE: %s" % (device.id))
        if device.id in devices:
            logger.warning("\tAlready analyzed device: %s" % device.id)
            # Complete link information
            links[link.id][enumDevice[index]] = device.id
            links[link.id][enumGraphServer[index]] = devices[device.id]['graphServer']
        else:
            devices[device.id] = {'link':link.id}
            try:
                service = getDeviceGraphService(device)
                # Using enum to avoid if else
                links[link.id][enumDevice[index]] = device.id
                links[link.id][enumGraphServer[index]] = service.id
                logger.info("\t\tGraphserver %s" % (service.id))
                devices[device.id]['graphServer'] = service.id
            except NoCNMLServerError as error:
                logger.error(error)
                # Using enum to avoid if else
                links[link.id][enumDevice[index]] = error.device.id
                links[link.id][enumGraphServer[index]] = None
                devices[device.id]['graphServer'] = None
                continue
            if service.id in graphServers:
                logger.warning("\t\tAlready analyzed graphserver: %s" % service.id)
            else:
                #Initialize devices list
                graphServers[service.id] = {}
                graphServers[service.id]['devices'] = []
                try:
                    ipBlacklist = []
                    ip = checkGraphServer(service,device, ipBlacklist)
                    if ip:
                        graphServers[service.id]['ip'] = ip
                    else:
                        # Anyway ip value here is None
                        # Just writting explicitly for clarity
                        graphServers[service.id]['ip'] = None
                    #if not ip:
                        # The ip was found but no data for this device on this graphserver
                        # In this case should I ask with snmp?
                #except EnvironmentError as error:
                #    logger.error("\t\tCould not find working IP of graphserver %s of device %s\n Error: %s" % (service.id,device.id,error))
                #    ip = None
                except NoWorkingIPError as e:
                    logger.error(e)
                    graphServers[service.id]['ip'] = None
                    graphServers[service.id]['ipBlackList'] = e.ipBlackList
                    ip = None
                except ServerMisconfiguredError as e:
                    logger.error(e)
                    graphServers[service.id]['misconfigured'] = True
                    #continue
                    #sys.exit(1)
                #logger.info("\tThe ip %s of graphserver %s is correct for the device %s" % (ip,service.id,device.id))
                logger.info("\t\t IP %s" % ip)
#Assign devices to graphServers
graphServers['None'] = {}
graphServers['None']['ip'] = None
graphServers['None']['devices'] = []
print graphServers
for key,d in devices.iteritems():
    if d['graphServer']:
        (graphServers[d['graphServer']]['devices']).append(key)
    else:
        (graphServers['None']['devices']).append(key)

# Store results
storeDir = prepareDirs()
linksTable,devicesTable,graphServersTable = initStorage(storeDir)
storeDict2Table(links,linksTable)
storeDict2Table(devices,devicesTable)
storeDict2Table(graphServers,graphServersTable)
closeStorage([linksTable,devicesTable,graphServersTable])


# Print statistics
logger.info("DEVICES STATS")
logger.info("\t# of Total Devices in Links:%s" % len(devices))
logger.info("\t# of Devices without GraphServer:%s\t%s" % (len(graphServers['None']['devices']),len(graphServers['None']['devices'])/float(len(devices))))
temp = 0
for key,gr in graphServers.iteritems():
    if not gr['ip'] and key != 'None':
        temp += len(gr['devices'])
logger.info("\t#{ of Devices with GraphServer without working IP:%s\t%s" % (temp,temp/float(len(devices))))
#logger.info("\t\t# of Locally Misconfigured Devices:%s\t%s" % (len(misDevices),len(misDevices)/float(len(devices))))
#logger.info("\t\t# of WTF Devices:%s\t%s" % (len(wtfDevices),len(wtfDevices)/float(len(devices))))
logger.info("\t# devs to be graphed: %s\t%s" % ((len(devices)-len(graphServers['None']['devices'])-temp),(len(devices)-len(graphServers['None']['devices'])-temp)/float(len(devices))))

workingGraphServers = {g:graphServers[g] for g in graphServers if graphServers[g]['ip']}
graphedDevices = {d:devices[d] for d in devices if devices[d]['graphServer'] in workingGraphServers}
#print links
# Can find the graphed links it in a better way fixing the above code
# Also, due to if some deviceA or deviceB are missing
graphedLinks = {l:links[l] for l in links if (links[l]['deviceA'] in graphedDevices) and (links[l]['deviceB'] in graphedDevices)}
semiGraphedLinks = {l:links[l] for l in links if (links[l]['deviceA'] in graphedDevices) != (links[l]['deviceB'] in graphedDevices)}

logger.info("LINKS STATS")
logger.info("\t# of Total Links:%s" % len(links))
logger.info("\t# of Totally Graphed Links:%s\t%s" % (len(graphedLinks),len(graphedLinks)/float(len(links))))
logger.info("\t# of Partially Graphed Links:%s\t%s" % (len(semiGraphedLinks),len(semiGraphedLinks)/float(len(links))))
logger.info("GRAPHSERVER STATS")
for key,s in graphServers.iteritems():
    logger.info("Server %s : %s devices, Working: %s" % (key,len(s['devices']),('Yes' if s['ip'] else 'No')  ))
#logger.info(len(workingGraphServers))
logger.info("\t# of Total Graphservers:%s" % (len(graphServers)-1))
logger.info("\t# of Working GraphServers:%s\t%s" % (len(workingGraphServers),len(workingGraphServers)/float(len(graphServers)-1)))

# - Add stats about how many of the devices on the same link have the
#   same graphserver etc
# SOS -Change libcnml to add mainipv4 attribute to devices
# - Print with the ips the code or that it didn;t reply
# - Cannot find all locally misconfigured devices in the first run. Need to
#   do it in a second run
# - Mirrar si es core lo que no funciona o no
# - Some nodes may be graphed from more than one server. There is some
#   kind of hierarchy, i.e. server that graphs whole Osona, another server that grahps
#   only Vic etc.
#  - Admin in Guifi Web can see latest stats. maybe we should get info from there

#main()




if __name__ == "__main__":
    if False:
        main()

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
