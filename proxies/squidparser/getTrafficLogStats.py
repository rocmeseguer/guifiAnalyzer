#test.py
from guifiAnalyzer.proxies.squidparser.squidparser import SquidTrafficParser

import pandas as pd
import numpy as np
from scipy import signal

from statsmodels.graphics.tsaplots import plot_acf, plot_pacf
from statsmodels.tsa.seasonal import seasonal_decompose
from statsmodels.tsa import stattools
from statsmodels.stats import stattools as stat1


from matplotlib import pyplot as plt
plt.style.use('ggplot')

import multiprocessing
import os
import pdb

output_dir = os.path.join( os.getcwd(), 'guifiAnalyzerOut', 'results','getTrafficLogStats')

def helper(proxy):
	print '%s: Worker Started' % multiprocessing.current_process().name
	parser = SquidTrafficParser(proxy)
	df = parser.getTrafficTimeSeries()
	print '%s: Worked Done' % multiprocessing.current_process().name
	return df

def start_process():
    print 'Starting', multiprocessing.current_process().name


def resampler_count(array_like):
	return array_like.size



def proxiesStats(proxy_ids):
	### GET TIME SERIES
	logs_df_file = os.path.join(output_dir,'logs_df')
	if os.path.isfile(logs_df_file):
		logs_df = pd.read_pickle(logs_df_file)
	else:
		pool = multiprocessing.Pool(processes=len(proxy_ids),
									initializer=start_process,
									)
		pool_outputs = pool.map(helper, proxy_ids)
		pool.close()
		pool.join()
		print 'Joined'
		logs_df = pd.concat(pool_outputs, ignore_index=True)
		logs_df.to_pickle(logs_df_file)


	bytes_ts = pd.Series(logs_df['bytes'].set_index('ts').bytes.resample('60Min', how='sum'))
	requests_ts = pd.Series(logs_df['bytes'].set_index('ts').bytes.resample('60Min', how='resampler_count'))
	bytes_df = pd.DataFrame(bytes_ts)
	requests_df = pd.DataFrame(requests_ts)
	pdb.set_trace()

	### PLOT GENERAL TIME SERIES GRAPHS
	bytes_df.plot(logy=True)
	plt.show()
	raw_input('End')

	periodogram = stattools.periodogram(bytes_df.bytes)
	plotTwin(bytes_df,'Bytes', periodogram, 'Frequency', 'Periodogram')

	acf = stattools.acf(bytes_df)
	plotTwin(bytes_df, 'Bytes', 'acf', 'Correlation Coefficient', 'Autocorrelation', bytes_df)

	pacf = stattools.pacf(bytes_df)
	plotTwin(bytes_df, 'Bytes', 'pacf', 'Partial Correlation Coefficient', 'Partial Autocorrelation', bytes_df)


	decomposition = seasonal_decompose(bytes_df.values, freq=24)
	decomposition.plot()
	plt.show()
	raw_input('End')

	du_wa = stat1.durbin_watson(np.nan_to_num(decomposition.resid))
	print 'Durbin-Watson test for residuals: %s' % du_wa


	### EVEN/ODD ANALYSIS 
	#odd_mask = bytes_df.index.map(lambda x: x.day%2 ) == 1
	odd_mask = bytes_df.index.map(lambda x: x.day in [15,17,19,21]) == True
	bytes_df_odd = bytes_df[odd_mask].shift(-7,'D')

	#even_mask = bytes_df.index.map(lambda x: x.day%2) == 0
	even_mask = bytes_df.index.map(lambda x: x.day in [8,10,12,14]) == True
	bytes_df_even = bytes_df[even_mask]

	fig, ax1 = plt.subplots()
	lns1 = ax1.plot(bytes_df_odd, 'b--', label='Odd', visible=True)
	lns2 =ax1.plot(bytes_df_even, 'b:', label='Even', visible=True)
	ax1.set_ylabel('Bytes', color='b', fontsize=18)
	ax1.set_yscale('log')
	for tl in ax1.get_yticklabels():
		tl.set_color('b')
	
	#corr = pd.rolling_corr(arg1=bytes_df_odd['bytes'],arg2=bytes_df_even['bytes'].shift(-24,'H'),window=24)
	#corr = pd.rolling_corr(arg1=bytes_df_odd['bytes'],arg2=bytes_df_even['bytes'],window=24)
	corr = bytes_df_odd['bytes'].rolling(window=24).corr(other=bytes_df_even['bytes'])

	ax2=ax1.twinx()
	lns3 = ax2.plot(corr, 'r-', label='Correlation', visible=True)
	lns = lns1+lns2+lns3
	labs = [l.get_label() for l in lns]
	ax1.legend(lns, labs, loc=0)
	ax2.set_ylabel('Correlation Coefficient', color='r', fontsize=18)
	for tl in ax2.get_yticklabels():
		tl.set_color('r')
	plt.show()
	raw_input('End')

	print 'Even/Odd correlation: %s' %  bytes_df_odd.corrwith(bytes_df_even).bytes



def plotTwin(a,labela, b, labelb, title, df=None):
	fig,ax1 = plt.subplots()	
	ax1.plot(a,'b')
	ax1.set_ylabel(labela, color='b', fontsize=18)
	ax2 = ax1.twinx()
	ax2.set_ylabel(labelb, color='r', fontsize=18)
	if b=='acf':
		plot_acf(df,ax2)
	elif b=='pacf':
		plot_pacf(df,ax2)
	else:
		ax2.plot(b,'r')
	for tl in ax1.get_yticklabels():
		tl.set_color('b')
	for tl in ax2.get_yticklabels():
		tl.set_color('r')
	plt.title(title)
	plt.show()
	raw_input('End')

	

def getECDF(df):
	df = df.sort_values().value_counts()
	ecdf = df.sort_index().cumsum()*1./df.sum()
	return ecdf

proxies=['3982','10473','11252','18202']
#proxies = ['10473','18202']
#proxies=['18202']
proxiesStats(proxies)
