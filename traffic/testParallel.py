#!/usr/bin/env python
#
# snpservicesClient.py

import urllib2
import sys


commands = ["help", "version", "phpinfo", "serverinfo"]
services = [
    "availability",
    "example",
    "graph",
    "liveping",
    "livetraceroute",
    "stats"]


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
        # Add arguments
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
        # New code
        # Url character Limit
        # http://stackoverflow.com/a/1289610
        if arguments < 4000:
            doRequest(base, arguments, timeout)
        else:
            doParallellRequests(base,args, timeout)

        # Make request
        url = base + arguments
        print len(arguments)
        #print("SNPServices request to graph server: %s" % url)
        req = urllib2.Request(url)
        #if timeout:
        #   response = urllib2.urlopen(req, timeout=timeout)
        #else:
        #    response = urllib2.urlopen(req)
        # New code
        response = doRequest(req,timeout)


        if csv:
            return response
        else:
            data = response.read()
            return data

#/snpservices/index.php?call=stats&devices=


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


def chunks(l, n):
    """Yield successive n-sized chunks from l."""
    for i in xrange(0, len(l), n):
        yield l[i:i+n]

def doParallelRequests(base, arguments, timeout):
    arglists  = list(chunks(arguments,))
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
    # Make request
    url = base + arguments
    print len(arguments)
    #print("SNPServices request to graph server: %s" % url)
    req = urllib2.Request(url)
    if timeout:
        return urllib2.urlopen(req, timeout=timeout)
    else:
        return urllib2.urlopen(req)

# Define utilites for parallel request
from urlparse import urlparse
from threading import Thread
import httplib, sys
from Queue import Queue

concurrent = 200

def doWork():
    while True:
        url = q.get()
        status, url = getStatus(url)
        doSomethingWithResult(status, url)
        q.task_done()

def getStatus(ourl):
    try:
        url = urlparse(ourl)
        conn = httplib.HTTPConnection(url.netloc)
        conn.request("HEAD", url.path)
        res = conn.getresponse()
        return res.status, ourl
    except:
        return "error", ourl

def doSomethingWithResult(status, url):
    print status, url



# 10k/max_numero_ids_por_url/max_concurrent

def doParallelRequest(request, timeout):
    q = Queue(concurrent * 2)
    for i in range(concurrent):
        t = Thread(target=doWork)
        t.daemon = True
        t.start()
    try:
        for url in open('urllist.txt'):
            q.put(url.strip())
        q.join()
    except KeyboardInterrupt:
        sys.exit(1)





     if timeout:
            return urllib2.urlopen(req, timeout=timeout)
        else:
            return urllib2.urlopen(req)


