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


def buildArgs(args):
    """
    Take a list of arguments and convert it to a url
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




def doParallelRequests(base, args, timeout, csv):
    # Define utilites for parallel request
    from urlparse import urlparse
    from threading import Thread
    import httplib, sys
    from Queue import Queue

    def buildUrls(base, argsLists):
        argumentsList = map(buildArgs,argsList)
        urlsList = [(base+argument) for argument in argumentsList]
        return urlsList

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
            req = urllib2.Request(url)
            if timeout:
                responses.extend(urllib2.urlopen(req, timeout=timeout))
            else:
                responses.extend(urllib2.urlopen(req))
            q.task_done()
             # Parallel stuff end above this command

    

    # Separate arguments in lists that fit the apache max url size (4000 chars)
    chunksize = (len(args)*6) / (4000-len(base))
    argsLists  = list(chunks(args, chunksize))
    urls = [buildUrls(base,argsList) for argsList in argsLists]
    print urls
    #Do parallel request for each url innlist
    concurrent = len(urls)
    q = Queue(concurrent * 2)
    responses = []

    for i in range(concurrent):
        t = Thread(target=worker)
        t.daemon = True
        t.start()
    try:
        for url in urls:
            q.put(url.strip())
        q.join()

    if csv:
        # TODO
        #Merge all responses in one csv... How?????
        return response
    else: 
        readResponses = [r.read() for r in responses]
        return readResponses


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
        
        # New code
        # Url character Limit
        # http://stackoverflow.com/a/1289610
        if len(arguments) < 4000:
            response = doRequest(base, arguments, timeout)
        else:
            response = doParallellRequests(base, args, timeout, csv)

        if csv:
            return response
        else:
            data = response.read()
            return data

#/snpservices/index.php?call=stats&devices=



