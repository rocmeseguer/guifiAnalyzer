from pymongo import MongoClient
import datetime

def initDB():
    """Create traffic database of a zone"""
    client = MongoClient('mongodb://localhost:27017/')
    dbname = 'scalability'
    db = client[dbname]
    return db

def createDB(db):
	dbCollection = db.collection
	#documents = [{'_id':str(i),'machine':str(i),'traffic':{'0':100*i}} for i in range(1,10000)]

	documents = [{'_id':str(i),'machine':str(i)} for i in range(1,10000)]
	dbCollection.insert_many(documents)

def addEmbedded(db, i):
	start = datetime.datetime.now()
	dbCollection = db.collection
	collections = dbCollection.find()
	test = {'Hi':1,'No':2}
	trafficupdates = {c['_id']:{'key':str(i*5),'value':{'Hi':1,'No':2*i*int(c['_id'])}} for c in collections}
	bulk = dbCollection.initialize_unordered_bulk_op()
	for cid,cdata in trafficupdates.iteritems():
		bulk.find({'_id':cid}).upsert().\
				update_one({'$set': {'traffic.'+cdata['key']:cdata['value']}})
	bulk.execute()
	end = datetime.datetime.now()
	print "Time for updates %s: %s" % (i,(end-start).total_seconds())
	none = raw_input('Press Enter')



#db = initDB()
#createDB(db)
#print 'Adding Embedded'
#for i in range(0,11):
#	addEmbedded(db,i)





# How to query for stats?




# Bulk Example
# https://stackoverflow.com/questions/27360600/pymongo-update-multiple-records-with-multiple-data
# bulk = hdd.initialize_ordered_bulk_op()
# for product, product_id in data:
#     hdd.find({'_id': product_id}).update({'$set': {'Speed': products['Speed'],
#                                                    'capacity': products['capacity'],
#                                                    'format': products['format']}})
# bulk.execute()