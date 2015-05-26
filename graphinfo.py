#!/usr/bin/env python
#
#graphinfo.py


# Pordria pretender que yo soy un servidor de graficas?

from guifiwrapper import *
from cnmlUtils import *

def getDeviceGraphServer(device,node=None):
    #Get info from device
    if device.graphserverId:
        return device.graphserverId
    #get info from node
    if not node:
        node = getParentCNMLNode(device)
    if node.graphserverId:
        return node.graphserverId
    zone = node.parentZone
    if zone.graphserverId:
        return zone.graphserverId
    else:
        while zone.parentzone:
            zone = g.zones[zone.parentzone]
            if zone.graphserverId:
                return zone.graphserverId
        return 0

root = 8076
g = CNMLWrapper(root)

linkid = 16691
link=g.links[linkid]



serverA = getDeviceGraphServer(link.deviceA,link.nodeA)
serverB = getDeviceGraphServer(link.deviceB,link.nodeB)

print serverA
print serverB






# Get list of nodes
# associate links with couples of devices
# find how to get link info from devices
# for each device:
#   ask info from his graph server
#parse and store the info (find a proper way to do that)
# test if that works in
