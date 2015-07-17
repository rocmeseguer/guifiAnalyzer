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

import collections

#prepare regular expresion
#r = re.compile('http:\/\/([^\/]*).*')

#root = 8346 #Lucanes
#root = 2444 #Osona
#root = 18668 #Castello
#g = CNMLWrapper(root)
#Get connection object form guifiwrapper
#conn = g.conn

#misDevices = []
#wtfDevices = []


def loadDB(root):
    db = os.path.join(os.getcwd(),'guifiAnalyzerOut','traffic',str(root),'data.sqld')
    linksTable = SqliteDict(
        filename=db,
        tablename='links',
        # create new db file if not exists and rewrite if exists
        flag='c',
        autocommit=False)
    devicesTable= SqliteDict(
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
    return linksTable,devicesTable, graphServersTable


def getAllDevicesGraphData(url):
    try:
        data = snpRequest(
            url,
            command="stats",
            args={},
            debug=False,
            timeout=0,
                     csv=True)
        #return data,0
        return data
    except urllib2.HTTPError as e:
        #logger.error('Server not configured correctly')
        #logger.error("Error code: %s" % str(e.code))
        #return None,1
        msg = "Server not configured correctly, " + "HTTPError: " + str(e.code)
        raise EnvironmentError(msg)
    except urllib2.URLError as e:
        #logger.error('Failed to reach server')
        #logger.error(e.reason)
        #return None,1
        msg = "Failed to reach server, " + "URLError: "  + e.reason
        raise EnvironmentError(msg)
    except socket.timeout:
       #logger.error('Server could not be reached')
       #return None,1
       msg = "Server could not be reached, " + "Socket Timeout"
       raise EnvironmentError(msg)


def getDevicesGraphData(url, devices):
    try:
        data = snpRequest(
	        url,
	        command="stats",
	        args={
	            "devices": devices},
	        debug=False,
	        timeout=0,
                     csv = True)
        #return data,0
        return data
    except urllib2.HTTPError as e:
        logger.error("HTTPError")
        logger.error("Error code: %s" % str(e.code))
        if e.code == 414:
            logger.warning("URL too big. Have to retrieve all the data")
            return getAllDevicesGraphData(url)
        else:
           #logger.warning("Server misconfigured")
           #return None,1
           msg = "Server not configured correctly, " + "HTTPError: " + str(e.code)
           raise EnvironmentError(msg)
    except urllib2.URLError as e:
        #logger.error('Failed to reach server')
        #logger.error(e.reason)
        #return None,1
        msg = "Failed to reach server, " + "URLError: " + e.reason
        raise EnvironmentError(msg)
    except socket.timeout:
        #logger.error('Server could not be reached')
        #return None,1
        msg = "Server could not be reached, " + "Socket Timeout"
        raise EnvironmentError(msg)

def processDevicesGraphData(result, devicesTable):
    data = csv.reader(result,delimiter='|')
    rows = 0
    for row in data:
        rows += 1
        if len(row) == 2:
            #No Data for this node
            deviceId = row[0]
            if deviceId in devicesTable:
                logger.error("No data")
                temp = devicesTable[deviceId]
                temp['data'] = False
                devicesTable[deviceId] = temp
        elif len(row) == 3:
            # check from here:
            # https://github.com/guifi/snpservices/blob/master/services/stats.php
            deviceId = row[0]
            availability = row[1].split(',')
            traffic = row[2].split(',')
            if deviceId in devicesTable:
                #print devicesTable[deviceId]
                temp = devicesTable[deviceId]
                temp['data']={}
                temp['data']['availability'] = {}
                temp['data']['availability']['max_latency'] = availability[0]
                temp['data']['availability']['avg_latency'] = availability[1]
                temp['data']['availability']['succeed'] = availability[2]
                temp['data']['availability']['last_online'] = availability[3]
                temp['data']['availability']['last_sample_date'] = availability[4]
                temp['data']['availability']['last_sample'] = availability[5]
                temp['data']['availability']['last_succeed'] = availability[6]
                temp['data']['traffic'] = {}
                temp['data']['traffic']['snmp_key'] = traffic[0]
                temp['data']['traffic']['traffic_in'] = traffic[1]
                temp['data']['traffic']['traffic_out'] = traffic[2]
                devicesTable[deviceId] = temp
                #print devicesTable[deviceId]
        else:
            logger.error("Server Data Incorrect")
            deviceId = row[0]
            if deviceId in devicesTable:
                temp = devicesTable[deviceId]
                temp['data'] = 'Incorrect'
                devicesTable[deviceId] = temp
    devicesTable.commit()
    return rows


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


def graphDevicesInfo(root):
    linksTable,devicesTable, graphServersTable = loadDB(root)
    for g, data in graphServersTable.iteritems():
    	# If there is a working IP
        if data['ip']:
            logger.info("GraphServer: %s" % str(g))
            # result, error = getDevicesGraphData(data['ip'],data['devices'])
            # if not error:
            #     data['Working'] = True
            #     graphServersTable[g] = data
            #     graphServersTable.commit()
            #     processDevicesGraphData(result, devicesTable)
            # else:
            #     data['Working'] = False
            #     graphServersTable[g] = data
            #     graphServersTable.commit()
            #     continue
            try :
                logger.info("\tTotal Devices %s" % len(data['devices']))
                toBeGraphed = [d1 for d1,d2 in devicesTable.iteritems() if str(d2['graphServer']) == g]
                logger.info("\tGraphed Devices %s" % len(toBeGraphed))
                result = getDevicesGraphData(data['ip'],toBeGraphed)
                data['Working'] = True
                rows = processDevicesGraphData(result, devicesTable)
                data['Rows'] = rows
                graphServersTable[g] = data
                graphServersTable.commit()
            except EnvironmentError as e:
                data['Working'] = False
                data['Error'] = str(e)
                graphServersTable[g] = data
                graphServersTable.commit()
                continue
        else:
            logger.info("GrahpServer: %s" % str(g))
            logger.info("No working ip")

    for d, data in devicesTable.iteritems():
        print("%s : %s" % (str(d),data))

    noDataDevices = {d:data for d,data in devicesTable.iteritems() if 'data' in data and data['data']==False }
    wrongDataDevices = {d:data for d,data in devicesTable.iteritems() if 'data' in data and data['data']=='Incorrect' }
    correctDataDevices = {d:data for d,data in devicesTable.iteritems() if 'data' in data and isinstance(data['data'],dict)}
    shouldWorkGraphServers = {g:data for g,data in graphServersTable.iteritems() if 'ip' in data and data['ip']}
    noGraphServer = {g:data for g,data in graphServersTable.iteritems() if 'Working' in data and data['Working']==False}
    totalWorkingGraphServers = {g:data for g,data in graphServersTable.iteritems() if 'Working' in data and data['Working']==True }
    graphedDevices = {d:data for d,data in devicesTable.iteritems() if str(data['graphServer']) in totalWorkingGraphServers}
    wtfDataDevices = {d:data for d,data in devicesTable.iteritems() if 'data' not in data and str(data['graphServer']) in totalWorkingGraphServers }


    logger.info("Servers should work %s : %s" % (len(shouldWorkGraphServers),[s for s in shouldWorkGraphServers]))
    logger.info("Servers working %s : %s" % (len(totalWorkingGraphServers),[s for s in totalWorkingGraphServers]))
    logger.info("Servers not working %s : %s" % (len(noGraphServer),{(s,data['Error']) for s,data in noGraphServer.iteritems()}))
    logger.info("Total Devices: %s" % len(devicesTable))
    logger.info("Total Should Be Graphed Devices: %s" % len(graphedDevices))
    logger.info("No data devices: %s" % len(noDataDevices))
    logger.info("Wrong data devices: %s" % len(wrongDataDevices))
    logger.info("wtf devices: %s" % len(wtfDataDevices)) #Should have some of the above types of data
    logger.info("Correct data devices: %s" % len(correctDataDevices))

    linksTable.close()
    devicesTable.close()
    graphServersTable.close()


def testResult(root):
    linksTable,devicesTable, graphServersTable = loadDB(root)
    noDataDevices = {d:data for d,data in devicesTable.iteritems() if 'data' in data and data['data']==False }
    wrongDataDevices = {d:data for d,data in devicesTable.iteritems() if 'data' in data and data['data']=='Incorrect' }
    correctDataDevices = {d:data for d,data in devicesTable.iteritems() if 'data' in data and isinstance(data['data'],dict)}
    shouldWorkGraphServers = {g:data for g,data in graphServersTable.iteritems() if 'ip' in data and data['ip']}
    noGraphServer = {g:data for g,data in graphServersTable.iteritems() if 'Working' in data and data['Working']==False}
    totalWorkingGraphServers = {g:data for g,data in graphServersTable.iteritems() if 'Working' in data and data['Working']==True }
    wtfDataDevices = {d:data for d,data in devicesTable.iteritems() if 'data' not in data and str(data['graphServer']) in totalWorkingGraphServers }
    graphedDevices = {d:data for d,data in devicesTable.iteritems() if str(data['graphServer']) in totalWorkingGraphServers}

    for g,gdata in graphServersTable.iteritems():
        if gdata['ip']:
            logger.info("Server %s working with ip/url: %s" % (g,gdata['ip']))
            noDataDevices1 = {dev:devd for dev,devd in noDataDevices.iteritems() if int(dev) in gdata['devices']}
            wrongDataDevices1 = {dev:devd for dev,devd in wrongDataDevices.iteritems() if int(dev) in gdata['devices']}
            wtfDataDevices1 = {dev:devd for dev,devd in wtfDataDevices.iteritems() if int(dev) in gdata['devices']}
            correctDataDevices1 = {dev:devd for dev,devd in correctDataDevices.iteritems() if int(dev) in gdata['devices']}
            graphedDevices1 = {dev:devd for dev,devd in graphedDevices.iteritems() if int(dev) in gdata['devices']}
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
    logger.info("Total Devices: %s" % len(devicesTable))
    logger.info("Total Should Be Graphed Devices: %s" % len(graphedDevices))
    logger.info("No data devices: %s" % len(noDataDevices))
    logger.info("Wrong data devices: %s" % len(wrongDataDevices))
    logger.info("wtf devices: %s" % len(wtfDataDevices)) #Should have some of the above types of data
    logger.info("Correct data devices: %s" % len(correctDataDevices))
    correctDataServers = [g['graphServer'] for  g in correctDataDevices.values()]
    wtfDataServers = [g['graphServer'] for  g in wtfDataDevices.values()]
    print collections.Counter(correctDataServers)
    print collections.Counter(wtfDataServers)


    linksTable.close()
    devicesTable.close()
    graphServersTable.close()


if __name__ == "__main__":
    if len(sys.argv) > 2:
        if sys.argv[1] == '1':
            graphDevicesInfo(sys.argv[2])
        elif sys.argv[1] =='2':
            testResult(sys.argv[2])

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
# 2) what does the index means in the snpservices stats service that causes multiple
#     results of traffic?
# 3)  separate core and see