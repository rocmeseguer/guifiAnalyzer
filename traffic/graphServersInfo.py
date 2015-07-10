#snpservers.py



from ..guifiwrapper.guifiwrapper import *
from ..guifiwrapper.cnmlUtils import *
from snpservicesClient import *

import urllib2
import socket
import csv
from netaddr import IPNetwork, IPAddress

from collections import Counter


from ..lib.pyGuifiAPI import *
from ..lib.pyGuifiAPI.error import GuifiApiError
import urllib

from exceptions import *


root = 8346 #Lucanes
#root = 2444 #Osona
#root = 18668 #Castello
g = CNMLWrapper(root)
#Get connection object form guifiwrapper
conn = g.conn


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
            command="help",
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
                service, found = getDeviceGraphService(device)
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
                graphServers[service.id]['found'] = found
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
#graphServers['None'] = {}
#graphServers['None']['ip'] = None
#graphServers['None']['devices'] = []

def zonesGraphServers(zone, depth=0, counter=0):
	graphServers = {}
    tabs = "\t"*depth
    gr = zone.workingZone.graphserverId
    if gr :
    	try:
    		graphServers[service.id] = {}
    		ip = checkGraphServer(service,device, []])
	        if gr in graphServers:
	            counter += 1
	            logger.info("%sZone: %s Graphserver: %s, %s" % (tabs,str(zone.id),str(gr),graphServers[gr]))
	        else:
	            logger.info("%sZone: %s Graphserver: %s, %s" % (tabs,str(zone.id),str(gr),"Not found in CNML"))
    else:
        logger.info("%sZone: %s Graphserver: %s" % (tabs,str(zone.id),"No server found"))
    for z in zone.subzones.values():
        zonesGraphServers(z, (depth+1),counter) 

return zonesGraphServers(g.guifizone)