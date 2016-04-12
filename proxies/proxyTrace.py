

from guifiAnalyzer.db.infrastructure import InfraDB
from guifiAnalyzer.traffic.snpservicesClient import snpRequest, snpLiveTracerouteParser
from guifiAnalyzer.vis.proxiesDB import createGraph, drawGraph
from getIPNetworks import invertListDic

import networkx as nx
import pandas as pd
from matplotlib import pyplot as plt
import numpy as np
randomState = np.random.RandomState()

import random
from collections import Counter, defaultdict

import cPickle as pickle

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

read_traceroute = {
	'7857':'7857_traceroute.out',
	#'5417':'5417_traceroute.out',
	#'3982':'my_node_traceroute.out',
	#'4892':'4892_traceroute.out'
}

proxy_pair = {
	'3982':('7193','11697')
}

file_dir = os.path.join( os.getcwd(), 'guifiAnalyzerOut', 'results', 'proxyTrace')
helper_dir = os.path.join( os.getcwd(), 'guifiAnalyzer', 'proxies', 'helpers')
getIPNetworks_dir = os.path.join( os.getcwd(), 'guifiAnalyzerOut', 'results', 'getIPNetworks')


def parseLiveTraceroute(data, node_per_ip):
	output = snpLiveTracerouteParser(data)
	#pprint(output)
	traceroute = {}
	hop = 0
	for counter, data in output.iteritems():
		node = node_per_ip[data['ip']][0] if data['ip'] in node_per_ip else None
		#Fix ip 10.139.250.41 that probably belongs to node 9215
		if data['ip'] == '10.139.250.41':
			#node = '9215'
			node = '4891'
		if data['ip'] == '10.140.200.130' or data['ip'] == "10.38.141.65" or data['ip'] =="10.138.49.1"  or data['ip'] == "10.138.0.1" or data['ip'] == "10.138.61.129":
			node = '3982'

		if hop in traceroute and traceroute[hop]['node'] == node:
			continue
		else:
			hop += 1
			traceroute[hop] = data
			traceroute[hop]['node'] = node

	#pprint(traceroute)
	return traceroute

def calculatePathLenghts(proxy, router, traceroute, G):
	pprint(traceroute)
	distance = -1
	reached = False
	delay = float('NaN')
	if router == traceroute[max(traceroute.keys())]['node']:
		reached = True
		distance = max(traceroute.keys())
		delay = traceroute[max(traceroute.keys())]['avg_rtt']
	else:
		print 'Did not reach destination'

	if proxy == traceroute[1]['node'] and distance != -1:
		print 'First hop is local'
		distance -= 1

	
	print "The distance between proxy %s and router %s is %s hops" % (proxy, router, distance)
	shortest_path = nx.shortest_path(G, source=proxy, target=router)
	shortest_path_length = len(shortest_path)-1
	print "Shortest path between proxy %s and router %s is %s hops" % (proxy, router, shortest_path_length)
	return (distance, reached, shortest_path_length, delay)

def calculateLinks(proxy, traceroute):
	links = []
	src = 1
	dst = 2
	while dst <= max(traceroute.keys()):
		node_src = traceroute[src]['node'] 
		node_dst = traceroute[dst]['node']
		if node_src != node_dst:
			node_a = min(node_src,node_dst)
			node_b = max(node_src,node_dst)
			links.append((node_a,node_b))
			src += 1
			dst += 1
	#pdb.set_trace()
	#for (a,b) in links:
		#if a == None or b == None:
		#	pdb.set_trace()
	return links


def parseTracerouteFilePerRouter(t_file):
	traceroutes = {}
	with open(t_file,'r') as fi:
		router_ip = ''
		for line in fi:
			split_line = line.split(' ')
			if split_line[0] == 'traceroute':
				router_ip = split_line[3].rstrip('),').lstrip('(')
				traceroutes[router_ip] = [line]
			else:
				traceroutes[router_ip].append(line)
	return traceroutes


def averageInt(a,b):
	i = (a+b)/2
	return int(round(i))

def findShortestPaths(proxy):
	G, ips_per_node, router_ips_per_node = createGraph(root, core)
	node_per_ip = invertListDic(ips_per_node)
	#for router,ips in router_ips_per_node.iteritems():
	#	data = snpRequest(ip=proxy_graph[proxy],command='liveping', 
	#					args={'ip':ips[0],'count':3})
	if proxy in read_traceroute:
		tr_path = os.path.join(helper_dir,read_traceroute[proxy])
		traceroutes = parseTracerouteFilePerRouter(tr_path)

	shortest_paths = []
	links = {}
	for router, ips in router_ips_per_node.iteritems():
		# If destination and source are the same
		if router == proxy:
			shortest_paths.append({'router':router,
								'path':0, 
								'reached':True,
								'delay':0, 
								'shortest_path':0})
		else:
			# If proxy is working and colocated with a graphserver
			if proxy in proxy_graph:
				reached = False
				count = 0
				while reached==False and count < len(ips):
					print 'EFFORT %s' % count
					data = snpRequest(ip=proxy_graph[proxy], command='livetraceroute', 
										args={'ip':ips[count], 'count':3}, timeout=60)
					data = data.split('\n')
					traceroute = parseLiveTraceroute(data, node_per_ip)
					distance, reached, shortest_path_length, delay = calculatePathLenghts(proxy, router, traceroute, G)
					count += 1
				links[router] = calculateLinks(proxy, traceroute)
			# if proxy is not colocated with a graphserver and we have
			# obtained manually the traceroute
			elif proxy in read_traceroute:
				data = traceroutes[ips[0]]
				traceroute = parseLiveTraceroute(data, node_per_ip)
				distance, reached, shortest_path_length, delay = calculatePathLenghts(proxy, router, traceroute, G)
				links[router] = calculateLinks(proxy, traceroute)
			# the weird case of the moved proxies in Llucanes where a new id represents two old ones
			elif proxy in proxy_pair:
				# Use random select of proxy
				proxy_list = list(proxy_pair[proxy])
				help_proxy = random.choice(proxy_list)
				reached = False
				count = 0
				while reached==False and count < len(ips):
					data = snpRequest(ip=proxy_graph[help_proxy], command='livetraceroute', 
										args={'ip':ips[count], 'count':3}, timeout=60)
					data = data.split('\n')
					traceroute = parseLiveTraceroute(data, node_per_ip)
					distance, reached, shortest_path_length, delay = calculatePathLenghts(help_proxy, router, traceroute, G)
					count += 1
				links[router] = calculateLinks(help_proxy, traceroute)


				#information from old logs

				# Use the averages
				# Does not help when we have to find the exact paths used
				if False: 
					proxy1, proxy2 = proxy_pair[proxy]
					data1 = snpRequest(ip=proxy_graph[proxy1], command='livetraceroute', 
										args={'ip':ips[0], 'count':3}, timeout=60)
					data2 = snpRequest(ip=proxy_graph[proxy2], command='livetraceroute', 
										args={'ip':ips[0], 'count':3}, timeout=60)
					data1 = data1.split('\n')
					data2 = data2.split('\n')
					traceroute1 = parseLiveTraceroute(data1, node_per_ip)
					traceroute2 = parseLiveTraceroute(data2, node_per_ip)
					distance1, reached1, shortest_path_length1, delay1 = calculatePathLenghts(proxy1, router, traceroute1, G)
					distance2, reached2, shortest_path_length2, delay2 = calculatePathLenghts(proxy2, router, traceroute2, G)
					# If both of them reached or didnt reach then just take
					# the average
					# Have to think about the path in that case
					if reached1 == reached2:
						distance = averageInt(distance1, distance2) + 1
						shortest_path_length = averageInt(shortest_path_length1, shortest_path_length2) + 1
						reached = reached1
					# If one of them reached while the other not keep the one
					# that reached
					else:
						distance = distance1 if reached1 else distance2
						shortest_path_length = shortest_path_length1 if reached1 else shortest_path_length2
						reached = reached1 if reached1 else reached2
			
			shortest_paths.append({'router':router,
									'path':distance, 
									'reached':reached, 
									'delay': delay,
									'shortest_path':shortest_path_length})


	fil = os.path.join(file_dir, proxy+'_edges_list')
	with open(fil, 'wb') as f:
		pickle.dump(links, f)

	
	df_shortest_paths = pd.DataFrame(shortest_paths)
	fil = os.path.join(file_dir, proxy+'_paths')
	df_shortest_paths.to_pickle(fil)
	
	return df_shortest_paths, links
	#return router_ips_per_node


def plotProxyToRoutersShortestPathvsRealPath(df):
	df[['shortest_distance', 'distance']].sort_values('shortest_distance').plot(kind='bar',
																title='Proxy to Routers Shortest vs Real Path')
	plt.show()
	raw_input("End")




def plotProxyToNodesShortestPathvsRealPath(df,title):
	df = df[df.reached==True]
	if False:
		grps = df.groupby('proxy')
		for  n,grp in grps:
			#grp = grp[['shortest_distance', 'distance']].sort_values('shortest_distance')
			ecdf1 = getECDF(grp['shortest_distance'])
			ax = ecdf1.plot(legend=True)
			ax.set_xlabel('Distance in Hops')
			ax.set_ylabel('ECDF')
			ecdf2 = getECDF(grp['distance'])
			title = n+" ECDF shortest distance vs real distance from client to proxy"
			ecdf2.plot(legend=True, title = title)
			#grp.plot(legend=True)
			plt.show()
			raw_input("End")

	ecdf1 = getECDF(df['shortest_distance'])
	ecdf2 = getECDF(df['distance'])
	ax = ecdf1.plot(legend=True)
	ax.set_xlabel('Distance in Hops')
	ax.set_ylabel('ECDF')
	ecdf2.plot(legend=True, title = "ECDF shortest distance vs real distance from client to proxy")
	raw_input("End")
	#df = df[['shortest_distance', 'distance']].sort_values('shortest_distance')
	#df.plot(title=title)
	#plt.show()
	#raw_input("End")


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



def combineLogTraceroute(df_proxy_clients, shortest_paths):
	proxy_clients = df_proxy_clients.to_dict()
	#shortest_paths = {p:df.to_dict() for p,df in shortest_paths.iteritems()}

	data = []

	proxy_clients_nodes = proxy_clients['nodeId']
	for i, nodeId in proxy_clients_nodes.iteritems():
		router = proxy_clients['router'][i]
		proxy = proxy_clients['proxy'][i]
		bytes = proxy_clients['bytes'][i]
		elapsed = proxy_clients['elapsed'][i]
		if proxy == 'my_proxy':
			proxy = '3982'
		for destination, paths in shortest_paths.iteritems():
			temp = paths[paths.router==router]
			if temp.empty:
				continue
			reached = temp['reached'].item()
			# Routers
			if nodeId == router:
				distance = temp['path'].item()
				shortest_distance = temp['shortest_path'].item()
			# For clients we use router distance+1
			else:
				distance = temp['path'].item() + 1
				shortest_distance = temp['shortest_path'].item() + 1
			
			delay = temp['delay'].item()
			if destination == router:
				delay = 0

			data.append({'nodeId': nodeId,
						'router': router,
						'proxy' : proxy,
						'bytes' : bytes,
						'elapsed': elapsed,
						'destination' : destination,
						'reached' : reached,
						'delay' : delay,
						'distance': distance,
						'shortest_distance' : shortest_distance})

	return pd.DataFrame(data)

	



def getBetweeness(links_proxies, G, final_df):
	df = final_df[final_df.reached==True]
	df = df[df.destination==df.proxy].set_index('nodeId')
	proxies_routers_count_df = df.groupby(['proxy','router']).size()


	# Keep only the links actually used and add them as many times
	# they are used
	links = []
	for proxy, dic in links_proxies.iteritems():
		for router, path_links in dic.iteritems():
			if proxy in proxies_routers_count_df.index and router in proxies_routers_count_df.loc[proxy].index:
				times = proxies_routers_count_df.loc[proxy].loc[router]
				for i in range(times):
					links.extend(path_links)



	#links = []
	#for l in links_proxies.values():
	#	links.extend(l)

	#proxy_clients = df_proxy_clients.set_index('nodeId').to_dict()
	#proxies = list(set(proxy_clients['proxy'].values()))
	#routers = list(set(proxy_clients['router'].values()))
	#clients = list(set(proxy_clients['router'].keys()))
	#all_nodes= list(clients.extend(routers).extend(proxies))

	#Keep in the graph only used nodes
	delete_nodes = []
	for node,data in G.nodes(data=True):
		if ('type' not in data) or (data['type'] == 'client' and data['proxies'] == 'N' and data['isproxy']==0 and data['isrouter']==0):
			delete_nodes.append(node)
	G.remove_nodes_from(delete_nodes)


	#add weight 0.1 to all edges
	# non-zero to not distract betweeness algorithm
	for (a,b) in G.edges():
		G[a][b]['weight'] = 0.1
	none_links = 0
	for src, dst in links:
		if src != None and dst != None:
			try:
				if 'weight' in G[src][dst]:
					G[src][dst]['weight'] += 1
				else:
					G[src][dst]['weight'] = 0
			except Exception, e:
				# It seems that traceroute includes a link that does 
				# not exist in the cnml db
				G.add_edge('4206', '4982', 
                        {'id': '1', 
                        'type': 'wds' 
                        #'direction': 'b',
                        #'group': link['status'],
                        })
				if 'weight' in G[src][dst]:
					G[src][dst]['weight'] += 1
				else:
					G[src][dst]['weight'] = 0
				#print e
				#pdb.set_trace()
		else:
			none_links += 1

	#pdb.set_trace()



	# Keep Backbone links
	edges_in_backbone =[]
	for a,b in G.edges():
		if len(G.neighbors(a))<=1 or len(G.neighbors(b))<=1:
			if  (not G.node[a]['isproxy'] and not G.node[a]['isrouter']) or (not  G.node[b]['isproxy'] and not G.node[b]['isrouter']):
				edges_in_backbone.append((a, b))
	G.remove_edges_from(edges_in_backbone)
	G = max(nx.connected_component_subgraphs(G), key=len)

	#edges_to_remove = []
	#for a,b,data in G.edges(data=True):
	#	if 'weight' not in data or data['weight']==0:
	#		edges_to_remove.append((a, b))
	#G.remove_edges_from(edges_to_remove)

	
	if False:
		# Draw Backbone graph using bytes as weight
		for (a,b) in G.edges():
			G[a][b]['weight'] = 0.1 
		bytes_per_link = caluclateBytesPerLink(final_df,links_proxies)
		for link,bytes in bytes_per_link.iteritems():
			src = link.split('-')[0]
			dst = link.split('-')[1]
			print src,dst
			if src in G and dst in G[src]:
				G[src][dst]['weight'] = bytes

		drawGraph(G, 8346, '')
		return
	
	tr_edge_between = nx.edge_betweenness_centrality(G, weight='weight')
	edge_between = nx.edge_betweenness_centrality(G)



	#pprint(tr_edge_between)
	#pprint(edge_between)
	if False:
		all_pairs_shortest_paths = nx.all_pairs_shortest_path(G).values()
		all_shortest_paths = []
		for p in all_pairs_shortest_paths:
			all_shortest_paths.extend(p.values())
		links_in_shortest_paths = {l:0 for l in links}
		for src,dst in links:
			for p in all_shortest_paths:
				if src in p:
					pos = p.index(src)
					if ((pos-1) >=0 and p[pos-1] == dst) or ((pos+1) <len(p)-1 and p[pos+1] == dst):
						links_in_shortest_paths[(src,dst)] += 1


	betweeness = []
	for (a,b),between in edge_between.iteritems():
		#min_paths = 0
		#if (a,b) in links_in_shortest_paths:
		#	min_paths = links_in_shortest_paths[(a,b)] 
		#elif (b,a) in links_in_shortest_paths:
		#	min_paths =  links_in_shortest_paths[(b,a)]
			
		betweeness.append({'link': a+b,
							#'paths': G[a][b]['weight'],
							#'min_paths': min_paths, 
							'edge_betweeness' : between,
							'weighted_edge_betweeness' : tr_edge_between[(a,b)]})


	return pd.DataFrame(betweeness)

def plotBetweeness(dfs):
	#df_betweeness[['edge_betweeness','weighted_edge_betweeness']].plot()
	#df_betweeness.plot(x='edge_betweeness',y='weighted_edge_betweeness', kind='scatter', style='x', color='r')
	plt.figure()
	i=1
	for title,df_betweeness in dfs.iteritems():
		plt.subplot(2,2,i)
		plt.scatter(df_betweeness['edge_betweeness'],df_betweeness['weighted_edge_betweeness'],s=40,marker='x')
		
		#plt.legend = ''
		
		# Linear Reggression
		# Following: http://stamfordresearch.com/linear-regression-using-pandas-python/
		
		# Get the linear models
		lm_original = np.polyfit(df_betweeness['edge_betweeness'], df_betweeness['weighted_edge_betweeness'], 1)
		# calculate the y values based on the co-efficients from the model
		r_x, r_y = zip(*((i, i*lm_original[0] + lm_original[1]) for i in df_betweeness['edge_betweeness']))
		# Put in to a data frame, to keep is all nice
		legend = 'y='+str(lm_original[0])+'x + '+str(lm_original[1])
		lm_original_plot = pd.DataFrame({
			'edge_betweeness' : r_x,
			'weighted_edge_betweeness' : r_y})
		line, = plt.plot(r_x,r_y, label=legend)
		plt.legend(handles=[line])
		plt.xlabel('Edge Betweeness', fontsize=18)
		plt.ylim(-0.1,0.6)
		plt.ylabel('Weighted Edge Betweeness', fontsize=18)
		plt.title(title)
		plt.show()
		i += 1
	raw_input("End")

def plotBetweenessECDF(dfs):
	plt.figure()
	i=1
	for title,df_betweeness in dfs.iteritems():
		plt.subplot(2,2,i)
		ecdf_bet = getECDF(df_betweeness['edge_betweeness'])
		ecdf_bet.plot(legend=True)
		plt.show()
		ecdf_bet1 = getECDF(df_betweeness['weighted_edge_betweeness'])
		ecdf_bet1.plot(legend=True)
		plt.title(title)
		plt.show()
		plt.xlim(0,0.5)
		i +=1
	raw_input("End")


def plotECDFDelays(final_df):
	clients_df = final_df[final_df.proxy == final_df.destination].set_index('nodeId')
	clients_df = clients_df[clients_df.reached==True]
	grps = clients_df.groupby('proxy')
	for  n,grp in grps:
		grp[n] = grp['delay']
		ecdf = getECDF(grp[n])
		ecdf.plot(legend=True)
		plt.show()
	raw_input("End")



def caluclateBytesPerLink(final_df,links_proxies):
	all_links = [l for j in links_proxies.values() for l in j.values()]
	all_links = sum(all_links,[])
	bytes_per_link = {a+'-'+b:0 for (a,b) in all_links if a!=None and b!=None}

	final_df = final_df[final_df.reached == True]
	final_df = final_df[final_df.router != final_df.proxy]
	final_df = final_df[final_df.destination==final_df.proxy]
	for i in final_df.index:
		router = final_df.loc[i]['router']
		proxy = final_df.loc[i]['proxy']
		bytes = final_df.loc[i]['bytes']
		for (a,b) in links_proxies[proxy][router]:
			if a!=None and b!=None:
				bytes_per_link[a+'-'+b] += bytes 
	return bytes_per_link

def drawLinksBytesECDF(final_df,links_proxies):
	all_links = [l for j in links_proxies.values() for l in j.values()]
	all_links = sum(all_links,[])
	bytes_per_link = caluclateBytesPerLink(final_df,links_proxies)
	
	non_zero_bytes_per_links = {l:b for l,b in bytes_per_link.iteritems() if b>0}
	stats_df = pd.DataFrame({'Total Links': len(set(all_links)),
								'Defined Links': len(set(bytes_per_link)),
								'Non-Zero Links': len(set(non_zero_bytes_per_links))}, index=[0])
	columns = stats_df.columns[stats_df.ix[stats_df.last_valid_index()].argsort()]
	columns = list(reversed(columns))
	stats_df = stats_df[columns]

	#stats_df = stats_df.T
	#stats_df.plot(kind='bar', legend=True)
	#plt.show()
	#raw_input("End")

	df = pd.DataFrame(pd.Series(bytes_per_link, name='Gbytes'))
	ecdf = getECDF(df['Gbytes']/1000000000)
	plt.figure()
	ax=ecdf.plot(legend=False, title="ECDF Total GBytes Per Link")
	ax.set_xlabel('GBytes')
	ax.set_ylabel('ECDF')
	plt.show()
	raw_input("End")


def drawComparativeLinksBytesECDF(dfs,links_proxies):
	all_links = [l for j in links_proxies.values() for l in j.values()]
	all_links = sum(all_links,[])
	plt.figure()
	for name,df in dfs.iteritems():
		bytes_per_link = caluclateBytesPerLink(df,links_proxies)


		df1 = pd.DataFrame(pd.Series(bytes_per_link, name='Gbytes'))
		ecdf = getECDF(df1['Gbytes']/1000000000)
		ecdf.name = name
		ecdf.plot(legend=True)
	plt.title("ECDF Total GBytes Per Link")
	plt.xlabel('GBytes')
	plt.ylabel('ECDF')
	plt.show()
	raw_input("End")


def drawComparativeTotalLinksBytes(dfs,links_proxies):
	all_links = [l for j in links_proxies.values() for l in j.values()]
	all_links = sum(all_links,[])
	total_links_bytes = []
	for name,df in dfs.iteritems():
		bytes_per_link = caluclateBytesPerLink(df,links_proxies)
		print "Number of links: %s" % len(bytes_per_link)
		s1 = pd.Series(bytes_per_link, name=name)
		s1 = s1/1000000
		#df1.plot(legend=True)
		total_links_bytes.append(s1)
	total_links_bytes_df = pd.concat(total_links_bytes, axis=1)
	total_links_bytes_df = total_links_bytes_df[(total_links_bytes_df.T != 0).any()]
	total_links_bytes_df = total_links_bytes_df.reset_index()
	total_links_bytes_df[dfs.keys()].plot(legend=True, logy=True)
	plt.title("Total Bytes Per Link")
	plt.xlabel('Links')
	plt.ylabel('Bytes')
	plt.show()
	raw_input("End")


def getLinksBytesTS(final_df,links_proxies, df_bytes_ts_per_user, title):
	final_df = final_df[final_df.router != final_df.proxy]
	final_df = final_df.set_index('nodeId')
	final_df.drop_duplicates(inplace = True)
	#df_bytes_ts_per_user.index = pd.DatetimeIndex(df_bytes_ts_per_user.index)
	#idx = pd.date_range(df_bytes_ts_per_user.index[0],df_bytes_ts_per_user.index[-1],freq="60min")
	#df_bytes_ts_per_user = df_bytes_ts_per_user.reindex(idx,fill_value=0)

	links_bytes_ts = {}
	for nodeId in final_df.index:
		if nodeId in df_bytes_ts_per_user.columns:
			# If there is a time series for the node
			if isinstance(final_df.loc[nodeId],pd.DataFrame):
				# If node is client of more than one proxies
				df = final_df.loc[nodeId].reset_index()
				size = len(df.index)
				# for each line where this node is client
				for i in df.index:
					router = df.loc[i]['router']
					proxy = df.loc[i]['proxy']
					links = links_proxies[proxy][router]
					for (src,dst) in links:
						if src != None and dst != None:
							link_name = src+'+'+dst
							if isinstance(df_bytes_ts_per_user[nodeId], pd.DataFrame):
								# In case node exists twice in the df.
								# But doesnt thi mean that he should exist twice also in the df?
								# Only if we have tracerouter measurements for him
								df1 = df_bytes_ts_per_user[nodeId].sum(axis=1)/size
							else:
								df1 = df_bytes_ts_per_user[nodeId]/size

							if link_name in links_bytes_ts:
								#print '1'
								#pdb.set_trace()
								links_bytes_ts[link_name] = links_bytes_ts[link_name].add(df1, fill_value=0)
								if isinstance(links_bytes_ts[link_name], pd.DataFrame):
									print '1'
									pdb.set_trace()
							else:
								#print '2'
								#pdb.set_trace()

								links_bytes_ts[link_name] = df1/size
								links_bytes_ts[link_name].name = link_name
								if isinstance(links_bytes_ts[link_name], pd.DataFrame):
									print '2'
									pdb.set_trace()
						else:
							print 'FOUND ONE'
			else:
				# If node is client of one proxy
				router = final_df.loc[nodeId]['router']
				proxy = final_df.loc[nodeId]['proxy']
				links = links_proxies[proxy][router]
				for (src,dst) in links:
					if src != None and dst != None:
						link_name = src+'+'+dst
						if isinstance(df_bytes_ts_per_user[nodeId], pd.DataFrame):
							# In case node exists twice in the df.
							# But doesnt thi mean that he should exist twice also in the df?
							# Only if we have tracerouter measurements for him
							df1 = df_bytes_ts_per_user[nodeId].sum(axis=1)
						else:
							df1 = df_bytes_ts_per_user[nodeId]

						if link_name in links_bytes_ts:
							links_bytes_ts[link_name] = links_bytes_ts[link_name].add(df1, fill_value=0)
							if isinstance(links_bytes_ts[link_name], pd.DataFrame):
								print '3'
								pdb.set_trace()
						else:
							links_bytes_ts[link_name] = df1
							links_bytes_ts[link_name].name = link_name
							if isinstance(links_bytes_ts[link_name], pd.DataFrame):
								print '4'
								pdb.set_trace()
					else:
						print 'FOUND ONE'
		else:
			print 'Node %s has no time series' % nodeId
	df_links_bytes_ts = pd.concat(links_bytes_ts.values(),axis=1)	
	print '%s \nSum: %s' % (title,df_links_bytes_ts.sum(axis=1).sum())

	return df_links_bytes_ts

def drawLinksBytesTS(df_links_bytes_ts):
	plt.figure()
	df_links_bytes_ts.plot(legend=False,logy=True, title=title)
	plt.show()
	raw_input("End")

def getMinDelayDF(final_df):
	min_delay_df = final_df[final_df.reached==True]
	min_delay_idx = min_delay_df.groupby(['nodeId','proxy'])['delay'].idxmin(skipna=True)
	min_delay_df = min_delay_df.loc[min_delay_idx]
	min_delay_df['proxy'] = min_delay_df['destination']
	min_delay_df = min_delay_df.dropna()

	return min_delay_df

def getMaxDelayDF(final_df):
	max_delay_df = final_df[final_df.reached==True]
	max_delay_idx = max_delay_df.groupby(['nodeId','proxy'])['delay'].idxmax(skipna=True)
	max_delay_df = max_delay_df.loc[max_delay_idx]
	max_delay_df['proxy'] = max_delay_df['destination']
	max_delay_df = max_delay_df.dropna()

	return max_delay_df

def getMinHopsDF(final_df):
	min_hops_df = final_df[final_df.reached==True]
	min_hops_idx = min_hops_df.groupby(['nodeId','proxy'])['distance'].idxmin(skipna=True)
	min_hops_df = min_hops_df.loc[min_hops_idx]
	min_hops_df['proxy'] = min_hops_df['destination']
	min_hops_df = min_hops_df.dropna()

	return min_hops_df

def getMaxHopsDF(final_df):
	max_hops_df = final_df[final_df.reached==True]
	max_hops_idx = max_hops_df.groupby(['nodeId','proxy'])['distance'].idxmax(skipna=True)
	max_hops_df = max_hops_df.loc[max_hops_idx]
	max_hops_df['proxy'] = max_hops_df['destination']
	max_hops_df = max_hops_df.dropna()

	return max_hops_df


def dfRandomRow(df):
	#if '7857' in pd.unique(df.proxy.ravel()).tolist():
		# Give priority to 7857 because it does not exist in many results
	#	return df[df.destination=='7857']
	#else:
	#	return df.sample(n=1, random_state=randomState)
	return df.sample(n=1, random_state=randomState)

def getRandomProxyDF(final_df):
	# Choose proxies from a specific distribution
	# get list of unique proxies
	proxies = pd.unique(final_df.proxy.ravel()).tolist()
	#random_proxy_df = final_df.copy()
	random_proxy_df = final_df[final_df.reached == True]
	random_proxy_df = random_proxy_df.groupby(['nodeId','proxy']).apply(dfRandomRow)
	random_proxy_df['proxy'] = random_proxy_df['destination']
	random_proxy_df = random_proxy_df.reset_index(level=[0,1],drop=True)
	random_proxy_df = random_proxy_df.dropna()

	return random_proxy_df

def countNodes(df):
	return len(pd.unique(df.nodeId.ravel()).tolist())

def drawProxySelectionFrequency(final_df, random_proxy_df, min_delay_df, min_hops_df):
	temp = final_df[final_df.reached == True]
	temp = temp[temp.proxy == temp.destination]
	freq1 = temp.groupby('proxy').size()/temp['proxy'].count()
	freq2 = random_proxy_df.groupby('proxy').size()/random_proxy_df['proxy'].count()
	freq3 = min_delay_df.groupby('proxy').size()/min_delay_df['proxy'].count()
	freq4 = min_hops_df.groupby('proxy').size()/min_hops_df['proxy'].count()
	freq = pd.DataFrame({'Current Situation':freq1,
						'Random Proxy Selection':freq2,
						'Min Delay Proxy':freq3,
						'Min Hops Proxy':freq4})
	freq.plot(kind='bar',title='Frequency of proxy selection')
	plt.ylabel('Frequency')
	plt.show()
	raw_input("End")

	abs_freq1 = temp.groupby('proxy').size()
	abs_freq2 = random_proxy_df.groupby('proxy').size()
	abs_freq3 = min_delay_df.groupby('proxy').size()
	abs_freq4 = min_hops_df.groupby('proxy').size()
	abs_freq = pd.DataFrame({'Current Situation':abs_freq1,
							'Random Proxy Selection':abs_freq2, 
							'Min Delay Proxy':abs_freq3, 
							'Min Hops Proxy':abs_freq4})
	abs_freq.plot.box(title='Boxplot of Absolute Frequency of proxy selection')
	plt.ylabel('Absolute Frequency')
	plt.show()
	raw_input("End")

	if False:
		temp1 = final_df[final_df.reached == True]
		#Frequency
		#freq5 = temp1.groupby('proxy').size()/temp1['proxy'].count()
		#freq6 = final_df.groupby('proxy').size()/final_df['proxy'].count()
		#Absolute
		freq5 = temp1.groupby('destination').apply(countNodes)
		freq6 = final_df.groupby('destination').apply(countNodes)
		freq = pd.DataFrame({'All Measurements':freq6,'Succesfull measurements':freq5})
		freq.plot(kind='bar', title='Understanding Measurements')
		plt.ylabel('Frequency')
		plt.show()
		raw_input("End")


def drawBytesPerHour(dfs):
	plt.figure()
	for name,df in dfs.iteritems():
		df = df.resample('60Min',how='sum')
		df['hour'] = df.index.hour
		df = df.groupby('hour').sum()
		df = df.sum(axis=1)
		df.name = name
		df.plot(legend=True, logy=True)
		print df.sum()
	plt.show()
	raw_input("End")


def drawComparativeBytesElapsedPerProxy(dfs,column, name):
	results = []
	for title, df in dfs.iteritems():
		bytes = df.groupby('proxy')[column].sum()
		bytes.name = title
		results.append(bytes)
	results_df = pd.concat(results, axis=1)
	results_df.plot.box(logy=True)
	plt.ylabel(name)
	title = 'Proxy '+name+' Boxplot of various approaches'
	plt.title(title)
	plt.show()
	raw_input("End")
	results_df = results_df.T
	results_df.plot(kind='bar',legend=True,logy=True)
	plt.ylabel(name)
	title = name+' Per Proxy Per approach'
	plt.title(title)
	plt.xticks(rotation=90)
	plt.show()
	raw_input("End")
	#pdb.set_trace()

def drawComparativeSpeedPerProxy(dfs):
	results = []
	for title, df in dfs.iteritems():
		df['speed'] = df.bytes/df.elapsed.replace({ 0 : np.nan })
		#pdb.set_trace()
		#speed = df.groupby('proxy')['speed'].sum()
		speed = df['speed']
		speed.name = title
		pdb.set_trace()
		results.append(speed)
	results_df = pd.concat(results, axis=1)
	results_df.plot.box(logy=True)
	plt.ylabel('Bytes/Sec')
	plt.title('Proxy Speed Boxplot of various approaches')
	plt.show()
	raw_input("End")
	#pdb.set_trace()


def drawShortestPaths(proxies):
	fil = os.path.join(getIPNetworks_dir, 'df_proxy_clients')
	df_proxy_clients = pd.read_pickle(fil)
	fil = os.path.join(getIPNetworks_dir, 'df_bytes_ts_per_user')
	df_bytes_ts_per_user = pd.read_pickle(fil)
	shortest_paths = {}
	links_proxies = {}
	G, _, _= createGraph(root, core)
	for proxy in proxies:
		fil = os.path.join(file_dir, proxy+'_paths')
		if  not os.path.isfile(fil):
			p, l = findShortestPaths(proxy)
			shortest_paths[proxy] = p
			links_proxies[proxy] = l
		else:
			shortest_paths[proxy] = pd.read_pickle(fil)
			edges_file = os.path.join(file_dir, proxy+'_edges_list')
			with open(edges_file, 'rb') as f:
				links_proxies[proxy] = pickle.load(f)



	final_df = combineLogTraceroute(df_proxy_clients, shortest_paths)


	current_df = final_df[final_df.reached==True]
	current_df = current_df[current_df.destination==current_df.proxy]

	#plotECDFDelays(final_df)

	#drawLinksBytesECDF(final_df,links_proxies)

	final_link_bytes_df = getLinksBytesTS(current_df,links_proxies, df_bytes_ts_per_user, 'current')

	min_delay_df = getMinDelayDF(final_df)
	min_delay_link_bytes_df = getLinksBytesTS(min_delay_df,links_proxies, df_bytes_ts_per_user, 'min_delay')



	max_delay_df = getMaxDelayDF(final_df)

	min_hops_df = getMinHopsDF(final_df)
	min_hops_link_bytes_df = getLinksBytesTS(min_hops_df,links_proxies, df_bytes_ts_per_user, 'min_hops')

	max_hops_df = getMaxHopsDF(final_df)

	random_proxy_df = getRandomProxyDF(final_df)
	random_proxy_link_bytes_df = getLinksBytesTS(random_proxy_df,links_proxies, df_bytes_ts_per_user, 'random_proxy')

	
	drawProxySelectionFrequency(final_df, random_proxy_df, min_delay_df, min_hops_df)

	drawComparativeLinksBytesECDF({'current':current_df,'random_proxy':random_proxy_df,
									'min_delay':min_delay_df, 'min_hops':min_hops_df}, links_proxies)
	
	drawComparativeTotalLinksBytes({'current':current_df,'random_proxy':random_proxy_df,
									'min_delay':min_delay_df, 'min_hops':min_hops_df}, links_proxies)
	
	drawBytesPerHour({'current':final_link_bytes_df,'random_proxy':random_proxy_link_bytes_df,
						'min_delay':min_delay_link_bytes_df, 'min_hops':min_hops_link_bytes_df})


	drawComparativeBytesElapsedPerProxy({'current':current_df,'random_proxy':random_proxy_df,
									'min_delay':min_delay_df, 'min_hops':min_hops_df}, 'bytes','Load Bytes')

	drawComparativeBytesElapsedPerProxy({'current':current_df,'random_proxy':random_proxy_df,
									'min_delay':min_delay_df, 'min_hops':min_hops_df}, 'elapsed','Elapsed Time')

	drawComparativeSpeedPerProxy({'current':current_df,'random_proxy':random_proxy_df,
									'min_delay':min_delay_df, 'min_hops':min_hops_df})
	
	current_bet = getBetweeness(links_proxies, G, current_df)
	min_delay_bet = getBetweeness(links_proxies, G, min_delay_df)
	min_hops_bet = getBetweeness(links_proxies, G, min_hops_df)
	random_proxy_bet = getBetweeness(links_proxies, G, random_proxy_df)

	plotBetweeness({'Current Edge Betweeness':current_bet,
					'Min Delay Edge Betweeness':min_delay_bet,
					'Min Hops Edge Betweeness': min_hops_bet,
					'Random Proxy Edge Betweeness':random_proxy_bet})

	plotBetweenessECDF({'Current Edge Betweeness':current_bet,
					'Min Delay Edge Betweeness':min_delay_bet,
					'Min Hops Edge Betweeness': min_hops_bet,
					'Random Proxy Edge Betweeness':random_proxy_bet})


	#plotProxyToRoutersShortestPathvsRealPath(df_reached_shortest_paths)

	#nodes_df = final_df[final_df.proxy != proxy].set_index('nodeId')
	#nodes_df = final_df[final_df.proxy == final_df.destination].set_index('nodeId')
	#plotProxyToNodesShortestPathvsRealPath(nodes_df,'Proxy to Non-Clients Shortest vs Real Path')
	
	#clients_df = final_df[final_df.proxy == proxy].set_index('nodeId')
	#plotProxyToNodesShortestPathvsRealPath(clients_df, 'Proxy to  Clients Shortest vs Real Path')

	#reached_clients = final_df[(final_df.reached==True) & (final_df.proxy == final_df.destination)]
	#plotECDFPathVSShortestPath(reached_clients, title= 'Clients ECDF Path vs Shortest Path' )
	#reached_non_clients = final_df[(final_df.reached==True) & (final_df.proxy != final_df.destination)]
	#plotECDFPathVSShortestPath(reached_non_clients, title = 'Non-Clients ECDF Path vs Shortest Path' )




if __name__ == '__main__' :
	#drawShortestPaths('4892')
	drawShortestPaths(['7857','3982','4892','5417'])
	#drawShortestPaths(['5417'])
