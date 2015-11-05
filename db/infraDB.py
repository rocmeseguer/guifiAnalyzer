#testMongo1.py

"""
This module implements the backend class that communicates with
MongoDB for the database that stores all the collected CNML 
information concerning the infrastructure of the selected guifiZone. 
"""


from pymongo import MongoClient
from mongoiseCNML import *
from dbExceptions import *

from ..guifiwrapper.guifiwrapper import *


class InfraDB(object):
    """
    This function implements the storing of a cnml function
    in a MongoDB hierarchical database where each node document
    contains embedded all the sub-elements.
    2 Collections: Zones, Nodes
    """
    def __init__(self, zone, core = False):
        self.zone = zone
        self.core = core
        coreStr = "_core" if core else ''
        self.dbname = 'guifi_infra_'+str(zone)+coreStr
        self.client = None
        self.db = None

    def connect(self):
        self.client = MongoClient('mongodb://localhost:27017/')
        self.db = self.client[self.dbname]

    # Prepare data to add them in MongoDB
    # Add only workingZone versions

    def populate(self):
        g = CNMLWrapper(self.zone,True,self.core)
        zones = [mongoiseZone(z.workingZone) for z in g.zones.values() ]
        self.db.zones.insert_many(zones)
        nodes = [mongoiseNode(node) for node in g.nodes.values()]
        self.db.nodes.insert_many(nodes)
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
        return self.db.zones, self.db.nodes

    def getZones(self):
        return self.db.zones.find()

    def getZone(self,id):
        return self.db.zones.find_one({'_id':str(id)})

    def getNodes(self):
        return self.db.nodes.find()

    def getNode(self,id):
        return self.db.nodes.find_one({'_id':str(id)})

    def getDevices(self):
        return self.db.nodes.distinct('devices')

    def getDevice(self,id):
        devices = self.db.nodes.find_one({'devices._id':str(id)},{'devices.$':1,'_id':0})
        if not devices:
            raise DocumentNotFound(self.dbname, 'devices',id)
        else:
            devices = devices['devices']
            for device in devices:
                if device['_id'] == str(id):
                    return device
            raise DocumentNotFound(self.dbname, 'devices',id)
    #Maybe first query can be substituted with 
    #self.db.nodes.distinct('devices',{'devices._id':'19623'})  
    #but then again need to iterate and choose the right one

    def getServices(self):
        return self.db.nodes.distinct('services')

    def getService(self,id):
        services = self.db.nodes.find_one({'services._id':str(id)},{'services.$':1,'_id':0})
        if not services:
            raise DocumentNotFound(self.dbname, 'services',id)
        else:
            services = services['services']
            for service in services:
                if service['_id'] == str(id):
                    return service
            raise DocumentNotFound(self.dbname, 'services',id)

    def getRadios(self):
        return self.db.nodes.distinct('devices.radios')

    def getIfaces(self):
        temp = self.db.nodes.distinct('devices.radios.interfaces')
        return temp+self.db.nodes.distinct('devices.interfaces')

    def getLinks(self):
        temp = self.db.nodes.distinct('devices.radios.interfaces.links')
        return temp+self.db.nodes.distinct('devices.interfaces.links')




