from pymongo import MongoClient

#Exception
class DocumentNotFound(Exception):
    def __init__(self, collection, documentId):
        self.collection = collection
        self.documentId = documentId
    def __str__(self):
        msg = "No document of type " + str(self.collection) + "with id: " + str(self.documentId)
        return repr(msg)


def initDB(zone, core=False):
    """Create traffic database of a zone"""
    client = MongoClient('mongodb://localhost:27017/')
    coreStr = "_core" if core else ''
    dbname = 'guifi_traffic_'+str(zone)+coreStr
    db = client[dbname]
    return db


def dictAddId(d,id):
        d['_id'] = id
        return d

def storeDictofDicts(db,name,dictionary):
    """	This function store into the database db a the dictionary
	as a collection with the given name. The dictionary must be in 
    the form {id:dic}"""
    collection = db[name]
    dictionaries = [dictAddId(value,key) for key,value in dictionary.iteritems()]
    collection.insert_many(dictionaries)

def getCollection(db,collection):
    documents = db[collection].find()
    return [d for d in documents]
#def getDocument(db,collection,id):


def updateDocument(db, collection, id, key, value ):
    update = db[collection].update_one(
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
    return


#def populateDB()