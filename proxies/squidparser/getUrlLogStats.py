#test.py
from guifiAnalyzer.proxies.squidparser.squidparser import SquidUrlParser, getDomain

import pandas as pd
import numpy as np
from sklearn.decomposition import PCA


import multiprocessing

from matplotlib import pyplot as plt
plt.style.use('ggplot')
import pdb
import os

output_dir = os.path.join( os.getcwd(), 'guifiAnalyzerOut', 'results','getUrlLogStats')



def helper(proxy):
	print '%s: Worker Started' % multiprocessing.current_process().name
	parser = SquidUrlParser(proxy)
	df = parser.getUrlsTimeSeries()
	print '%s: Worked Done' % multiprocessing.current_process().name
	return df

def start_process():
    print 'Starting', multiprocessing.current_process().name


def proxiesStats(proxy_ids):
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


	pdb.set_trace()

	top_requests_percent = (logs_df.url.value_counts()/len(logs_df.url))
	top_requests_percent.name = 'requests_frequency'
	top_requests_per_bytes_percent =logs_df.groupby('url').bytes.sum().sort_values(ascending=False)/logs_df.bytes.sum()
	top_requests_per_bytes_percent.name = 'requests_traffic_frequency'
	top_requests = pd.concat([top_requests_per_bytes_percent, top_requests_percent], axis=1).sort_values('requests_traffic_frequency',ascending=False)*100
	top_requests = top_requests[top_requests['requests_frequency']<3]
	top_requests = top_requests[top_requests['requests_traffic_frequency']<10]
	
	pca = PCA(n_components=2)
	top_requests_pca = pca.fit(top_requests) 
	axis = top_requests_pca.components_.T * (-1)
	plt.figure()
	plt.scatter(top_requests['requests_traffic_frequency'],top_requests['requests_frequency'], s=40,marker='x')
	axis /= axis.std()
	x_axis, y_axis = axis
	plt.quiver(0, 0, x_axis, y_axis, zorder=11, width=0.01, scale=15, color='r')

	plt.xlabel('Requests Traffic Frequency (%)', fontsize=18)
	plt.ylabel('Requests Frequency (%)', fontsize=18)
	plt.title('Requests Frequencies Correlation', fontsize=18)
	plt.show()
	raw_input('End')

	plt.figure()
	top_types_percent = (logs_df.type.value_counts()/len(logs_df.type))
	top_types_percent.name = 'types_frequency'
	top_types_per_bytes_percent =logs_df.groupby('type').bytes.sum().sort_values(ascending=False)/logs_df.bytes.sum()
	top_types_per_bytes_percent.name = 'types_traffic_frequency'
	top_types = pd.concat([top_types_per_bytes_percent, top_types_percent], axis=1).sort_values('types_traffic_frequency',ascending=False)*100
	
	pca = PCA(n_components=2)
	top_types_pca = pca.fit(top_types) 
	axis = top_types_pca.components_.T * (-1)
	plt.figure()
	plt.scatter(top_types['types_traffic_frequency'],top_types['types_frequency'], s=40,marker='x')
	axis /= axis.std()
	x_axis, y_axis = axis
	plt.quiver(0, 0, x_axis, y_axis, zorder=11, width=0.01, scale=15, color='r')

	plt.xlabel('Types Traffic Frequency (%)', fontsize=18)
	plt.ylabel('Types Frequency (%)', fontsize=18)
	plt.title('Types Frequencies Correlation', fontsize=18)
	plt.show()
	raw_input('End')

	plt.figure()
	top_cache_percent = (logs_df.cache_status.value_counts()/len(logs_df.cache_status))
	top_cache_percent.name = 'cache_status_frequency'
	top_cache_per_bytes_percent =logs_df.groupby('cache_status').bytes.sum().sort_values(ascending=False)/logs_df.bytes.sum()
	top_cache_per_bytes_percent.name = 'cache_status_traffic_frequency'
	top_cache = pd.concat([top_cache_per_bytes_percent, top_cache_percent], axis=1).sort_values('cache_status_traffic_frequency',ascending=False)*100
	
	pca = PCA(n_components=2)
	top_cache_pca = pca.fit(top_cache) 
	axis = top_cache_pca.components_.T * (-1)
	plt.figure()
	plt.scatter(top_cache['cache_status_traffic_frequency'],top_cache['cache_status_frequency'], s=40,marker='x')
	axis /= axis.std()
	x_axis, y_axis = axis
	plt.quiver(0, 0, x_axis, y_axis, zorder=11, width=0.01, scale=15, color='r')

	plt.xlabel('Cache Status Traffic Frequency (%)', fontsize=18)
	plt.ylabel('Cache Status Frequency (%)', fontsize=18)
	plt.title('Cache Status Frequencies Correlation', fontsize=18)
	plt.show()
	raw_input('End')



	top_methods_percent = (logs_df.method.value_counts()/len(logs_df.method))
	pdb.set_trace()
	top_methods_percent.name = 'methods_frequency'
	top_methods_per_bytes_percent =logs_df.groupby('method').bytes.sum().sort_values(ascending=False)/logs_df.bytes.sum()
	top_methods_per_bytes_percent.name = 'methods_traffic_frequency'
	top_methods = pd.concat([top_methods_per_bytes_percent, top_methods_percent], axis=1).sort_values('methods_traffic_frequency',ascending=False)*100
	#top_methods = top_methods[top_methods['methods_frequency']]
	#top_methods = top_methods[top_methods['methods_traffic_frequency']]
	
	pca = PCA(n_components=2)
	top_methods_pca = pca.fit(top_methods) 
	axis = top_methods_pca.components_.T * (-1)
	plt.figure()
	plt.scatter(top_methods['methods_traffic_frequency'],top_methods['methods_frequency'], s=40,marker='x')
	axis /= axis.std()
	x_axis, y_axis = axis
	plt.quiver(0, 0, x_axis, y_axis, zorder=11, width=0.01, scale=15, color='r')

	plt.xlabel('Method Traffic Frequency (%)', fontsize=18)
	plt.ylabel('Method Frequency (%)', fontsize=18)
	plt.title('Method Frequencies Correlation', fontsize=18)
	plt.show()
	raw_input('End')


	if False:

		fname = 'top_requests.tex'
		with open(os.path.join(output_dir,fname), 'w') as f:
			f.write('\\begin{table}[!htb]\n')
			f.write('\\centering\n')
			f.write('\\rowcolors{2}{lightgray}{darkgray}\n')
			top_requests.head(n=10).to_latex(f, column_format='l p{1.5cm} p{1.5cm}', formatters=[formatter, formatter])		
			f.write('\\caption{Domain Requests Relative Frequency and Relative Bytes Frequency}')
			f.write('\\end{table}\n')

		fname = 'top_types.tex'
		with open(os.path.join(output_dir,fname), 'w') as f:
			f.write('\\begin{table}[!htb]\n')
			f.write('\\centering\n')
			f.write('\\rowcolors{2}{lightgray}{darkgray}\n')
			top_types.head(n=10).to_latex(f, column_format='l p{1.5cm} p{1.5cm}',formatters=[formatter, formatter])
			f.write('\\caption{Request Types Relative Frequency and Relative Bytes Frequency}')
			f.write('\\end{table}\n')

		fname = 'top_cache.tex'
		with open(os.path.join(output_dir,fname), 'w') as f:
			f.write('\\begin{table}[!htb]\n')
			f.write('\\centering\n')
			f.write('\\rowcolors{2}{lightgray}{darkgray}\n')
			top_cache.head(n=10).to_latex(f, column_format='l p{1.65cm} p{1.5cm}', formatters=[formatter, formatter])
			f.write('\\caption{Cache Statuses Relative Frequency and Relative Bytes Frequency}')
			f.write('\\end{table}\n')

		fname = 'top_methods.tex'
		with open(os.path.join(output_dir,fname), 'w') as f:
			f.write('\\begin{table}[!htb]\n')
			f.write('\\centering\n')
			f.write('\\rowcolors{2}{lightgray}{darkgray}\n')
			top_methods.to_latex(f, column_format='l p{1.5cm} p{1.5cm}', formatters=[formatter1, formatter1])
			f.write('\\caption{Methods Relative Frequency and Relative Bytes Frequency}')
			f.write('\\end{table}\n')

	#pdb.set_trace()


def OLSRegr(data,x,y):
	# Linear OLS regression using statsmodels
	# create a fitted model in one line
	form = '%s ~ %s' % (y,x)
	lm = smf.ols(formula=form, data=data).fit()
	X_new = pd.DataFrame({x: [data[x].min(), data[x].max()]})
	preds = lm.predict(X_new)
	return X_new,preds

def getECDF(df):
	df = df.sort_values().value_counts()
	ecdf = df.sort_index().cumsum()*1./df.sum()
	return ecdf

def formatter(x):
	st = '%2.1f' % x
	return st+'%'

def formatter1(x):
	st = '%2.2f' % x
	return st+'%'

proxies=['3982','10473','11252','18202']
#proxies = ['10473','18202']
#proxies=['18202']
proxiesStats(proxies)
