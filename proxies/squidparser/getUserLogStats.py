#test.py
from guifiAnalyzer.proxies.squidparser.squidparser import SquidUserParser

import pandas as pd
import numpy as np

import multiprocessing

from matplotlib import pyplot as plt
plt.style.use('ggplot')
import pdb



def getSampledDFByHour(dfs, sample_freq='60Min',sample_fun='sum', var='bytes', groupby=True, merge_fun='mean'):
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
	if merge_fun == 'mean':
		new_df['mean'] = new_df.mean(axis=1)
	elif merge_fun == 'sum':
		new_df['sum'] = new_df.sum(axis=1)
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
	parser = SquidUserParser(proxy_id)
	dfs = parser.getUsersTimeSeries()

	plotUsersProxyStats(dfs, proxy_id, sample_freq='60Min',sample_fun='sum',var='bytes', groupby=True)
	plotUsersProxyStats(dfs, proxy_id, sample_freq='60Min',sample_fun='mean',var='timeElapsed', groupby=True)

#proxy = '10473'
#plotUserProxyStats(proxy)





def getUsersProxiesBytesLog(proxies):
	usersproxy_stats_df = {}
	for proxy in proxies:
		parser = SquidUserParser(proxy)
		dfs = parser.getUsersTimeSeries()
		df = getSampledDFByHour(dfs, sample_freq='60Min',sample_fun='sum', var='bytes', groupby=False)
		usersproxy_stats_df[proxy] = df

	usersproxies_stats_df = pd.concat(usersproxy_stats_df.values(), axis=1)
	return usersproxies_stats_df

def getBytesPerUser(proxies):
	bytes_per_user = {}
	for proxy in proxies:
		parser = SquidUserParser(proxy)
		dfs = parser.getUsersTimeSeries()
		for user, df in dfs.iteritems():
			bytes_per_user[user] = df['bytes'].sum()
	return bytes_per_user

def getBytesElapsedTSPerUser(proxies):
	bytes_ts_per_user = {}
	bytes_per_user = {}
	elapsed_ts_per_user = {}
	elapsed_per_user = {}
	for proxy in proxies:
		parser = SquidUserParser(proxy)
		dfs = parser.getUsersTimeSeries()
		for user, df in dfs.iteritems():
			bytes_ts = pd.Series(df['bytes'].resample('60Min', how='sum'), name=user)
			elapsed_ts = pd.Series(df['timeElapsed'].resample('60Min', how='sum'), name=user)
			bytes_ts_per_user[user] = bytes_ts
			bytes_per_user[user] = df['bytes'].sum()
			elapsed_ts_per_user[user] = elapsed_ts
			elapsed_per_user[user] = df['timeElapsed'].sum()
	return bytes_ts_per_user, bytes_per_user, elapsed_ts_per_user, elapsed_per_user



def helper(proxy):
	print 'Worker Started'
	parser = SquidUserParser(proxy)
	dfs = parser.getUsersTimeSeries()
	df = getSampledDFByHour(dfs, sample_freq='60Min',
								sample_fun='sum', 
								var='bytes', 
								groupby=False,
								merge_fun='sum')
	ts_bytes = pd.Series(df['sum'], name=proxy)
	df = getSampledDFByHour(dfs, sample_freq='60Min', 
								sample_fun='sum', 
								var='timeElapsed', 
								groupby=False,
								merge_fun='sum')
	ts_delay = pd.Series(df['sum'], name=proxy)
	print 'Worked Done'
	return ts_bytes,ts_delay

def start_process():
    print 'Starting', multiprocessing.current_process().name


def plotProxiesStats(proxy_ids):
	ts_bytes_list = []
	ts_delay_list = []
	pool = multiprocessing.Pool(processes=len(proxy_ids),
								initializer=start_process,
								)
	pool_outputs = pool.map(helper, proxy_ids)
	pool.close()
	pool.join()
	print 'Joined'
	for (ts_bytes,ts_delay) in pool_outputs:
		ts_bytes_list.append(ts_bytes)
		ts_delay_list.append(ts_delay)


	#plt.figure()
	#plt.subplot(311)
	df = pd.concat(ts_bytes_list, axis=1)
	#ax = df.plot(legend=True, logy=True)
	#ax.set_ylabel('Bytes')
	plt.plot(df)
	
	mean = df.mean(axis=1)
	
	#ax = mean.plot(legend=True, logy=True, title='Proxies Bytes per hour')
	#ax.lines[-1].set_linewidth(2)
	#ax.yaxis.label.set_size(16)
	#ax.xaxis.label.set_size(16)
	plt.plot(mean,linestyle='--', linewidth=2)
	plt.yscale('log')
	plt.ylabel('Bytes', fontsize=20)
	plt.title('Proxies Bytes per hour', fontsize=20)

	plt.xticks(fontsize=18)
	plt.yticks(fontsize=18)
	#ax.tick_params(axis=u'both', which=u'both',length=2)
	plt.show()
	#raw_input("End")

	plt.subplot(312)
	df1 = pd.concat(ts_delay_list, axis=1)
	#ax = df1.plot(legend=True, logy=True)
	#ax.set_ylabel('Time Elapsed (ms)')
	plt.plot(df1)

	mean = df1.mean(axis=1)
	
	#ax = mean.plot(legend=True, logy=True, title='Proxies Elapsed Time per hour')
	plt.plot(mean,linestyle='--', linewidth=2)
	#ax.lines[-1].set_linewidth(2)
	#ax.yaxis.label.set_size(16)
	#ax.xaxis.label.set_size(16)
	plt.yscale('log')
	plt.ylabel('Time Elapsed (ms)', fontsize=20)
	plt.title('Proxies Elapsed Time per hour', fontsize=20)

	plt.xticks(fontsize=18)
	plt.yticks(fontsize=18)


	plt.show()
	#raw_input("End")

	plt.subplot(313)
	df2 = df/df1.replace({ 0 : np.nan })
	df2 = df2*1000
	#ax = df2.plot(legend=True, logy=True)

	plt.plot(df2)

	#ax.set_ylabel('Speed (Bytes/sec)')
	mean = df2.mean(axis=1)
	#ax = df2['mean'].plot(legend=True, logy=True, title='Proxies Bytes Over Elapsed Time per Hour')
	#ax.lines[-1].set_linewidth(2)
	#ax.yaxis.label.set_size(16)
	#ax.xaxis.label.set_size(16)
	plt.plot(mean,linestyle='--', linewidth=2)
	plt.yscale('log')
	plt.ylabel('Speed (Bytes/sec)', fontsize=20)
	plt.title('Proxies Bytes Over Elapsed Time per Hour', fontsize=20)


	plt.xticks(fontsize=18)
	plt.yticks(fontsize=18)
	plt.show()
	raw_input("End")

	#TODO FIND PROXY SPEEd FROM ABOVE
	# TODO APPLY INFO FROM USERS TO LINKS


proxies=['3982','10473','11252','18202']
#proxies = ['10473','18202']
plotProxiesStats(proxies)
