#test.py
from guifiAnalyzer.proxies.squidparser.squidparser import SquidParser

import pandas as pd
from matplotlib import pyplot as plt
plt.style.use('ggplot')
import pdb



def getSampledDFByHour(dfs, sample_freq='60Min',sample_fun='sum', var='bytes', groupby=True):
	new_dfs = []
	for user, df in dfs.iteritems():
		#Sampling
		ts = pd.Series(df[var].resample(sample_freq, how=sample_fun), name=user)
		df1 = pd.DataFrame(ts)
		#Groupby hour
		if groupby:
			df1['hour'] = df1.index.hour
			new_dfs.append(df1.groupby('hour').mean())
		else:
			new_dfs.append(df1)
	#Merge all users
	new_df = pd.concat(new_dfs, axis=1).fillna(0)
	new_df['mean'] = new_df.mean(axis=1)
	return new_df



def plotUsersProxyStats(dfs, proxy_id, sample_freq, sample_fun, var, groupby):
	new_df = getSampledDFByHour(dfs, sample_freq=sample_freq, sample_fun=sample_fun, var=var, groupby=groupby)
	title = 'Proxy '+proxy_id+' Users Mean ' + var + ' per hour'
	new_df.plot(legend=False, logy=True, style='o', title=title)
	
	#Plot mean
	ax=new_df['mean'].plot(legend=True, logy=True)
	ax.lines[-1].set_linewidth(1.5)
	ax.set_ylabel(var)
	ax.yaxis.label.set_size(16)
	ax.xaxis.label.set_size(16)
	plt.xticks(fontsize=14)
	plt.yticks(fontsize=14)
	pdb.set_trace()
	#plt.ylim((0,70000000))
	plt.show()
	raw_input("End")


def plotUserProxyStats(proxy_id):
	parser = SquidParser(proxy_id)
	dfs = parser.getUsersTimeSeries()

	plotUsersProxyStats(dfs, proxy_id, sample_freq='60Min',sample_fun='sum',var='bytes', groupby=True)
	plotUsersProxyStats(dfs, proxy_id, sample_freq='60Min',sample_fun='mean',var='timeElapsed', groupby=True)

#proxy = '10473'
#plotUserProxyStats(proxy)





def getUsersProxiesBytesLog(proxies):
	usersproxy_stats_df = {}
	for proxy in proxies:
		parser = SquidParser(proxy)
		dfs = parser.getUsersTimeSeries()
		df = getSampledDFByHour(dfs, sample_freq='60Min',sample_fun='sum', var='bytes', groupby=False)
		usersproxy_stats_df[proxy] = df

	usersproxies_stats_df = pd.concat(usersproxy_stats_df.values(), axis=1)
	return usersproxies_stats_df

def getBytesPerUser(proxies):
	bytes_per_user = {}
	for proxy in proxies:
		parser = SquidParser(proxy)
		dfs = parser.getUsersTimeSeries()
		for user, df in dfs.iteritems():
			bytes_per_user[user] = df['bytes'].sum()
	return bytes_per_user

def getBytesTSPerUser(proxies):
	bytes_ts_per_user = {}
	bytes_per_user = {}
	for proxy in proxies:
		parser = SquidParser(proxy)
		dfs = parser.getUsersTimeSeries()
		for user, df in dfs.iteritems():
			ts = pd.Series(df['bytes'].resample('60Min', how='sum'), name=user)
			bytes_ts_per_user[user] = ts
			bytes_per_user[user] = df['bytes'].sum()
	return bytes_ts_per_user, bytes_per_user


def plotProxiesStats(proxy_ids):
	ts_bytes_list = []
	ts_delay_list = []
	for proxy in proxy_ids:
		parser = SquidParser(proxy)
		dfs = parser.getUsersTimeSeries()
		df = getSampledDFByHour(dfs, sample_freq='60Min',sample_fun='sum', var='bytes')
		ts = pd.Series(df['mean'], name=proxy)
		ts_bytes_list.append(ts)
		df = getSampledDFByHour(dfs, sample_freq='60Min',sample_fun='mean', var='timeElapsed')
		ts = pd.Series(df['mean'], name=proxy)
		ts_delay_list.append(ts)

	df = pd.concat(ts_bytes_list, axis=1)
	ax = df.plot(legend=True, logy=True)
	ax.set_ylabel('Bytes')
	df['mean'] = df.mean(axis=1)
	ax = df['mean'].plot(legend=True, logy=True, title='Proxies Bytes per hour')
	ax.lines[-1].set_linewidth(2)
	ax.yaxis.label.set_size(16)
	ax.xaxis.label.set_size(16)
	plt.xticks(fontsize=14)
	plt.yticks(fontsize=14)
	plt.show()
	raw_input("End")

	df = pd.concat(ts_delay_list, axis=1)
	ax = df.plot(legend=True, logy=True)
	ax.set_ylabel('Time Elapsed (ms)')
	df['mean'] = df.mean(axis=1)
	ax = df['mean'].plot(legend=True, logy=True, title='Proxies Elapsed Time per hour')
	ax.lines[-1].set_linewidth(2)
	ax.yaxis.label.set_size(16)
	ax.xaxis.label.set_size(16)
	plt.xticks(fontsize=14)
	plt.yticks(fontsize=14)
	plt.show()
	raw_input("End")

	#TODO FIND PROXY SPEEd FROM ABOVE
	# TODO APPLY INFO FROM USERS TO LINKS


#proxies=['3982','10473','11252','18202']
#plotProxiesStats(proxies)