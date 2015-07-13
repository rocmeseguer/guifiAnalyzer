#graphDevicesInfo.py
import os
import sys

# For storing dicts in sqlite3
from ..lib.sqlitedict.sqlitedict import SqliteDict

from ..guifiwrapper.guifiwrapper import *
from ..guifiwrapper.cnmlUtils import *
from snpservicesClient import *

import urllib2
import socket
import csv
from netaddr import IPNetwork, IPAddress

from collections import Counter


from ..lib.pyGuifiAPI import *
from ..lib.pyGuifiAPI.error import GuifiApiError
import urllib
import re

from exceptions import *

#prepare regular expresion
r = re.compile('http:\/\/([^\/]*).*')

#root = 8346 #Lucanes
root = 2444 #Osona
#root = 18668 #Castello
#g = CNMLWrapper(root)
#Get connection object form guifiwrapper
#conn = g.conn

misDevices = []
wtfDevices = []


db = os.path.join(os.getcwd(),'guifiAnalyzerOut','traffic',str(root),'data.sqld')
linksTable = SqliteDict(
    filename=db,
    tablename='links',
    # create new db file if not exists and rewrite if exists
    flag='c',
    autocommit=False)
devicesTable = SqliteDict(
    filename=db,
    tablename='devices',
    # r/w table
    flag='c',
    autocommit=False)
graphServersTable = SqliteDict(
    filename=db,
    tablename='graphServers',
    # r/w table
    flag='c',
    autocommit=False)


def getAllDevicesGraphData(url):
	try:
	    data = snpRequest(
	        url,
	        command="stats",
	        args={},
	        debug=False,
	        timeout=0)
	    return data
	except urllib2.HTTPError as e:
		logger.error('Server not configured correctly')
		logger.error("Error code: %s" % str(e.code))
	except urllib2.URLError as e:
		logger.error('Failed to reach server')
		logger.error(e.reason),
	except socket.timeout:
		logger.error('Server could not be reached')


def getDevicesGraphData(url, devices):
    try:
        data = snpRequest(
	        url,
	        command="stats",
	        args={
	            "devices": devices},
	        debug=False,
	        timeout=0)
        return data
    except urllib2.HTTPError as e:
        logger.error("HTTPError")
        logger.error("Error code: %s" % str(e.code))
        if e.code == 414:
            logger.warning("URL too big. Have to retrieve all the data")
            return getAllDevicesGraphData(url)
        else:
            raise EnvironmentError("Server misconfigured")
	except urllib2.URLError as e:
		logger.error('Failed to reach server')
		logger.error(e.reason),
	except socket.timeout:
		logger.error('Server could not be reached')

def processDevicesGraphData(data):
    data = csv.reader(data,delimiter="|")
    for row in data:
        if len(row) == 2:
            #No Data for this node
            deviceId = row[0]
        elif len(row) == 3:
            # check from here:
    		# https://github.com/guifi/snpservices/blob/master/services/stats.php
            deviceId = row[0]
            availability = row[1].strip(',')
            traffic = row[2].strip(',')
            if deviceId in devicesTable:
                devicesTable[deviceId]['data']={}
                devicesTable[deviceId]['data']['availability'] = {}
            	devicesTable[deviceId]['data']['availability']['max_latency'] = availability[0]
            	devicesTable[deviceId]['data']['availability']['avg_latency'] = availability[1]
            	devicesTable[deviceId]['data']['availability']['succeed'] = availability[2]
            	devicesTable[deviceId]['data']['availability']['last_online'] = availability[3]
            	devicesTable[deviceId]['data']['availability']['last_sample_date'] = availability[4]
            	devicesTable[deviceId]['data']['availability']['last_sample'] = availability[5]
            	devicesTable[deviceId]['data']['availability']['last_succeed'] = availability[6]
            	devicesTable[deviceId]['data']['traffic']['snmp_key'] = traffic[0]
            	devicesTable[deviceId]['data']['traffic']['traffic_in'] = traffic[1]
            	devicesTable[deviceId]['data']['traffic']['traffic_out'] = traffic[2]
            else:
                pass
        else:
            logger.error("Server Data Incorrect")
    devicesTable.commit()



    #return data
    # if data == str(device.id)+"|0,0,0.00,0,,,0":
    #     #Check if server is responsible for the nodes
    #     devices = graphServerDevices(graphService)
    #     if device.id in devices:
    #         # If yes, then it means that the node locally is misconfigured
    #         logger.error("Misconfigured device %s" % (device.id))
    #         misDevices.append(device)
    #     else:
    #         logger.error("VAYA PUTA MIERDA device %s" % (device.id))
    #         wtfDevices.append(device)
    #     return None
    # return


for g, data in graphServersTable.iteritems():
	# If there is a working IP
    if data['ip']:
        logger.info("GrahpServer: %s" % str(g))
        try:
            result = getDevicesGraphData(data["ip"],data['devices'])
            processDevicesGraphData(result)
        except EnvironmentError as e:
            logger.error(e)
            continue
    else:
        logger.info("GrahpServer: %s" % str(g))
        logger.info("No working ip")

for d, data in devicesTable.iteritems():
    print("%s : %s" % (str(d),data))

