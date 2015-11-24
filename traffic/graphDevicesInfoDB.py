"""
Performs a one time collection of traffic data from all the devices of
the accessible graphServers in a guifi.net zone.
"""
import os
import sys

from ..guifiwrapper.guifiwrapper import *
from ..guifiwrapper.cnmlUtils import *
from snpservicesClient import *

from ..db.traffic_assistant import TrafficAssistantDB
from ..db.traffic import TrafficDB
from ..db.exceptions import DocumentNotFoundError

import urllib2
import socket
import csv
from netaddr import IPNetwork, IPAddress

from collections import Counter


from ..lib.pyGuifiAPI import *
from ..lib.pyGuifiAPI.error import GuifiApiError
import urllib
import re

from exceptionsDB import *

import collections

import pdb

from datetime import datetime as dt

def getAllDevicesGraphData(url):
    """Performs a single snpRequest that will download all the traffic data
    of the devices that correspond to the graphServer in question.
    """
    try:
        data = snpRequest(
            url,
            command="stats",
            args={},
            debug=False,
            timeout=0,
                     csv=True)
        return data
    except urllib2.HTTPError as e:
        msg = "Server not configured correctly, " + "HTTPError: " + str(e.code)
        raise EnvironmentError(msg)
    except urllib2.URLError as e:
        msg = "Failed to reach server, " + "URLError: "  + e.reason
        raise EnvironmentError(msg)
    except socket.timeout:
       msg = "Server could not be reached, " + "Socket Timeout"
       raise EnvironmentError(msg)


def getDevicesGraphData(url, devices):
    """Performs one or more snpRequests that will download the traffic data
    of the devices are included in the devices list.
    """
    try:
        data = snpRequest(
	        url,
	        command="stats",
	        args={
	            "devices": devices},
	        debug=False,
	        timeout=0,
                     csv = True)
        return data
    except urllib2.HTTPError as e:
        logger.error("HTTPError")
        logger.error("Error code: %s" % str(e.code))
        logger.error(e)
        if e.code == 414:
            logger.warning("URL too big. Have to retrieve all the data")
            # Ids size from 4-6 and one more for the comment
            urlSize = 43 + len(devices)*6
            # Max no problem size in characters found on web 4000
            urlMax = 4000

            return getAllDevicesGraphData(url)
        else:
           msg = "Server not configured correctly, " + "HTTPError: " + str(e.code)
           raise EnvironmentError(msg)
    except urllib2.URLError as e:
        msg = "Failed to reach server, " + "URLError: " + str(e.reason)
        raise EnvironmentError(msg)
    except socket.timeout:
        msg = "Server could not be reached, " + "Socket Timeout"
        raise EnvironmentError(msg)


def processDevicesGraphData(result, devices, links, trafficAssDB, trafficdb, date):
    """Parses and stores the result of an snpRequest.
    """
    data = csv.reader(result, delimiter='|')
    rows = 0
    correct_data = False
    trafficdb.initializeBulk('devices')
    #trafficdb.initializeBulk('links')
    for row in data:
        rows += 1
        if len(row) == 2:
            #No Data for this node
            deviceId = row[0]
            if deviceId in devices:
                #logger.error("No data")
                temp = devices[deviceId]
                temp['data'] = False
                devices[deviceId] = temp
                trafficdb.storeBulk('devices',deviceId, date, False)
        elif len(row) >= 3:
            # 3 is a normal device that has traffic info for only 1 iface
            # More than 3 are supernodes
            # check from here:
            # https://github.com/guifi/snpservices/blob/master/services/stats.php
            deviceId = row[0]
            availability = row[1].split(',')
            traffic = {}
            for i in range(2,len(row)):
                traffic[i-2] = row[i].split(',')
            if deviceId in devices:
                #linkId = devices['deviceId']['link']
                #link = links[linkId]
                #devicePosition = 'deviceA' if deviceId == link['deviceA'] else 'deviceB'
                #correct_data = True
                temp = devices[deviceId]
                temp['data']={}
                temp['data']['availability'] = {}
                temp['data']['availability']['max_latency'] = availability[0]
                temp['data']['availability']['avg_latency'] = availability[1]
                temp['data']['availability']['availability'] = availability[2]
                temp['data']['availability']['last_online'] = availability[3]
                temp['data']['availability']['last_sample_date'] = availability[4]
                temp['data']['availability']['last_sample_time'] = availability[5]
                temp['data']['availability']['last_availability'] = availability[6]
                temp['data']['traffic'] = {}
                for data in traffic.values():
                    # snmp_key is used for indexing
                    temp['data']['traffic'][data[0]] = {}
                    temp['data']['traffic'][data[0]]['traffic_in'] = data[1]
                    temp['data']['traffic'][data[0]]['traffic_out'] = data[2]
                devices[deviceId] = temp
                try: 
                    trafficAssDB.updateDocument('devices',deviceId,'data','Correct')
                    bulk = trafficdb.storeBulk('devices',deviceId, date, temp['data'])
                    #trafficdb.storeBulk('links',deviceId, date, temp['data'])
                    correct_data = (correct_data or bulk)
                except DocumentNotFoundError as e:
                    msg= "processDevicesGraphData: "+e
                    raise EnvironmentError(msg)
        else:
            #logger.error("Server Data Incorrect")
            deviceId = row[0]
            if deviceId in devices:
                try:
                    trafficAssDB.updateDocument('devices',deviceId,'data','Incorrect')
                    trafficdb.storeBulk('devices',deviceId, date, False)
                except DocumentNotFoundError as e:
                    msg= "processDevicesGraphData: "+e
                    raise EnvironmentError(msg)
    if correct_data:
        trafficdb.executeBulk('devices')
        #trafficdb.executeBulk('links')
    trafficdb.dropDevicesBulk('devices')
    #trafficdb.dropDevicesBulk('links')
    return rows



def graphDevicesInfo(root,core, date=None):
    """Performs one traffic measurement round for the devices inlcuded in the 
    trafficAssistantDB. 
    """
    if not date:
        date = dt.now()
    logger.info("START:%s" % dt.now().strftime(' %H:%M.%S | %d/%m/%y'))
    logger.info("/////////////////")
    logger.info("Starting measurement for Zone: %s" % str(root))

    trafficAssDB = TrafficAssistantDB(root,core)
    trafficAssDB.connect()
    trafficdb = TrafficDB(root,core)
    trafficdb.connect()
    graphServers = trafficAssDB.getCollection('graphServers')
    devices = trafficAssDB.getCollection('devices')
    links = trafficAssDB.getCollection('links')
    for data in graphServers:
        # If there is a working IP
        if data['ip']:
            logger.info("GraphServer: %s" % str(data['_id']))
            try :
                logger.info("\tTotal Devices %s" % len(data['devices']))
                toBeGraphed = [d['_id'] for d in devices if str(d['graphServer']) == data['_id']]               
                logger.info("\tGraphed Devices %s" % len(toBeGraphed))
                result = getDevicesGraphData(data['ip'],toBeGraphed)
                devicesDict = {data['_id']:data for data in devices}
                linksDict = {data['_id']:data for data in links}
                rows = processDevicesGraphData(result, devicesDict, linksDict, trafficAssDB, trafficdb, date)
                trafficAssDB.updateDocument('graphServers', data['_id'], 'Working', True)
                trafficAssDB.updateDocument('graphServers', data['_id'], 'Rows', rows)
            except EnvironmentError as e:
                trafficAssDB.updateDocument('graphServers', data['_id'], 'Working', False)
                trafficAssDB.updateDocument('graphServers', data['_id'], 'Error', str(e))
                continue
        else:
            logger.info("GrahpServer: %s" % str(data['_id']))
            logger.info("No working ip")


    #for data in devices:
    #    d = data['_id']
    #    print("%s : %s" % (str(d),data))

    graphServers = trafficAssDB.getCollection('graphServers')
    devices = trafficAssDB.getCollection('devices')
    links = trafficAssDB.getCollection('links')

    noDataDevices = {data['_id']:data for data in devices if 'data' in data and data['data']==False }
    wrongDataDevices = {data['_id']:data for data in devices if 'data' in data and data['data']=='Incorrect' }
    correctDataDevices = {data['_id']:data for data in devices if 'data' in data and data['data']=='Correct'}
    shouldWorkGraphServers = {data['_id']:data for data in graphServers if 'ip' in data and data['ip']}
    noGraphServer = {data['_id']:data for data in graphServers if 'Working' in data and data['Working']==False}
    totalWorkingGraphServers = {data['_id']:data for data in graphServers if 'Working' in data and data['Working']==True }
    graphedDevices = {data['_id']:data for data in devices if str(data['graphServer']) in totalWorkingGraphServers}
    wtfDataDevices = {data['_id']:data for data in devices if 'data' not in data and str(data['graphServer']) in totalWorkingGraphServers }


    logger.info("Servers should work %s : %s" % (len(shouldWorkGraphServers),[s for s in shouldWorkGraphServers]))
    logger.info("Servers working %s : %s" % (len(totalWorkingGraphServers),[s for s in totalWorkingGraphServers]))
    #pdb.set_trace()
    logger.info("Servers not working %s : %s" % (len(noGraphServer),{(s,data['Error']) for s,data in noGraphServer.iteritems()}))
    logger.info("Total Devices: %s" % len(devices))
    logger.info("Total Should Be Graphed Devices: %s" % len(graphedDevices))
    logger.info("No data devices: %s" % len(noDataDevices))
    logger.info("Wrong data devices: %s" % len(wrongDataDevices))
    logger.info("wtf devices: %s" % len(wtfDataDevices)) #Should have some of the above types of data
    logger.info("Correct data devices: %s" % len(correctDataDevices))

    logger.info("Finished measurement for Zone: %s" % str(root))
    logger.info("/////////////////")
    logger.info("STOP:%s" % dt.now().strftime(' %H:%M.%S | %d/%m/%y'))

#TODO Correct showDevicesInfo
#Store traffic in separate db

def showDevicesInfo(root, core):
    """Shows statistics for the current traffic measurement round for the devices inlcuded in the 
    trafficAssistantDB. 
    """
    trafficAssDB = TrafficAssistantDB(root,core)
    trafficAssDB.connect()
    graphServers = trafficAssDB.getCollection('graphServers')
    devices = trafficAssDB.getCollection('devices')
    links = trafficAssDB.getCollection('links')
    noDataDevices = {data['_id']:data for data in devices if 'data' in data and data['data']==False }
    wrongDataDevices = {data['_id']:data for data in devices if 'data' in data and data['data']=='Incorrect' }
    correctDataDevices = {data['_id']:data for data in devices if 'data' in data and data['data']=='Correct'}
    shouldWorkGraphServers = {data['_id']:data for data in graphServers if 'ip' in data and data['ip']}
    noGraphServer = {data['_id']:data for data in graphServers if 'Working' in data and data['Working']==False}
    totalWorkingGraphServers = {data['_id']:data for data in graphServers if 'Working' in data and data['Working']==True }
    wtfDataDevices = {data['_id']:data for data in devices if 'data' not in data and str(data['graphServer']) in totalWorkingGraphServers }
    graphedDevices = {data['_id']:data for data in devices if str(data['graphServer']) in totalWorkingGraphServers}

    for gdata in graphServers:
        g = gdata['_id']
        if gdata['ip']:
            logger.info("Server %s working with ip/url: %s" % (g,gdata['ip']))
            noDataDevices1 = {dev:devd for dev,devd in noDataDevices.iteritems() if str(devd) in gdata['devices']}
            wrongDataDevices1 = {dev:devd for dev,devd in wrongDataDevices.iteritems() if str(dev) in gdata['devices']}
            wtfDataDevices1 = {dev:devd for dev,devd in wtfDataDevices.iteritems() if str(dev) in gdata['devices']}
            correctDataDevices1 = {dev:devd for dev,devd in correctDataDevices.iteritems() if str(dev) in gdata['devices']}
            graphedDevices1 = {dev:devd for dev,devd in graphedDevices.iteritems() if str(dev) in gdata['devices']}
            logger.info("\tTotal Devices of server: %s" % len(gdata['devices']))
            logger.info("\tShould be graphed devices: %s" % len(graphedDevices1) )
            logger.info("\tNo data devices: %s" % len(noDataDevices1))
            logger.info("\tWrong data devices: %s" % len(wrongDataDevices1))
            logger.info("\twtf devices: %s" % len(wtfDataDevices1)) #Should have some of the above types of data
            logger.info("\tCorrect data devices: %s" % len(correctDataDevices1))
            logger.info("\t Rows read : %s " % (str(gdata['Rows'] if gdata['Working'] else '0')))

    logger.info("----- TOTAL ----")
    logger.info("Servers should work %s : %s" % (len(shouldWorkGraphServers),[s for s in shouldWorkGraphServers]))
    logger.info("Servers working %s : %s" % (len(totalWorkingGraphServers),[s for s in totalWorkingGraphServers]))
    logger.info("Servers not working %s : %s" % (len(noGraphServer),{(s,data['Error']) for s,data in noGraphServer.iteritems()}))
    logger.info("Total Devices: %s" % len(devices))
    logger.info("Total Should Be Graphed Devices: %s" % len(graphedDevices))
    logger.info("No data devices: %s" % len(noDataDevices))
    logger.info("Wrong data devices: %s" % len(wrongDataDevices))
    logger.info("wtf devices: %s" % len(wtfDataDevices)) #Should have some of the above types of data
    logger.info("Correct data devices: %s" % len(correctDataDevices))
    correctDataServers = [g['graphServer'] for  g in correctDataDevices.values()]
    wtfDataServers = [g['graphServer'] for  g in wtfDataDevices.values()]
    print collections.Counter(correctDataServers)
    print collections.Counter(wtfDataServers)


if __name__ == "__main__":
    if len(sys.argv) == 3:
        if sys.argv[1] == '1':
            graphDevicesInfo(sys.argv[2], False)
        elif sys.argv[1] =='2':
            showDevicesInfo(sys.argv[2], False)
    elif len(sys.argv) == 4:
        if sys.argv[1] == '1':
            graphDevicesInfo(sys.argv[2], True if  sys.argv[3] == "core" else False)
        elif sys.argv[1] =='2':
            showDevicesInfo(sys.argv[2], True if  sys.argv[3] == "core" else False)


# Two open questions
# 1) why servers return everytime a different amount of entries? and why the fuck it
#     does not return all of them? for example
        # Server 6833 working with ip/url: 10.138.2
        #     Total Devices of server: 4719
        #     Should be graphed devices: 4719
        #     No data devices: 0
        #     Wrong data devices: 55
        #     wtf devices: 4055
        #     Correct data devices: 609
        #      Rows read : 816
# Reply(Possible):  Cause graphserver returns values only from the nodes that it has ping
# value the last 12 hours? Nope. because of 30 seconds php call limit
# Solution: Instead of asking all stats break requests in smaller parallel requests and combine that
# with the maximum possible chars
# 2) what does the index means in the snpservices stats service that causes multiple
#     results of traffic?
# Reply: Different interface
# 3) Test what are the differences of my devices and the supernode argument
