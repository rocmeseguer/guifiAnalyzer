"""
This module converts CNML objects to MongoDB compatible dictionaries
"""


def mongoiseZone(zone):
    mZone = vars(zone)
    mZone['_id'] = str(mZone['id'])
    del mZone['id']
    mZone['subzones'] = [str(z) for z in mZone['subzones']]
    mZone['nodes'] = [str(n) for n in mZone['nodes']]
    return mZone


def mongoiseNode(node):
    mNode = vars(node)
    # Use node id as MongoDB id
    mNode['_id'] = str(mNode['id'])
    # Delete old id element
    del mNode['id']
    # Keep id of parentZone
    mNode['parentZone'] = str(mNode['parentZone'].id)
    # Keep an array of device ids
    devices = [mongoiseDevice(d) for d in mNode['devices'].values()]
    mNode['devices'] = devices
    services = [mongoiseService(d) for d in mNode['services'].values()]
    mNode['services'] = services
    return mNode

def mongoiseService(service):
    mService = vars(service)
    mService['_id'] = str(mService['id'])
    del mService['id']
    mService['parentDevice'] = str(mService['parentDevice'].id)
    return mService

def mongoiseDevice(device):
    mDevice = vars(device)
    mDevice['_id'] = str(mDevice['id'])
    del mDevice['id']
    mDevice['parentNode'] = str(mDevice['parentNode'].id)
    radios = [mongoiseRadio(d) for d in mDevice['radios'].values()]
    mDevice['radios'] = radios
    interfaces = [mongoiseInterface(d) for d in mDevice['interfaces'].values()]
    mDevice['interfaces'] = interfaces
    return mDevice

def mongoiseRadio(radio):
    mRadio = vars(radio)
    mRadio['_id'] = {'device':str(mRadio['parentDevice'].id), 'radio':str(mRadio['id'])}
    del mRadio['id']
    mRadio['parentDevice'] = str(mRadio['parentDevice'].id)
    interfaces = [mongoiseInterface(d) for d in mRadio['interfaces'].values()]
    mRadio['interfaces'] = interfaces
    return mRadio

def mongoiseInterface(interface):
    mInterface = vars(interface)
    mInterface['_id'] = str(mInterface['id'])
    del mInterface['id']
    # Watch out that the parent can be either radio or device
    mInterface['parent'] = str(mInterface['parentRadio'].id)
    del mInterface['parentRadio']
    links = [mongoiseLink(d) for d in mInterface['links'].values()]
    mInterface['links'] = links
    return mInterface


def mongoiseLink(link):
    mLink = vars(link)
    mLink['_id'] = str(mLink['id'])
    del mLink['id']
    mLink['nodeA'] = str(mLink['nodeA'].id)
    mLink['nodeB'] = str(mLink['nodeB'].id)
    mLink['deviceA'] = str(mLink['deviceA'].id)
    mLink['deviceB'] = str(mLink['deviceB'].id)
    mLink['interfaceA'] = str(mLink['interfaceA'].id)
    mLink['interfaceB'] = str(mLink['interfaceB'].id)
    mLink['parentInterface'] = str(mLink['parentInterface'].id)
    return mLink

