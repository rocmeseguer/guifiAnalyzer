#testMongo.py

from pymongo import MongoClient

from  ...guifiwrapper.guifiwrapper import *

client = MongoClient('mongodb://localhost:27017/')
db = client.guifiAnalyzer
#db.drop_database()
db.drop_collection("zones")
db.drop_collection("nodes")
db.drop_collection("devices")
db.drop_collection("services")
db.drop_collection("interfaces")
db.drop_collection("radios")
db.drop_collection("links")











#index working nodes or store only working nodes and working in general?
#index devices?