#test.py
from guifiAnalyzer.proxies.squidparser.squidparser import SquidUrlParser, getDomain

import pandas as pd
import numpy as np

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


def plotProxiesStats(proxy_ids):
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

	plt.figure()
	(logs_df.url.value_counts()/len(logs_df.url)).head(n=10).plot(kind='bar', title='1')
	plt.show()
	raw_input("End")
	plt.figure()
	(logs_df.type.value_counts()/len(logs_df.type)).head(n=10).plot(kind='bar', title='2')
	plt.show()
	raw_input("End")



proxies=['3982','10473','11252','18202']
#proxies = ['10473','18202']
#proxies=['18202']
plotProxiesStats(proxies)
