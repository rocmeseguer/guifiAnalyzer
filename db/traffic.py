"""
This module implements the backend class that communicates with
MongoDB for the database that stores information that assists
"""

from pymongo import MongoClient
from pymongo.errors import BulkWriteError
from pymongo import ASCENDING, DESCENDING
from guifiAnalyzer.db.exceptions import BulkAlreadyExistsError,\
                                            NoBulkExistsError,\
                                            DocumentNotFoundError

import copy
from pprint import pprint

from datetime import datetime#, timedelta
from pytz import timezone
time_zone = 'Europe/Madrid'

#import pdb



empty_data = {'devices':
            {'traffic': 
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
            },
        'links':
            {'deviceA': 
                    {'id': None,
                    'traffic_out':float('nan'), 
                    'traffic_in':float('nan')
                    }, 
            'deviceB': 
                    {'id': None,
                    'traffic_out':float('nan'), 
                    'traffic_in':float('nan')
                    }
            }
        }

empty_document = {'devices':
            {'_id' : None,
                'total_measurements' : 0,
                'total_correct_measurements' : 0,
                'total_traffic_in' : 0,
                'total_traffic_out' : 0,
                'last_traffic_in' : 0,
                'last_traffic_out' : 0,
                'measurements' : [
                            {'time':00, 'measured':False, 'has_data':False,
                                'data':empty_data['devices'].copy()},
                            {'time':05, 'measured':False, 'has_data':False, 
                                'data':empty_data['devices'].copy()},
                            {'time':10, 'measured':False, 'has_data':False, 
                                'data':empty_data['devices'].copy()},
                            {'time':15, 'measured':False, 'has_data':False, 
                                'data':empty_data['devices'].copy()},
                            {'time':20, 'measured':False, 'has_data':False, 
                                'data':empty_data['devices'].copy()},
                            {'time':25, 'measured':False, 'has_data':False, 
                                'data':empty_data['devices'].copy()},
                            {'time':30, 'measured':False, 'has_data':False, 
                                'data':empty_data['devices'].copy()},
                            {'time':35, 'measured':False, 'has_data':False, 
                                'data':empty_data['devices'].copy()},
                            {'time':40, 'measured':False, 'has_data':False, 
                                'data':empty_data['devices'].copy()},
                            {'time':45, 'measured':False, 'has_data':False, 
                                'data':empty_data['devices'].copy()},
                            {'time':50, 'measured':False, 'has_data':False, 
                                'data':empty_data['devices'].copy()},
                            {'time':55, 'measured':False, 'has_data':False, 
                                'data':empty_data['devices'].copy()}
                        ]

            },
        'links':
            {'_id' : None,
                'total_measurements' : 0,
                'total_correct_measurements' : 0,
                'total_traffic_in' : 0,
                'total_traffic_out' : 0,
                'measurements' : [
                            {'time':00, 'measured':False, 'has_data':False,
                                'data':empty_data['links'].copy()},
                            {'time':05, 'measured':False, 'has_data':False, 
                                'data':empty_data['links'].copy()},
                            {'time':10, 'measured':False, 'has_data':False, 
                                'data':empty_data['links'].copy()},
                            {'time':15, 'measured':False, 'has_data':False, 
                                'data':empty_data['links'].copy()},
                            {'time':20, 'measured':False, 'has_data':False, 
                                'data':empty_data['links'].copy()},
                            {'time':25, 'measured':False, 'has_data':False, 
                                'data':empty_data['links'].copy()},
                            {'time':30, 'measured':False, 'has_data':False, 
                                'data':empty_data['links'].copy()},
                            {'time':35, 'measured':False, 'has_data':False, 
                                'data':empty_data['links'].copy()},
                            {'time':40, 'measured':False, 'has_data':False, 
                                'data':empty_data['links'].copy()},
                            {'time':45, 'measured':False, 'has_data':False, 
                                'data':empty_data['links'].copy()},
                            {'time':50, 'measured':False, 'has_data':False, 
                                'data':empty_data['links'].copy()},
                            {'time':55, 'measured':False, 'has_data':False, 
                                'data':empty_data['links'].copy()}
                        ]

            }
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
        self.dblinks = None
        self.dbinfo = None
        self.bulk = {}
        self.dateformat = "%y%m%d%H"
        self.readdateformat = "%Y%m%d%H:%M"

    # DEVICES        

    def __getDocumentId(self, id, date):
        return id+':'+date.strftime(self.dateformat)

    def __getTimeSlot(self, date):
        minute = date.minute
        for i in range(0, 60, 5):
            if minute == 0:
                return 0
            if (minute >= i) and (minute < i+5):
                return i/5
            

    def __insertOneBulk(self, collection, document):
        if not self.bulk:
            self.initializeBulk(collection)

        # How to do the bulk>????

        self.bulk[collection].insert(document)
    
    def __updateOneBulk(self, collection, document_id, time_slot,data, last_document):
        if not self.bulk[collection]:
            self.initializeBulk(collection)
        time = time_slot*5
        if data:
            new_traffic_in = 0
            for i in data['traffic'].values():
                new_traffic_in += int(i['traffic_in'])
            new_traffic_out = 0
            for i in data['traffic'].values():
                new_traffic_out += int(i['traffic_out'])
            total_traffic_in = (new_traffic_in 
                                - int(last_document['last_traffic_in']))
            total_traffic_out = (new_traffic_out 
                                - int(last_document['last_traffic_out']))
            self.bulk[collection].find({'_id':document_id, 
                                        'measurements.time':time}).\
                    upsert().update_one({'$set':{'last_traffic_in':new_traffic_in,
                                            'last_traffic_out':new_traffic_out,
                                            'measurements.$.data':data,
                                            'measurements.$.measured':True,
                                            'measurements.$.has_data':True
                                        },
                                        '$inc':{'total_measurements':1,
                                            'total_correct_measurements':1,
                                            'total_traffic_in':total_traffic_in,
                                            'total_traffic_out':total_traffic_out}
                                        })
        else:
            self.bulk[collection].find({'_id':document_id, 
                                        'measurements.time':time}).\
                    upsert().update_one({'$set':{'measurements.$.measured':True,
                                                'measurements.$.has_data':False},
                                        '$inc':{'total_measurements':1}
                                        })

    #def updateOneStatsBulk(self, document_id, time_slot):

    def __dic2DicCopyValues(self, dic1, dic2):
        for k,v in dic1.iteritems():
            dic2[k] = v.copy()



    def connect(self):
        self.client = MongoClient('mongodb://localhost:27017/')
        self.database = self.client[self.dbname]
        self.dbdevices = self.database.devices
        self.dblinks = self.database.links
        self.dbinfo = self.database.info


    def initializeBulk(self, collection):
        #if self.bulk:
        #    raise BulkAlreadyExistsError(self.dbname, 'traffic')
        #else:
        self.bulk[collection] = self.database[collection].\
                                    initialize_unordered_bulk_op()

    def getMeasurementTotalTraffic(self, data):
        total_traffic_in = 0
        total_traffic_out = 0
        for i in data['traffic'].values():
            total_traffic_in += int(i['traffic_in'])
            total_traffic_out += int(i['traffic_out'])
        return (total_traffic_in, total_traffic_out)


    def getDeviceLastDocument(self, device_id):
        documents = self.dbdevices.find({'_id':{'$regex':'^'+device_id}}).\
                                    sort('_id', DESCENDING)
        if documents.count():
            for doc in documents:
                return doc
        else:
            return None

    def getDeviceDocumentsAscending(self, device_id):
        documents = self.dbdevices.find({'_id':{'$regex':'^'+device_id}}).\
                                    sort('_id', ASCENDING)
        if documents.count():
            return list(documents)
        else:
            return None

    def getDeviceLastMeasurementTime(self, device_id, last_document):
        if last_document:
            document_id = last_document['_id']
            date = document_id.split(':')[1]
            # Traverse measurements table on reverse finding
            # last measurement
            for i in range(11,-1,-1):
                if last_document['measurements'][i]['measured']:
                    minutes = str(i*5) if i > 1 else '0'+str(i*5)
                    date = date+minutes
                    return datetime.strptime(date, "%y%m%d%H%M")
        return None

    def executeBulk(self, collection):
        if not self.bulk[collection]:
            raise NoBulkExistsError(self.dbname)
        #pdb.set_trace()
        try:
            self.bulk[collection].execute()
        except BulkWriteError as bwe:
            pprint(bwe.details) 


    def dropDevicesBulk(self, collection):
        if self.bulk[collection]:
           self.bulk[collection] = None 


    def getDeviceHourDocument(self, device_id, date):
        document_id = self.__getDocumentId(device_id, date)
        document = self.dbdevices.find_one({'_id':document_id})
        if document:
            return document
        else:
            raise DocumentNotFoundError(self.dbname, 'devices', document_id)


    def storeBulk(self, collection, device_id, date, results):
        remote_date = results['availability']['last_sample_date'] if isinstance(results, dict) else ''
        remote_time = results['availability']['last_sample_time'] if isinstance(results, dict) else ''
        if results != False and remote_date != ''  and remote_time != '':
        # Data exists 
            remote_datetime = datetime.strptime(remote_date+remote_time,
                                                 self.readdateformat)
            # Add timezone
            #remote_datetime = timezone(time_zone).localize(remote_datetime)
            # convert to UTC
            #remote_datetime = remote_datetime.astimezone(timezone('UTC'))
            last_document = self.getDeviceLastDocument(device_id)
            last_measured_datetime = self.getDeviceLastMeasurementTime(device_id, last_document)
            if ((not last_measured_datetime) or 
                    remote_datetime > last_measured_datetime):
            # Data has the correct expected time
                document_id = self.__getDocumentId(device_id, remote_datetime)
                time_slot = self.__getTimeSlot(remote_datetime)
                results = results.copy()
                if (time_slot == 0 or (not last_measured_datetime) or 
                    remote_datetime.strftime('%y%m%H') != last_measured_datetime.strftime('%y%m%H')):
                # New document
                    new_document = copy.deepcopy(empty_document[collection])
                    #Set values for new document:
                    new_document['_id'] = document_id
                    #Set initial counters for new document
                    new_document['total_measurements'] = 1
                    new_document['measurements'][time_slot]['measured'] = True
                    
                    last_total_traffic_in = last_document['total_traffic_in'] if last_document else 0
                    last_total_traffic_out = last_document['total_traffic_out'] if last_document else 0
                    new_total_traffic_in, new_total_traffic_out =\
                                        self.getMeasurementTotalTraffic(results)
                    new_document['total_traffic_in'] = (new_total_traffic_in - 
                                                        last_total_traffic_in)
                    new_document['total_traffic_out'] = (new_total_traffic_out - 
                                                        last_total_traffic_out)
                    new_document['last_traffic_in'] = new_total_traffic_in
                    new_document['last_traffic_out'] = new_total_traffic_out
                    new_document['total_correct_measurements'] = 1
                    new_document['measurements'][time_slot]['has_data'] = True
                    self.__dic2DicCopyValues(results, 
                                new_document['measurements'][time_slot]['data'])
                    self.__insertOneBulk(collection, new_document)
                    return True
                else:
                    self.__updateOneBulk(collection, document_id, time_slot, results, last_document)
                    return True
        return False

    # LINKS

#TODO Think how to update statistics
# Also how to keep the separate info statistics