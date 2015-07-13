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

import re

#prepare regular expresion
r = re.compile('http:\/\/([^\/]*).*')

#root = 8346 #Lucanes
root = 2444 #Osona
#root = 18668 #Castello
g = CNMLWrapper(root)
#Get connection object form guifiwrapper
conn = g.conn


def checkGuifiSubnet(ip):
    return IPAddress(ip) in IPNetwork("10.0.0.0/8")

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

def checkGraphServer(graphService, ipBlacklist, checkedUrl=False):
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
        return checkGraphServer(graphService, ipBlacklist, checkedUrl)
    except socket.timeout:
        ipBlacklist.append(ip)
        return checkGraphServer(graphService, ipBlacklist, checkedUrl)

graphServers = {}
def zonesGraphServers(zone):
    gr = zone.workingZone.graphserverId
    if gr :
        if gr not in graphServers :
            try:
                graphServers[gr] = {}
                graphServers[gr]['zones']= [zone.id]
                if gr in g.services:
                    ip = checkGraphServer(g.services[gr],[])
                    graphServers[gr]['ip'] = ip
                else:
                    graphServers[gr]['NotInCNML'] = True
                    graphServers[gr]['ip'] = None
            except NoWorkingIPError as e:
                logger.error(e)
                graphServers[gr]['ip'] = None
                graphServers[gr]['ipBlackList'] = e.ipBlackList
                ip = None
            except ServerMisconfiguredError as e:
                logger.error(e)
                graphServers[gr]['ip'] = None
                graphServers[gr]['misconfigured'] = True
            #logger.info("%sZone: %s Graphserver: %s" % (tabs,str(zone.id),"No server found"))
        else:
            graphServers[gr]['zones'].append(zone.id)
    for z in zone.subzones.values():
        zonesGraphServers(z) 

zonesGraphServers(g.guifizone)

counter = 0
def printZonesGraphServers(zone, depth=0):
    tabs = "\t"*depth
    gr = zone.workingZone.graphserverId
    counter += 1
    print counter
    if gr :
        if gr in graphServers:
            counter += 1
            logger.info("%sZone: %s Graphserver: %s, %s" % (tabs,str(zone.id),str(gr),graphServers[gr]))
        else:
            logger.info("%sZone: %s Graphserver: %s, %s" % (tabs,str(zone.id),str(gr),"Not found in CNML"))
    else:
        logger.info("%sZone: %s Graphserver: %s" % (tabs,str(zone.id),"No server found"))
    for z in zone.subzones.values():
        printZonesGraphServers(z, (depth+1))

printZonesGraphServers(g.guifizone)

workingGraphServers = {g:graphServers[g] for g in graphServers if graphServers[g]['ip']}
print len(g.guifizone.allsubzones)
logger.info("\t# of Total Graphservers:%s" % (len(graphServers)-1))
logger.info("\t# of Working GraphServers:%s\t%s" % (len(workingGraphServers),len(workingGraphServers)/float(len(graphServers)-1)))
