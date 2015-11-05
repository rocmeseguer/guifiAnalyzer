from pymongo import MongoClient



client = MongoClient('mongodb://localhost:27017/')
rootZone = 2444
dbname = 'guifi_'+str(rootZone)
db = client[dbname]
dbZones = db.zones
dbNodes = db.nodes
dbDevices = db.devices
dbServices = db.services
dbRadios = db.radios
dbInterfaces = db.interfaces
dbLinks = db.links



for link in dbLinks.find():
	print link['_id']