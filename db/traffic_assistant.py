"""
This module implements the backend class that communicates with
MongoDB for the database that stores information that assists
to perform the extraction of value information
"""

from pymongo import MongoClient
from guifiAnalyzer.db.exceptions import DocumentNotFoundError
from guifiAnalyzer.db.settings import SERVER, PORT

def dictAddId(d, id):
        d['_id'] = id
        return d

class TrafficAssistantDB(object):
    """
    3 Collections:
    Links
    Devices
    GraphServices
    """
    def __init__(self, zone, core=False):
        self.zone = zone
        self.core = core
        core_str = "_core" if core else ''
        self.dbname = 'guifi_traffic_assistant_'+str(zone)+core_str
        self.client = None
        self.database = None

    def connect(self):
        self.client = MongoClient('mongodb://'+SERVER+':'+PORT+'/')
        self.database = self.client[self.dbname]

    def storeDictofDicts(self,name,dictionary):
        """	This function store into the database db a the dictionary
    	as a collection with the given name. The dictionary must be in 
        the form {id:dic}"""
        collection = self.database[name]
        dictionaries = [dictAddId(value, key) for key, value in\
                                                dictionary.iteritems()]
        collection.insert_many(dictionaries)

    def getCollection(self,collection):
        documents = self.database[collection].find()
        return [d for d in documents]

    def getLink(self, link_id):
        return self.database.links.find_one({'_id':link_id})

    def getDevice(self, device_id):
        return self.database.devices.find_one({'_id':device_id})

    def getGraphServer(self, graphServer_id):
        return self.database.graphServers.find_one({'_id':graphServer_id})
    
    #def getDocument(db,collection,id): ???


    def updateDocument(self, collection, id, key, value ):
        update = self.database[collection].update_one(
            {'_id':str(id)},
            {
                "$set":{
                    key:value
                },
                "$currentDate": {"lastModified": True}
            }
        )
        if not update.raw_result['updatedExisting']:
            raise DocumentNotFoundError(self.dbname, collection, id)


    #def populateDB() ????
