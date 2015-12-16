

#db.collection.find({'traffic.50.No':{'$gte':199980}})
# Search how to search for example for specific mins if mins are
# field name

# 2 collections one with one document and general info like when experiment started finished etc.
# one with all devices and measurements

import pprint
data = {'traffic': 
			{'0':{'traffic_out':float('nan'), 
				'traffic_in':float('nan')}
			}, 
		'availability': 
			{'max_latency':float('nan'), 
			'last_sample_time':'',
			'last_sample_date':'', 
			'last_online':'',
			'avg_latency':float('nan'), 
			'last_availability':float('nan'),
			'availability':float('nan')
			}
		}

#pprint.pprint(data)

dic = {'_id' : 'a',
    'total_measurements' : 0,
    'total_correct_measurements' : 0,
    'total_traffic_in' : 0,
    'total_traffic_out' : 0,
    'measurements' : [
                {'time':00, 'measured':False, 'has_data':False, 'data':data.copy()},
                {'time':05, 'measured':False, 'has_data':False, 'data':data.copy()},
                {'time':10, 'measured':False, 'has_data':False, 'data':data.copy()},
                {'time':15, 'measured':False, 'has_data':False, 'data':data.copy()},
                {'time':20, 'measured':False, 'has_data':False, 'data':data.copy()},
                {'time':25, 'measured':False, 'has_data':False, 'data':data.copy()},
                {'time':30, 'measured':False, 'has_data':False, 'data':data.copy()},
                {'time':35, 'measured':False, 'has_data':False, 'data':data.copy()},
                {'time':40, 'measured':False, 'has_data':False, 'data':data.copy()},
                {'time':45, 'measured':False, 'has_data':False, 'data':data.copy()},
                {'time':50, 'measured':False, 'has_data':False, 'data':data.copy()},
                {'time':55, 'measured':False, 'has_data':False, 'data':data.copy()}
            ]

    }

#pprint.pprint(dic)
#pprint.pprint(dic['measurements'][0]['data'])

def getTimeSlot(minute):
    for i in range(0, 60, 5):
        if (minute > i) and (minute <= (i+5)):
            print 'In'
            return i/5


def testDB():
	from ..traffic import TrafficDB

	test = TrafficDB(2444,False)
	test.connect()
	#test.database.traffic.insert_one(dic)

	test_data = {'traffic': 
				{'0':{'traffic_out':1, 
					'traffic_in':1}
				}, 
			'availability': 
				{'max_latency':1, 
				'last_sample_time':'',
				'last_sample_date':'', 
				'last_online':'',
				'avg_latency':float('nan'), 
				'last_availability':float('nan'),
				'availability':float('nan')
				}
			}

	bulk = test.database.traffic.initialize_unordered_bulk_op()
	bulk.find({'_id':'a', 'measurements.time':0}).\
		upsert().update_one({'$set':{'measurements.$.data':test_data}})
	bulk.execute()
	#test.database.traffic.update_one({'_id':'a','measurements.time':0},
	#			{'$set':{'measurements.$.data':test_data}})

#t.database.traffic.find({},{'measurements':{'$elemMatch':{'time':0}}})
#t.devices.find({'_id':{'$regex':'^5617'}}).pretty()
