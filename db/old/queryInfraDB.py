from pymongo import MongoClient

"""
This module implements the main queries of the
embeded-document based infrastructure DB 
"""

# Exception
class DocumentNotFound(Exception):
	def __init__(self, collection, documentId):
		self.collection = collection
		self.documentId = documentId
	def __str__(self):
		msg = "No document of type " + str(self.collection) + "with id: " + str(self.documentId)
		return repr(msg)



def getDB(zone,core=False):
	client = MongoClient('mongodb://localhost:27017/')
	coreStr = "_core" if core else ''
	dbname = 'guifi_infra_'+str(zone)+coreStr
	db = client[dbname]
	return db

def getCollections(db):
	return db.zones, db.nodes

def getZones(db):
	return db.zones.find()

def getZone(db,id):
	return db.zones.find_one({'_id':str(id)})

def getNodes(db):
	return db.nodes.find()

def getNode(db,id):
	return db.nodes.find_one({'_id':str(id)})

def getDevices(db):
	return db.nodes.distinct('devices')

def getDevice(db,id):
	devices = db.nodes.find_one({'devices._id':str(id)},{'devices.$':1,'_id':0})
	if not devices:
		raise DocumentNotFound('devices',id)
	else:
		devices = devices['devices']
		for device in devices:
			if device['_id'] == str(id):
				return device
		raise DocumentNotFound('devices',id)
#Maybe first query can be substituted with 
#db.nodes.distinct('devices',{'devices._id':'19623'})  
#but then again need to iterate and choose the right one

def getServices(db):
	return db.nodes.distinct('services')

def getService(db,id):
	services = db.nodes.find_one({'services._id':str(id)},{'services.$':1,'_id':0})
	if not services:
		raise DocumentNotFound('services',id)
	else:
		services = services['services']
		for service in services:
			if service['_id'] == str(id):
				return service
		raise DocumentNotFound('services',id)

def getRadios(db):
	return db.nodes.distinct('devices.radios')

def getIfaces(db):
	temp = db.nodes.distinct('devices.radios.interfaces')
	return temp+db.nodes.distinct('devices.interfaces')

def getLinks(db):
	temp = db.nodes.distinct('devices.radios.interfaces.links')
	return temp+db.nodes.distinct('devices.interfaces.links')



