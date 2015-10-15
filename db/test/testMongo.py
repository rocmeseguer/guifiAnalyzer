#testMongo.py

from pymongo import MongoClient

import ..guifiwrapper.guifiwrapper as gi
import ..guifiwrapper.cnmlUtils as cnmlUtils


client = MongoClient('mongodb://localhost:27017/')
db = client.guifiAnalyzer
dbZones = db.zones
dbNodes = db.nodes
dbDevices = db.devices
dbServices = db.services
dbRadios = db.radios
dbInterfaces = db.interfaces
dbLinks = db.Links


g = gi.CNMLWrapper(2444)


def mongoiseNode(node):
    mNode = vars(node)
    # Use node id as MongoDB id
    mNode['_id'] = mNode['id']
    # Delete old id element
    del mNode['id']
    # Keep id of parentZone
    mNode['parentZone'] = mNode['parentZone'].id
    # Keep an array of device ids
    mNode['devices'] = [d for d in mNode['devices']]
    return mNode

def mongoiseService(service):
    mService = vars(service)
    mService['_id'] = mService['id']
    del mService['id']
    mService['parentDevice'] = mService['parentDevice'].id
    mService['interfaces'] = [d for d in mService['interfaces']]
    return mService

def mongoiseDevice(device):
    mDevice = vars(device)
    mDevice['_id'] = mDevice['id']
    del mDevice['id']
    mDevice['parentNode'] = mDevice['parentNode'].id
    mDevice['radios'] = [d for d in mDevice['radios']]
    mDevice['interfaces'] = [d for d in mDevice['interfaces']]
    return mDevice

def mongoiseRadio(radio):
    mRadio = vars(radio)
    mRadio['_id'] = mRadio['id']
    del mRadio['id']
    mRadio['parentDevice'] = mRadio['parentDevice'].id
    mRadio['interfaces'] = [d for d in mRadio['interfaces']]
    return mRadio

def mongoiseInterface(interface):
    mInterface = vars(interface)
    mInterface['_id'] = mInterface['id']
    del mInterface['id']
    mInterface['parentRadio'] = mInterface['parentRadio'].id
    mInterface['links'] = [d for d in mInterface['links']]
    return mInterface


def mongoiseLink(link):
    mLink = vars(link)
    mLink['_id'] = mLink['id']
    del mLink['id']
    mLink['nodeA'] = mLink['nodeA'].id
    mLink['nodeB'] = mLink['nodeB'].id
    mLink['deviceA'] = mLink['deviceA'].id
    mLink['deviceB'] = mLink['deviceB'].id
    mLink['interfaceA'] = mLink['interfaceA'].id
    mLink['interfaceB'] = mLink['interfaceB'].id
    mLink['parentInterface'] = mLink['parentInterface'].id
    mLink['links'] = [d for d in mLink['links']]
    return mLink

# Prepare nodes to add them in MongoDB
zones = [mogoiseZone(zone.zone) for  ]
nodes = [mongoiseNode(node) for node in g.nodes.values()]





#index working nodes or store only working nodes and working in general?
#index devices?