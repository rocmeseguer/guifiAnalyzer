"""
This module implements the backend class that communicates with
MongoDB for the database that stores information that assists
"""

from pymongo import MongoClient
from pymongo.errors import BulkWriteError
from guifiAnalyzer.db.exceptions import BulkAlreadyExistsError,\
                                            NoBulkExistsError
import copy
from pprint import pprint

import pdb



empty_device_data = {'traffic': 
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

empty_device_document = {'_id' : None,
                'total_measurements' : 0,
                'total_correct_measurements' : 0,
                'total_traffic_in' : 0,
                'total_traffic_out' : 0,
                'measurements' : [
                            {'time':00, 'measured':False, 'has_data':False,
                                'data':empty_device_data.copy()},
                            {'time':05, 'measured':False, 'has_data':False, 
                                'data':empty_device_data.copy()},
                            {'time':10, 'measured':False, 'has_data':False, 
                                'data':empty_device_data.copy()},
                            {'time':15, 'measured':False, 'has_data':False, 
                                'data':empty_device_data.copy()},
                            {'time':20, 'measured':False, 'has_data':False, 
                                'data':empty_device_data.copy()},
                            {'time':25, 'measured':False, 'has_data':False, 
                                'data':empty_device_data.copy()},
                            {'time':30, 'measured':False, 'has_data':False, 
                                'data':empty_device_data.copy()},
                            {'time':35, 'measured':False, 'has_data':False, 
                                'data':empty_device_data.copy()},
                            {'time':40, 'measured':False, 'has_data':False, 
                                'data':empty_device_data.copy()},
                            {'time':45, 'measured':False, 'has_data':False, 
                                'data':empty_device_data.copy()},
                            {'time':50, 'measured':False, 'has_data':False, 
                                'data':empty_device_data.copy()},
                            {'time':55, 'measured':False, 'has_data':False, 
                                'data':empty_device_data.copy()}
                        ]

                }


class TrafficDB(object):
    """Implements MongoDB backend for storing traffic data
    """
    def __init__(self, zone, core=False):
        self.zone = zone
        self.core = core
        core_str = "_core" if core else ''
        self.dbname = 'guifi_traffic_'+str(zone)+core_str
        self.client = None
        self.database = None
        self.dbdevices = None
        self.dbinfo = None
        self.bulk = None
        self.dateformat = "%y%m%d%H"
        

    def __getDocumentId(self, device_id, date):
        return device_id+':'+date.strftime(self.dateformat)

    def __getTimeSlot(self, date):
        minute = date.minute
        for i in range(0, 60, 5):
            if minute == 0:
                return 0
            if (minute > i) and (minute <= i+5):
                return i/5
            

    def __insertOneDeviceBulk(self, document):
        if not self.bulk:
            self.initializeDevicesBulk()
        self.bulk.insert(document)
    
    def __updateOneDeviceBulk(self, document_id, time_slot,data):
        if not self.bulk:
            self.initializeDevicesBulk()
        time = time_slot*5
        self.bulk.find({'_id':document_id, 'measurements.time':time}).\
                upsert().update_one({'$set':{'measurements.$.data':data}})

    #def updateOneStatsBulk(self, document_id, time_slot):

    def __dic2DicCopyValues(self, dic1, dic2):
        for k,v in dic1.iteritems():
            dic2[k] = v.copy()


    def connect(self):
        self.client = MongoClient('mongodb://localhost:27017/')
        self.database = self.client[self.dbname]
        self.dbdevices = self.database.devices
        self.dbinfo = self.database.info


    def initializeDevicesBulk(self):
        #if self.bulk:
        #    raise BulkAlreadyExistsError(self.dbname, 'traffic')
        #else:
        self.bulk = self.dbdevices.initialize_unordered_bulk_op()


    def storeDeviceBulk(self, device_id, date, results):
        document_id = self.__getDocumentId(device_id, date)
        time_slot = self.__getTimeSlot(date)
        results = results.copy()
        if time_slot == 0 or (not self.dbdevices.find_one({'_id':document_id})):
            new_document = copy.deepcopy(empty_device_document)
            #Set values for new document:
            new_document['_id'] = document_id
            self.__dic2DicCopyValues(results, 
                                new_document['measurements'][time_slot]['data'])
            #new_document['total_measurements'] = 1
            #new_document['total_traffic_in'] = results[4]
            self.__insertOneDeviceBulk(new_document)
        else:
            self.__updateOneDeviceBulk(document_id, time_slot, results)


    def executeDevicesBulk(self):
        if not self.bulk:
            raise NoBulkExistsError(self.dbname)
        #pdb.set_trace()
        try:
            self.bulk.execute()
        except BulkWriteError as bwe:
            pprint(bwe.details) 


    def dropDevicesBulk(self):
        if self.bulk:
           self.bulk = None 


#TODO Think how to update statistics
# Also how to keep the separate info statistics