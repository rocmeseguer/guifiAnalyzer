"""
This module implements the backend class that communicates with
MongoDB for the database that stores all the collected SQUID logs. 
"""

from guifiAnalyzer.lib.squidlog.squidlog import SquidLog

import pandas as pd

import datetime
import os
import fnmatch
from urlparse import urlparse
from tldextract import extract

log_dir = os.path.join(os.getcwd(),'guifiAnalyzer','proxies','logs','new')

class SquidUserParser(object):

	def __init__(self,proxy_id):
		self.proxy_id = proxy_id
		self.logs_by_date = {}
		self.users = []
		self.ips = []
		self.populate()
		self.findUsersNIPs()



	def populate(self):
		name = self.proxy_id+'_*_access_1.log.gz'
		for fil in os.listdir(log_dir):
		    if fnmatch.fnmatch(fil, name):
		    	path = os.path.join(log_dir,fil)
		    	date = fil.split('_')[1]
		        log = SquidLog(path)
		        self.logs_by_date[date] = log


	def findUsersNIPs(self):
		for date, log in self.logs_by_date.iteritems():
			for l in log:
				self.users.append((l.remhost,l.rfc931))
				self.ips.append(l.remhost)
			self.users = list(set(self.users))
			self.ips = list(set(self.ips))


	def getUsersTimeSeries(self):
		self.populate()
		dics = {}
		for user in self.users:
			dics[user] = {'timeElapsed':{},'bytes':{}}
		for date, log in self.logs_by_date.iteritems():
			for l in log:
				ts = datetime.datetime.fromtimestamp(l.ts)
				dics[(l.remhost,l.rfc931)]['timeElapsed'][ts] = int(l.elapsed)
				dics[(l.remhost,l.rfc931)]['bytes'][ts] = int(l.bytes)
		dfs = {}
		for user,dic in dics.iteritems():
			df = pd.DataFrame(dic)
			#df.index = pd.to_datetime(df.index, unit='s')
			dfs[user] = df
		return dfs

def getDomain(url):
#		url = url.replace('http://','').split('/')[0].split(':')[0]
#		split = url.split('.')
#		if len(split) > 1:
#			return url.split('.')[-2]+'.'+url.split('.')[-1]
#		else:
#			return url
	if not url.startswith('http'):
		url = '%s%s' % ('http://', url)
	p = urlparse(url) 
	p = p.hostname if p.hostname else p.netloc
	if  p.startswith('www.'):
		p = p.lstrip('www.')
	return extract(p).domain


class SquidUrlParser(object):

	def __init__(self,proxy_id):
		self.proxy_id = proxy_id
		self.logs = []
		self.populate()

	def populate(self):
		name = self.proxy_id+'_*_access_0.log.gz'
		for fil in os.listdir(log_dir):
		    if fnmatch.fnmatch(fil, name):
		    	path = os.path.join(log_dir,fil)
		    	date = fil.split('_')[1]
		        log = SquidLog(path)
		        self.logs.append(log)

	def getUrlsTimeSeries(self):
		result = []
		for log in self.logs:
			for l in log:
				ts = datetime.datetime.fromtimestamp(l.ts)
				url = l.url
				dic = {'proxy':self.proxy_id,
						'ts': ts,
						'user': l.remhost+':'+l.rfc931,
						'timeElapsed': l.elapsed,
						'bytes': int(l.bytes),
						'url': getDomain(l.url),
						'type': l.type,
						'cache_status': l.status.split('/')[0],
						'request_status': l.status.split('/')[1]}
				result.append(dic)

		df = pd.DataFrame(result)
		#df.index = pd.to_datetime(df.index, unit='s')
		return df
