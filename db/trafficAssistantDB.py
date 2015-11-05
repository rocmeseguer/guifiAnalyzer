from pymongo import MongoClient
"""
This module implements the backend class that communicates with
MongoDB for the database that stores information that assists
to perform the extraction of value information
"""

#Exception
class DocumentNotFound(Exception):
    def __init__(self, collection, documentId):
        self.collection = collection
        self.documentId = documentId
    def __str__(self):
        msg = "No document of type " + str(self.collection) + "with id: " + str(self.documentId)
        return repr(msg)

def dictAddId(d,id):
        d['_id'] = id
        return d

class TrafficAssistantDB(object):
    """
    3 Collections:
    Links
    Devices
    GraphServices
    """

    def __init__(self,zone,core = False):
        self.zone = zone
        self.core = core
        coreStr = "_core" if core else ''
        self.dbname = 'guifi_traffic_'+str(zone)+coreStr
        self.client = None
        self.db = None

    def connect(self):
        self.client = MongoClient('mongodb://localhost:27017/')
        self.db = self.client[self.dbname]

    def storeDictofDicts(self,name,dictionary):
        """	This function store into the database db a the dictionary
    	as a collection with the given name. The dictionary must be in 
        the form {id:dic}"""
        collection = self.db[name]
        dictionaries = [dictAddId(value,key) for key,value in dictionary.iteritems()]
        collection.insert_many(dictionaries)

    def getCollection(self,collection):
        documents = self.db[collection].find()
        return [d for d in documents]
    
    #def getDocument(db,collection,id): ???


    def updateDocument(self, collection, id, key, value ):
        update = self.db[collection].update_one(
            {'_id':str(id)},
            {
                "$set":{
                    key:value
                },
                "$currentDate": {"lastModified": True}
            }
        )
        if not update.raw_result['updatedExisting']:
            raise DocumentNotFound(collection, id)


    #def populateDB() ????