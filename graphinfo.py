#!/usr/bin/env python
#
#graphinfo.py

from guifiwrapper import *
from cnmlUtils import *

root = 8076
g = CNMLWrapper(root)

linkid = 16691
link=g.links[linkid]





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



# Get list of nodes
# associate links with couples of devices
# find how to get link info from devices
# for each device:
#   ask info from his graph server
#parse and store the info (find a proper way to do that)
# test if that works in
