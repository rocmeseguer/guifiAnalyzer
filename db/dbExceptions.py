#dbExceptions.py

class DocumentNotFound(Exception):
    def __init__(self, dbname, collection, documentId):
    	self.dbname = dbname
        self.collection = collection
        self.documentId = documentId
    def __str__(self):
        msg = self.dbname+" DB: No document of type " + str(self.collection) + "with id: " + str(self.documentId)
        return repr(msg)
