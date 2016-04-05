

from guifiAnalyzer.db.infrastructure import InfraDB
from guifiAnalyzer.traffic.snpservicesClient import snpRequest, snpLiveTracerouteParser, snpLivePingParser
from guifiAnalyzer.vis.proxiesDB import createGraph
from getIPNetworks import invertListDic, mapping

import networkx as nx
import pandas as pd
from matplotlib import pyplot as plt

import random
from collections import Counter, defaultdict

import pickle

import os
from pprint import pprint
import pdb

root=8346
core = False


proxy_graph = {
	'5417':"10.138.85.130", 
	'4892':"10.228.0.83",
	'7193':'perafita.guifi.net',
	'11697':'10.138.3.162'
}

read_ping = {
	'7857':'7857_routers_ping.out'
}

proxy_pair = {
	'3982':('7193','11697')
}

file_dir = os.path.join( os.getcwd(), 'guifiAnalyzerOut', 'results', 'proxyPing')
helper_dir = os.path.join( os.getcwd(), 'guifiAnalyzer', 'proxies', 'helpers')
getIPNetworks_dir = os.path.join( os.getcwd(), 'guifiAnalyzerOut', 'results', 'getIPNetworks')


def parsePingsFilePerNode(t_file, nodes_per_ip):
	helper = {}
	with open(t_file,'r') as fi:
		node_ip = ''
		for line in fi:
			split_line = line.split(' ')
			if split_line[0] == 'PING':
				node_ip = split_line[2].rstrip('),').lstrip('(')
				node = nodes_per_ip[node_ip][0]
				helper[node] = [line]
			else:
				helper[node].append(line)
	final_pings = {}
	for node, lines in helper.iteritems():
		ping = ''
		for line in lines:
			ping = ping + line + '\n'
		final_pings[node] = ping
	return final_pings


def findPathLoss(proxy):
	print 'Analyzing Proxy %s' % proxy
	#ips_per_node = mapping(root, core,"proxyPing")
	ips_per_node, router_ips_per_node = mapping(root, core,"proxyTrace")
	nodes_per_ip = invertListDic(ips_per_node)

	#fil = os.path.join(getIPNetworks_dir, 'df_proxy_clients')
	#df_proxy_clients = pd.read_pickle(fil)

	if proxy in read_ping:
		pi_path = os.path.join(helper_dir,read_ping[proxy])
		read_pings = parsePingsFilePerNode(pi_path, nodes_per_ip)

	empty_result = {'node':'',
					'received': 0, 
					'host': '', 
					'jitter': 0, 
					'packet_loss': 0, 
					'avgping': 0, 
					'minping': 0, 
					'sent': 0, 
					'maxping': 0
					}

	ping_results = []
	#for node in df_proxy_clients['nodeId'].to_dict().values():
	for node, ips in router_ips_per_node.iteritems():
		#ips = ips_per_node[node]
		ip = ips[0]

		# If destination and source are the same
		if node == proxy:
			ping = empty_result.copy()
			ping['node'] = node 
			ping['host'] = ip
			ping_results.append(ping)
		else:
			data = {}
			# If proxy is working and colocated with a graphserver
			if proxy in proxy_graph:
				data = snpRequest(ip=proxy_graph[proxy], command='liveping', 
									args={'ip':ip, 'count':3}, timeout=60)
				source = proxy
			# if proxy is not colocated with a graphserver and we have
			# obtained manually the traceroute
			elif proxy in read_ping:
				data = read_pings[node]
				source = proxy
			# the weird case of the moved proxies in Llucanes where a new id represents two old ones
			elif proxy in proxy_pair:
				# Use random select of proxy
				proxy_list = list(proxy_pair[proxy])
				help_proxy = random.choice(proxy_list)
				data = snpRequest(ip=proxy_graph[help_proxy], command='liveping', 
									args={'ip':ip, 'count':3}, timeout=60)
				source = help_proxy

			try:
				ping = snpLivePingParser(data)
				ping['node'] = node
				ping['source'] = source
			except Exception, e:
				ping = empty_result.copy()
				ping['node'] = node 
				ping['source'] = source
				ping['host'] = ip
			ping_results.append(ping)
				

	
	df_ping_results = pd.DataFrame(ping_results)
	fil = os.path.join(file_dir, proxy+'_ping_results')
	df_ping_results.to_pickle(fil)
	
	return df_ping_results


def plotProxyToRoutersShortestPathvsRealPath(df):
	df[['shortest_distance', 'distance']].sort_values('shortest_distance').plot(kind='bar',
																title='Proxy to Routers Shortest vs Real Path')
	plt.show()
	raw_input("End")


def plotProxyToNodesShortestPathvsRealPath(df,title):
	df = df[['shortest_distance', 'distance']].sort_values('shortest_distance')
	df.plot(title=title)
	plt.show()
	raw_input("End")


def getECDF(df):
	df = df.sort_values().value_counts()
	ecdf = df.sort_index().cumsum()*1./df.sum()
	return ecdf


def plotECDFPathVSShortestPath(df, title):
	ecdf_path = getECDF(df['distance'])
	ecdf_shortest_path = getECDF(df['shortest_distance'])	
	ecdf = pd.concat([ecdf_path, ecdf_shortest_path], axis=1)
	print ecdf
	ecdf.plot(title=title)
	plt.show()
	raw_input("End")



def combineLogTraceroute(df_proxy_clients, paths_lossess):
	proxy_clients = df_proxy_clients.set_index('nodeId').to_dict()
	paths_lossess = {p:df.set_index('node').to_dict() for p,df in paths_lossess.iteritems()}

	routers_of_clients = []
	for nodeId, router in proxy_clients['router'].iteritems():
		routers_of_clients.append(router)
	routers_of_clients = list(set(routers_of_clients))

	data = []

	#proxy_clients_nodes = proxy_clients['nodeId']
	#nodes = paths_lossess.values()[0].keys()
	for p, df in paths_lossess.iteritems():
		for nodeId in df.values()[0].keys():
	#for i, nodeId in proxy_clients_nodes.iteritems():
		#router = proxy_clients['router'][i]
		#proxy = proxy_clients['proxy'][i]
			if nodeId in routers_of_clients:
				router = proxy_clients['router'][nodeId]  if nodeId in proxy_clients['router'] else 'None'
				proxy = proxy_clients['proxy'][nodeId] if nodeId in proxy_clients['proxy'] else 'None'
				if proxy == 'my_node':
					proxy = '3982'
			#for p, df in paths_lossess.iteritems():
				if nodeId in df['avgping'].keys():
					data.append({'nodeId': nodeId,
								'router': router,
								'proxy' : proxy,
								'source': df['source'][nodeId],
								'avgping' : df['avgping'][nodeId],
								'packet_loss' : df['packet_loss'][nodeId]})

	return pd.DataFrame(data)

	

def drawPathLossess(proxies):
	fil = os.path.join(getIPNetworks_dir, 'df_proxy_clients')
	df_proxy_clients = pd.read_pickle(fil)
	paths_lossess = {}
	#G, _, _= createGraph(root, core)
	for proxy in proxies:
		fil = os.path.join(file_dir, proxy+'_ping_results')
		if  not os.path.isfile(fil):
			paths_lossess[proxy] = findPathLoss(proxy)
		else:
			paths_lossess[proxy] = pd.read_pickle(fil)


	for p,df in paths_lossess.iteritems():
		for i in ['avgping', 'jitter', 'maxping', 'minping', 'packet_loss', 'received', 'sent']:
			df[i] = df[i].astype(float)

	#keep only nodes with results
	#for p,df in paths_lossess.iteritems():
	#	df = df[df.avgping >0].reset_index()

	final_df = combineLogTraceroute(df_proxy_clients, paths_lossess)
	#df = final_df[final_df.proxy==final_df.source]
	#df1 = df[df.nodeId==df.router]
	#df2 = df[df.nodeId!=df.router]
	#final_df['source'] = final_df['source'].where(=='7193'),'3982')
	final_df['source'] = final_df['source'].replace('7193','3982')
	final_df['source'] = final_df['source'].replace('11697','3982')
	#final_df = final_df.replace(final_df.where(final_df.source=='11697'),'3982')
	dfs = final_df.groupby('source')
	for n,grp in dfs:
		grp = grp.set_index('nodeId')
		grp[n] = grp['avgping']
		ecdf = getECDF(grp[n])
		ax = ecdf.plot(legend=True, title='ECDF Client-Routers to Proxy Average Ping Delay')
		ax.set_ylabel('ECDF')
		ax.set_xlabel('Average Ping Delay')

		plt.show()
	#df2['avgping'].plot()
	#plt.show()
	raw_input("End")

	#for p,df in paths_lossess.iteritems():
	#	#pdb.set_trace()
	#	#df['packet_loss'] = df['packet_loss'].astype(float)
	#	df1['avgping'].plot()
	#	plt.show()
	#	raw_input("End")
	#final_df = combineLogTraceroute(df_proxy_clients, paths_lossess)

	return




	links = []
	for l in links_proxies.values():
		links.extend(l)
	none_links = 0
	for src,dst in links:
		if src != None and dst != None:
			if 'weight' in G[src][dst]:
				G[src][dst]['weight'] += 1
			else:
				G[src][dst]['weight'] = 0
		else:
			none_links += 1

	tr_edge_between = nx.edge_betweenness_centrality(G,weight='weight')
	edge_between = nx.edge_betweenness_centrality(G)

	#pprint(tr_edge_between)
	#pprint(edge_between)
	betweeness = []
	for (a,b),between in edge_between.iteritems():
		betweeness.append({'link': a+b, 
							'edge_betweeness' : between,
							'weighted_edge_betweeness' : tr_edge_between[(a,b)]})


	df_betweeness = pd.DataFrame(betweeness)
	df_betweeness.plot()
	plt.show()
	
	raw_input("End")


	#df_reached_shortest_paths = df_shortest_paths.set_index('router')
	#df_reached_shortest_paths = df_reached_shortest_paths[df_reached_shortest_paths.reached==True]
	

	final_df = combineLogTraceroute(df_proxy_clients, shortest_paths)

	#plotProxyToRoutersShortestPathvsRealPath(df_reached_shortest_paths)

	#nodes_df = final_df[final_df.proxy != proxy].set_index('nodeId')
	#plotProxyToNodesShortestPathvsRealPath(nodes_df,'Proxy to Non-Clients Shortest vs Real Path')
	
	#clients_df = final_df[final_df.proxy == proxy].set_index('nodeId')
	#plotProxyToNodesShortestPathvsRealPath(clients_df, 'Proxy to  Clients Shortest vs Real Path')

	reached_clients = final_df[(final_df.reached==True) & (final_df.proxy == final_df.destination)]
	plotECDFPathVSShortestPath(reached_clients, title= 'Clients ECDF Path vs Shortest Path' )
	reached_non_clients = final_df[(final_df.reached==True) & (final_df.proxy != final_df.destination)]
	plotECDFPathVSShortestPath(reached_non_clients, title = 'Non-Clients ECDF Path vs Shortest Path' )


if __name__ == '__main__' :
	#drawShortestPaths('4892')
	drawPathLossess(['7857','3982','4892','5417'])
