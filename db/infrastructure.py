#testMongo1.py
"""
This module implements the backend class that communicates with
MongoDB for the database that stores all the collected CNML 
information concerning the infrastructure of the selected guifiZone. 
"""


from pymongo import MongoClient
from mongoiseCNML import *
from guifiAnalyzer.db.exceptions import DocumentNotFoundError
from guifiAnalyzer.db.settings import SERVER, PORT

from ..guifiwrapper.guifiwrapper import CNMLWrapper
from ..guifiwrapper.cnmlUtils import *


class InfraDB(object):
    """
    This function implements the storing of a cnml function
    in a MongoDB hierarchical database where each node document
    contains embedded all the sub-elements.
    2 Collections: Zones, Nodes
    """
    def __init__(self, zone, core=False):
        self.zone = zone
        self.core = core
        core_str = "_core" if core else ''
        self.dbname = 'guifi_infra_'+str(zone)+core_str
        self.client = None
        self.database = None

    def connect(self):
        self.client = MongoClient('mongodb://'+SERVER+':'+PORT+'/')
        self.database = self.client[self.dbname]

    # Prepare data to add them in MongoDB
    # Add only workingZone versions

    def populate(self):
        cnmlwrapper = CNMLWrapper(self.zone, True, self.core)
        zones = [mongoiseZone(z.workingZone) for z in\
                                                cnmlwrapper.zones.values()]
        self.database.zones.insert_many(zones)
        nodes = [mongoiseNode(node) for node in cnmlwrapper.nodes.values()]
        self.database.nodes.insert_many(nodes)
    # Alternative insert manner for debugging
    #for node in g.nodes.values():
    #    print type(node)
    #    print node.id
    #    mNode = mongoiseNode(node)
    #    if mNode['_id'] == "65537":
    #        pdb.set_trace()
    #    dbNodes.insert_one(mNode)


    # QUERIES
    def getCollections(self):
        return self.database.zones, self.database.nodes

    def getZones(self):
        return self.database.zones.find()

    def getZone(self,id):
        return self.database.zones.find_one({'_id':str(id)})

    def getNodes(self):
        return self.database.nodes.find()

    def getNode(self,id):
        return self.database.nodes.find_one({'_id':str(id)})

    def getNodeLinks(self,id):
        temp = self.database.nodes.distinct('devices.radios.interfaces.links',
                                 {'_id':id})
        return temp +self.database.nodes.distinct('devices.interfaces.links',
                                         {'_id':id})

    def parseNodeLinks(self, getnode_result):
        links = []
        for device in getnode_result['devices']:
            for radio in device['radios']:
                for interface in radio['interfaces']:
                    links.extend(interface['links'])
            for interface in device['interfaces']:
                    links.extend(interface['links'])
        return links

    def getDevices(self):
        return self.database.nodes.distinct('devices')

    def getDevice(self,id):
        devices = self.database.nodes.find_one({'devices._id':str(id)},\
                                                {'devices.$':1, '_id':0})
        if not devices:
            raise DocumentNotFoundError(self.dbname, 'devices', id)
        else:
            devices = devices['devices']
            for device in devices:
                if device['_id'] == str(id):
                    return device
            raise DocumentNotFoundError(self.dbname, 'devices', id)
    #Maybe first query can be substituted with 
    #self.database.nodes.distinct('devices',{'devices._id':'19623'})  
    #but then again need to iterate and choose the right one

    def getDeviceLinks(self,id):
        temp = self.database.nodes.distinct('devices.radios.interfaces.links',
                                 {'devices._id':id})
        return temp +self.database.nodes.distinct('devices.interfaces.links',
                                         {'devices._id':id})

    def parseDeviceLinks(self, getdevice_result):
        links = []
        for radio in getdevice_result['radios']:
            for interface in radio['interfaces']:
                links.extend(interface['links'])
        for interface in getdevice_result['interfaces']:
                links.extend(interface['links'])
        return links

    def parseDeviceInterface(self, getdevice_result, interface_id):
        for radio in getdevice_result['radios']:
            for interface in radio['interfaces']:
                if interface['_id'] == interface_id:
                   return interface  
        for interface in getdevice_result['interfaces']:
            if interface['_id'] == interface_id:
                       return interface

    def parseDeviceRadio(self, getdevice_result, radio_id):
        for radio in getdevice_result['radios']:
            if radio['_id'] == radio_id:
               return radio
        # No result
        return None


    def getServices(self):
        return self.database.nodes.distinct('services')

    def getService(self,id):
        services = self.database.nodes.find_one({'services._id':str(id)},\
                                                 {'services.$':1, '_id':0})
        if not services:
            raise DocumentNotFoundError(self.dbname, 'services', id)
        else:
            services = services['services']
            for service in services:
                if service['_id'] == str(id):
                    return service
            raise DocumentNotFoundError(self.dbname, 'services', id)

    def getRadios(self):
        return self.database.nodes.distinct('devices.radios')

    def getRadio(self, radio_id):
        #TODO this should probably be getRadio(self, device_id, radio_id)
        radios = self.database.nodes.distinct("devices.radios",
                                    {'devices.radios._id':radio_id})
        #TODO this should probably be 
        #radios = self.database.nodes.distinct("devices.radios",
        #                            {'devices.radios._id':{'device':device_id
        #                                                   'radio':radio_id})
        #TODO also change next 
        if radios:
            for radio in radios:
                if radio['_id'] == radio_id:
                    return radio
        # `If none of the above works
        raise DocumentNotFoundError(self.dbname, 'radio', radio_id)



    def getIfaces(self):
        temp = self.database.nodes.distinct('devices.radios.interfaces')
        return temp+self.database.nodes.distinct('devices.interfaces')

    def getInterface(self, iface_id):
        ifaces = self.database.nodes.distinct("devices.radios.interfaces",
                                {'devices.radios.interfaces._id':iface_id})
        if ifaces:
            for iface in ifaces:
                if iface['_id'] == iface_id:
                    return iface
        ifaces = self.database.nodes.distinct("devices.interfaces",
                                    {'devices.interfaces._id':iface_id})
        if ifaces:
            for iface in ifaces:
                if iface['_id'] == iface_id:
                    return iface
        # `If none of the above works
        raise DocumentNotFoundError(self.dbname, 'interfaces', iface_id)


    def getLinks(self):
        temp = self.database.nodes.distinct('devices.radios.interfaces.links')
        return temp+self.database.nodes.distinct('devices.interfaces.links')

    def getLink(self, link_id):
        links = self.database.nodes.distinct("devices.radios.interfaces.links",
                                {'devices.radios.interfaces.links._id':link_id})
        if links:
            for link in links:
                if link['_id'] == link_id:
                    return link
        links = self.database.nodes.distinct("devices.interfaces.links",
                                    {'devices.interfaces.links._id':link_id})
        if links:
            for link in links:
                if link['_id'] == link_id:
                    return link
        # If none of the above works
        raise DocumentNotFoundError(self.dbname, 'links', link_id)

    def parseLinkSnmpKeyFromDevice(self, device, link):
        # Find correct interface
        if link['deviceA'] == device['_id']:
            interface_id = link['interfaceA']
        elif link['deviceB'] == device['_id']:
            interface_id = link['interfaceB']
        else:
            raise DocumentNotFoundError(self.dbname, 'device', device['_id'])
        interface = self.parseDeviceInterface(device, interface_id)
        radio_id = interface['parent']
        radio = self.parseDeviceRadio(device, radio_id)
        snmp_key = None
        if interface['snmp_index'] != None:
            snmp_key = interface['snmp_index']
        elif radio and radio['snmp_index'] != None:
            snmp_key = radio['snmp_index']
        elif interface['snmp_name'] != None or (radio and
                                         (radio['snmp_name'] != None)):
            snmp_key = radio['_id']['radio']
        else:
            raise DocumentNotFoundError(self.dbname,
                                        'snmp_key of link', link['_id'])
        return snmp_key

    def parseLinkDeviceRadioMode(self, device, link):
        # Find correct interface
        if link['deviceA'] == device['_id']:
            interface_id = link['interfaceA']
        elif link['deviceB'] == device['_id']:
            interface_id = link['interfaceB']
        else:
            raise DocumentNotFoundError(self.dbname, 'device', device['_id'])
        interface = self.parseDeviceInterface(device, interface_id)
        radio_id = interface['parent']
        radio = self.parseDeviceRadio(device, radio_id)
        radio_mode = None
        if radio:
            radio_mode = radio['mode']
        return radio_mode
