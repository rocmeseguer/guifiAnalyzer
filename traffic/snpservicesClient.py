#!/usr/bin/env python
#
# snpservicesClient.py

import urllib2
import sys
import socket

from exceptions import *

import pdb

from guifiAnalyzer.lib.pingparser import pingparser 

commands = ["help", "version", "phpinfo", "serverinfo"]
services = [
    "availability",
    "example",
    "graph",
    "liveping",
    "livetraceroute",
    "stats"]




def buildArgs(args,command):
    """
    Take a dictionary of arguments and values and convert it to a url
    string
    """
    arguments = ""
    for arg in args:
        arguments += "&" + str(arg)
        if args[arg]:
            arguments += "="
            if command == 'stats':
                for i in args[arg]:
                    if i == args[arg][-1]:
                        #print i
                        arguments += str(i)
                    else:
                        # print i
                        arguments += str(i) + ","
            else:
                arguments += str(args[arg])
    return arguments

def doRequest(base, arguments, timeout):
    # Make request
    url = base + arguments
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
                url += str(i)
            else:
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
            #print "%s\n" % url
            req = urllib2.Request(url)
            req_params = {}
            if timeout:
                req_params['timeout'] = timeout
            while True:
                try:
                    response = urllib2.urlopen(req, **req_params)
                    #print "Done", q.qsize()
                except (urllib2.HTTPError, urllib2.URLError, socket.timeout) as e:
                    print e
                else:
                    break
            #Need to find thread-safe way to return the result
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
    chunksize = (106-len(base))/6
    print "chunksize (# of devices)"
    print chunksize
    devicesLists  = list(chunks(devices, chunksize))
    print "devicesLists"
    print len(devicesLists)
    urls = [buildUrl(base,devicesList) for devicesList in devicesLists]
    #print "Urls"
    urlsLen = [len(url) for url in urls]
    #print urlsLen
    #Do parallel request for each url innlist
    # but use standard number of workers
    concurrent = 70
    q = Queue(len(urls))
    responses = []


    for i in range(concurrent):
        t = Thread(target=worker)
        t.daemon = True
        t.start()
    try:
        for url in urls:
            q.put(url.strip())
        q.join()
    except KeyboardInterrupt:
        sys.exit(1)


    return [resp for resp in responses]


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
        arguments = buildArgs(args, command)
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

        if csv:
            return response
        else:
            data = response.read()
            return data

#/snpservices/index.php?call=stats&devices=

def snpGetDevices(ip, devices):
    url = "http://" + str(ip) + "/snpservices/index.php?call=stats"
    req = urllib2.Request(url)
    response = urllib2.urlopen(req)
    #with open('test.txt','a') as outfile:
    #    outfile.write(response)


def snpLiveTracerouteParser(data):
    """Parses livetraceroute keeping only
       guifi 10.*.*.* ips
    """
    import re

    #exp = re.compile(r'\s+(\d+)\s+(\d+.\d+.\d+.\d+)\s+\((\d+.\d+.\d+.\d+)\)\s+(\d+.\d+)\s+ms\s+(?:![A-Z]\s+)?(\d+.\d+)\s+ms\s+(?:![A-Z]\s+)?(\d+.\d+)\s+ms(?:\s+![A-Z])?')
    exp = re.compile(r'\s+(\d+)\s+([^\s\*]+)\s+\((\d+.\d+.\d+.\d+)\)\s+(\d+.\d+)\s+ms\s+(?:![A-Z]\s+)?(\d+.\d+)\s+ms\s+(?:![A-Z]\s+)?(\d+.\d+)\s+ms(?:\s+![A-Z])?')
    exp1 = re.compile(r'\s+(\d+)\s+\*\s+\*\s+\*\s*')
    lines = data
    hops = {}
    counter = 0
    for line in lines[1:-1]:
        match = exp.search(line)
        try:
            groups = list(match.groups())
        except Exception, e:
            print 'ERROR in line: %s' % line 
            continue

        # If ip starts with 10 and is different with the last ip read
        if groups[2].split('.')[0] !='10' or (counter>= 2 and groups[2]==hops[counter]['ip']):
            continue
        else:
            counter += 1
            hop = counter
            ip = groups[2]
            avg_rtt = (float(groups[3]) + float(groups[4]) + float(groups[5]))/3
            hops[hop] = {'hop':hop, 'ip':ip,'avg_rtt':avg_rtt}
    #pdb.set_trace()
    print hops
    return hops


def snpLivePingParser(data):
    """Parses liveping  using pingparser:
        Parses the `ping_output` string into a dictionary containing the following
        fields:

            `host`: *string*; the target hostname that was pinged
            `sent`: *int*; the number of ping request packets sent
            `received`: *int*; the number of ping reply packets received
            `packet_loss`: *int*; the percentage of  packet loss
            `minping`: *float*; the minimum (fastest) round trip ping request/reply
                        time in milliseconds
            `avgping`: *float*; the average round trip ping time in milliseconds
            `maxping`: *float*; the maximum (slowest) round trip ping time in
                        milliseconds
            `jitter`: *float*; the standard deviation between round trip ping times
                        in milliseconds
    """
     
    return pingparser.parse(data)

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