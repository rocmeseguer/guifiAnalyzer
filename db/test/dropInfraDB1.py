#testMongo.py

from pymongo import MongoClient

from  ...guifiwrapper.guifiwrapper import *

client = MongoClient('mongodb://localhost:27017/')
rootZone = 2444
dbname = 'guifi_'+str(rootZone)+'_1'
db = client[dbname]
client.drop_database(dbname)
#db.drop_collection("zones")
#db.drop_collection("nodes")
#db.drop_collection("devices")
#db.drop_collection("services")
#db.drop_collection("interfaces")
#db.drop_collection("radios")
#db.drop_collection("links")











#index working nodes or store only working nodes and working in general?
#index devices?