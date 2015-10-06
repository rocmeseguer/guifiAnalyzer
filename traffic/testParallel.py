#!/usr/bin/env python
#
# snpservicesClient.py

import urllib2
import sys
import socket

from exceptions import *


commands = ["help", "version", "phpinfo", "serverinfo"]
services = [
    "availability",
    "example",
    "graph",
    "liveping",
    "livetraceroute",
    "stats"]




def buildArgs(args):
    """
    Take a dictionary of arguments and values and convert it to a url
    string
    """
    arguments = ""
    for arg in args:
        arguments += "&" + str(arg)
        if args[arg]:
            arguments += "="
            for i in args[arg]:
                if i == args[arg][-1]:
                    #print i
                    arguments += str(i)
                else:
                    # print i
                    arguments += str(i) + ","
    return arguments

def doRequest(base, arguments, timeout):
    # Make request
    url = base + arguments
    print len(arguments)
    #print("SNPServices request to graph server: %s" % url)
    req = urllib2.Request(url)
    if timeout:
        return urllib2.urlopen(req, timeout=timeout)
    else:
        return urllib2.urlopen(req)




def doParallelStatsRequests(base, args, tout, csv):
    # Define utilites for parallel request
    from urlparse import urlparse
    from threading import Thread
    import httplib, sys
    from Queue import Queue

    timeout = tout

    def buildUrl(base, devices):
        url = base
        for i in devices:
            if i == devices[-1]:
                #print i
                url += str(i)
            else:
                # print i
                url += str(i) + ","
        return url

    def chunks(l, n):
        """
        Yield successive n-sized chunks from l.
        """
        for i in xrange(0, len(l), n):
            yield l[i:i+n]

    def worker():
        while True:
            # Parallel stuff start under this command
            url = q.get()
            print "%s\n" % url
            req = urllib2.Request(url)
            req_params = {}
            if timeout:
                req_params['timeout'] = timeout
            while True:
                try:
                    response = urllib2.urlopen(req, **req_params)
                    print "Done", q.qsize()
                except (urllib2.HTTPError, urllib2.URLError, socket.timeout) as e:
                    print e
                else:
                    break
            responses.extend(response)
            q.task_done()
            # Parallel stuff end above this command


    # Since we know we are performing a stats command with many
    # arguments we can expand the base url
    base = base+"&devices="
    #Extract list of devices:
    devices = args['devices']

    # Separate arguments in lists that fit the apache max url size (4000 chars)
    # Each arg has a max of 5 chars + the comma after it
    #WRONG chunksize = (len(devices)*6) / (4000-len(base))
    print "total devices"
    print len(devices)
    chunksize = (100-len(base))/6
    print "chunksize (# of devices)"
    print chunksize
    devicesLists  = list(chunks(devices, chunksize))
    print "devicesLists"
    print len(devicesLists)
    urls = [buildUrl(base,devicesList) for devicesList in devicesLists]
    #print "Urls"
    urlsLen = [len(url) for url in urls]
    print urlsLen
    #Do parallel request for each url innlist
    concurrent = len(urls)
    q = Queue(concurrent)
    responses = []

    for i in range(20):
        t = Thread(target=worker)
        t.daemon = True
        t.start()
    try:
        for url in urls:
            q.put(url.strip())
        q.join()
    except KeyboardInterrupt:
        sys.exit(1)


    with open('test.txt','a') as outfile:
        for response in responses:
            outfile.write(response)
            #reader = response.reader()
            #for row in reader:
            #    outfile.write(row)


    # Queue problem????

    #if csv:
        # TODO
        #Merge all responses in one csv... How?????
    #    return response
    #else:
    #    readResponses = [r.read() for r in responses]
    #    return readResponses


def snpRequest(ip, command="help", args={}, debug=False, timeout=0, csv = False):
    """
    Request to snpservices server

    args: dictionary {"arg1":[val1],"arg2":[val2,val3]}

    Throws URLError exception
    """
    if command not in commands and command not in services:
        print("Wrong request arguments")
        return -1
    else:

        base = "http://" + str(ip) + "/snpservices/index.php?call=" + command
        # Build arguments
        arguments = buildArgs(args)
        #print "Total Args"
        #print len(arguments)


        # New code
        # Url character Limit
        # http://stackoverflow.com/a/1289610
        if len(arguments) < 4000:
            print "Normal request"
            response = doRequest(base, arguments, timeout)
        else:
            # Only stats command can have multiple argument values (for devices)
            # index.php?call=stats&devices=<device_id>[,<device_id>]
            print "Parallel Request"
            response = doParallelStatsRequests(base, args, timeout, csv)

        #if csv:
        #    return response
        #else:
        #    data = response.read()
        #    return data

#/snpservices/index.php?call=stats&devices=

def snpGetDevices(ip, devices):
    url = "http://" + str(ip) + "/snpservices/index.php?call=stats"
    req = urllib2.Request(url)
    response = urllib2.urlopen(req)
    #with open('test.txt','a') as outfile:
    #    outfile.write(response)




#TEST
#from guifiAnalyzer.traffic import testParallel as par
#from guifiAnalyzer.traffic import graphDevicesInfo as gd
#gd.graphDevicesInfo(18668,False)
#linksTable,devicesTable, graphServersTable = gd.loadDB(18668, False)
#toBeGraphed = [int(d1) for d1,d2 in devicesTable.iteritems() if str(d2['graphServer']) == '21314']
#b={'devices':toBeGraphed}
#a = par.snpRequest("castello.guifi.net","stats",b,0,False)
#OR
#a = par.doParallelStatsRequests("http://perafita.guifi.net/snpservices/index.php?call=stats",b,0,False)