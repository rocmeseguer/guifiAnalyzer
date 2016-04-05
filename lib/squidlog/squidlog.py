#!/usr/bin/env python
"""

Code to read a squid log file
    
Sample usage:

f = SquidLog('access.log.1.gz')
for l in f:
    print l.ts, l.remhost, l.url
   
AJC Nov 2007

"""                          

import gzip
import time   
import sys
import operator
   
# time format for pretty-printing log files   
_time_format = "%d %b %Y %H:%M:%S"    

class SquidLogLine(object):
    """Representation of a squid log entry
    
    Items are 'ts', 'elapsed', 'remhost', 'status', 'bytes', 'method', 'url', 'rfc931', 'peerstatus', 'type'
    
    'ip' is available as an alias for 'remhost'
    
    """ 
    fields = ['ts', 'elapsed', 'remhost', 'status', 'bytes', 'method', 'url', 'rfc931', 'peerstatus', 'type']  

    def __init__(self, line, print_human_times=False, print_minimal=False):
        """setup fields""" 
        self._print_human_times = print_human_times 
        self._print_minimal = print_minimal 
        try:                                        
            map( lambda k,v: setattr(self, k, v), SquidLogLine.fields, line.split() )
        except TypeError:
            # wacky data in file, probably space in the url
            # let's assume that and bung it back together 
            # sample guff data
            # 1187251401.688      1 192.168.35.2 TCP_DENIED/400 3612 GET http://a676.g.aka! maitech.net/f/676/773/60m/images.delivery.net/cm50content/2455/09008101807516c1/5-2007_PCS_TurnOffPa_130x200.jpg - NONE/- text/html
            l = line.split()
            l = l[:6] + [''.join(l[6:-3])] + l[-3:]
            map( lambda k,v: setattr(self, k, v), SquidLogLine.fields, l )
        self.client = self.remhost
        try:
            self.ts = float(self.ts)  
        except TypeError, e:
            # blank line
            if self.ts == None:
                pass
            else:
                raise e
        
    def __str__(self):   
        if self._print_human_times:
            s = "%s " % time.strftime(_time_format, time.localtime(self.ts))
        else:
            s = "%s " % self.ts 
        if self._print_minimal: 
            s += "%s %s %s %s %s" % (self.remhost, self.status[-3:], self.method, self.url, self.type)
        else:
            for k in SquidLogLine.fields[1:]:
                s += "%s " % getattr(self, k)
            s = s[:-1]
        return s
                
class SquidLog(object):
    """
    Class for opening and reading Squid logfile
    f can be any iterator
    """
    def __init__(self, f, print_human_times = False, print_minimal=False): 
        """open a squid logfile, optionally gziped""" 
        if type(f) == type(str()):
            # assume it's a filename and try and open it
            try:      
                self.f = gzip.open(f) 
                self.f.next()
                self.f.rewind()
            except IOError, e:         
                self.f = open(f)
            except StopIteration, e:
                pass
        else:
            # it's an iterator of some sort
            self.f = f
        self._print_human_times = print_human_times 
        self._print_minimal = print_minimal
            
    def __iter__(self):
        """iterator creator"""
        return self
        
    def next(self):
        """returns next line from the logs"""
        line = self.f.next()
        return SquidLogLine( line, print_human_times=self._print_human_times, print_minimal=self._print_minimal )
        
    def close(self):
        """close fh"""
        self.f.close()
        
if __name__ == '__main__':
    # sample code. Calc top 100 sites viewed
    import sys
    log = SquidLog(sys.argv[1], print_human_times = True, print_minimal=True) 
    counts = {}
    for l in log:
        if l.type == "text/html":
            if l.method == "CONNECT":
                vhost = (l.url).split(':')[0]
            else:
                try:
                    vhost = (l.url).split("/")[2]
                except IndexError:
                    continue
            counts[vhost] = counts.get(vhost, 0) + 1
    print sorted(counts.iteritems(), key=operator.itemgetter(1), reverse=True)[0:100]
