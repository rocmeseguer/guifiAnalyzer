class DocumentNotFoundError(Exception):
    def __init__(self, dbname, collection, document_id):
    	self.dbname = dbname
        self.collection = collection
        self.document_id = document_id
    def __str__(self):
        msg = self.dbname+" DB: No document of type " +\
                str(self.collection) + "with id: " + str(self.document_id)
        return repr(msg)

class BulkAlreadyExistsError(Exception):
    def __init__(self, dbname, collection):
        self.dbname = dbname
        self.collection = collection
    def __str__(self):
        msg = self.dbname+" DB: A bulk operation already exists"+\
                    " for the collection: "+self.collection
        return repr(msg)

class NoBulkExistsError(Exception):
    def __init__(self, dbname):
        self.dbname = dbname
    def __str__(self):
        msg = self.dbname+" DB: No bulk action exists"
        return repr(msg)
