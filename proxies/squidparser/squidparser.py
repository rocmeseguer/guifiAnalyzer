"""
This module implements the backend class that communicates with
MongoDB for the database that stores all the collected SQUID logs. 
"""

from guifiAnalyzer.lib.squidlog.squidlog import SquidLog

import pandas as pd

import datetime
import os
import fnmatch
import pdb


log_dir = os.path.join(os.getcwd(),'guifiAnalyzer','proxies','logs','new')

class SquidParser(object):

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



