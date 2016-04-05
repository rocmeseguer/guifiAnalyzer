# -*- coding: utf-8 -*- 
import os 

import urllib2
from BeautifulSoup import BeautifulSoup

import ipcalc
import random

from guifiAnalyzer.db.infrastructure import InfraDB
from guifiAnalyzer.db.traffic_assistant import TrafficAssistantDB

from guifiAnalyzer.proxies.squidparser.squidparser import SquidParser, log_dir
from guifiAnalyzer.proxies.squidparser.getLogStats import getUsersProxiesBytesLog, getBytesTSPerUser


from pprint import pprint
from collections import Counter

import pickle

import pdb

import pandas as pd
import operator
from matplotlib import pyplot as plt
plt.style.use('ggplot')


URL = "http://guifi.net/es/guifi/menu/ip/ipsearch/"
T_HEADER = "<thead><tr><th>id</th><th>nipv4</th><th>máscara</th><th>interfaz</th><th>dispositivo</th><th>nodo</th> </tr></thead>"
T_NODE = '<th>nodo</th>'
T_DEV = '<th>dispositivo</th>'
SELF_IPS = ['127.0.0.1','127.0.0.0','0.0.0.0']


#trace_output_dir = os.path.join( os.getcwd(), 'guifiAnalyzerOut', 'results','proxyTrace')
#ping_output_dir = os.path.join( os.getcwd(), 'guifiAnalyzerOut', 'results','proxyPing')
output_dir = os.path.join( os.getcwd(), 'guifiAnalyzerOut', 'results','getIPNetworks')

#-------------------- WEB QUERIES  --------------------#

def getIPNodeDeviceWeb(ip):
	"""Consult the guifi web tool where you can find node 
	   and device info based on an IP
	"""
	print 'Finding info for ip %s' % ip
	url = URL + ip
	req = urllib2.Request(url)
	resp = urllib2.urlopen(req)
	soup = BeautifulSoup(resp)
	tables = soup.findAll('table', attrs={'class':'sticky-enabled'})
	table = None
	for tab in tables:
		if str(tab.thead) == T_HEADER:
			table = tab
	if table == None:
		print 'NO DATA'
		return None
	headers1 = table.findAll('th')
	if headers1:
		headers = [str(h) for h in headers1]
		results = table.tbody.tr.findAll('td')
		#results = [str(s) for s in results1]
		node_index = headers.index(T_NODE)
		dev_index = headers.index(T_DEV)
		node_id = results[node_index].text.split('-')[0]
		device_id = results[dev_index].text.split('-')[0]
		print "Node id: %s" % node_id
		print "Device id: %s" % device_id
		return (node_id, device_id)
	else:
		print 'NO DATA'
		print "Node id: None"
		print "Device id: None "
		return None


#-------------------- DB QUERIES  --------------------#


def getDBZoneProxies(devices, services, logs_path):
	"""Define the proxies working set. That is the proxies 
	   that exist in the zone and also a log file is provided
	"""
	proxies = []
	files = [f for f in os.listdir(logs_path) if os.path.isfile(os.path.join(logs_path, f))]
	for f in files:
		service_id = f.split('_')[0]
		if service_id in services  and services[service_id]['parentDevice'] in devices:
			proxies.append(service_id)
	return list(set(proxies))


def getDBZoneIps(devices, ifaces):
	"""Return a list of the unique ips in the zone
	"""
	device_ips = [i['mainipv4'] for i in devices.values()]
	iface_ips = [i['ipv4'] for i in ifaces.values()]

	zone_ips = list(set(device_ips) | set(iface_ips))
	zone_ips = [i for i in zone_ips if i != '']
	if None in zone_ips:
		zone_ips.remove(None)
	
	ip_counter = list(set(zone_ips))
	print 'Total Interfaces: %s' % len(devices)
	print 'Total Unique IPs: %s' % len(ip_counter)
	return zone_ips


#NEEDS Improvement
def getIPDeviceDB(ip,devices, ifaces, radios):
	"""Given an IP this function return the device this
	   ip belongs to, if any in the studied zone
	"""

	# Search first in devices directly
	for _, dev in devices.iteritems():
		if dev['mainipv4'] == ip:
			return dev

	for _, iface in ifaces.iteritems():
		#pdb.set_trace()
		if iface['ipv4'] == ip:
			if type(iface['parent']) is dict:
				radio = radios[(iface['parent']['device'], iface['parent']['radio'])]
				if radio:
					return devices[radio['parentDevice']]
				else:
					return None
			else:
				if iface['parent'] in devices:
					return devices[iface['parent']]
				else:
					return None



def getDBDeviceNetworks(devices, ifaces, radios):
	"""Returns a dictionary with all the working network 
	   devices and the corresponding networks as they are
	   found in the DB created by the CNML
	"""
	zone_ips = getDBZoneIps(devices, ifaces)	
	# calculate devices of ips
	ips_per_device = {}
	for ip in zone_ips:
		dev = getIPDeviceDB(ip, devices, ifaces, radios)['_id']
		if dev in ips_per_device:
			ips_per_device[dev].append(ip)
		else:
			ips_per_device[dev] = [ip]
	#ips_per_device = {getIPDeviceDB(ip, devices, radios, ifaces)['_id']:ip for ip in zone_ips}
	#print ip_devices
	# calulate for each device in which network it belongs
	device_networks = {dev:map(lambda x: str(ipcalc.Network(x+'/27').network()), ips) for dev, ips in ips_per_device.iteritems()}
	print ' %s' % len(device_networks)

	return device_networks, ips_per_device


#-------------------- Proxy Log QUERIES  --------------------#


def getLogNetworksNUsers(proxy_id):
	'''Reads the file fil in logs_path which already
	   must contain the set of unique ip /27 subnets. Keeps only
	   10.*.*.* subnets
	'''
	#Check if file exists
	proxy_nets_fil = os.path.join(log_dir, proxy_id+'_nets')
	proxy_nets_users_fil = os.path.join(log_dir, proxy_id+'_nets_users')
	if os.path.isfile(proxy_nets_fil) and os.path.isfile(proxy_nets_users_fil):
		#If exists read
		with open(proxy_nets_fil, 'rb') as f:
			proxy_nets = pickle.load(f)
		with open(proxy_nets_users_fil, 'rb') as f:
			proxy_nets_users = pickle.load(f)
	else:
		#If not calculate
		parser = SquidParser(proxy_id)
		proxy_nets = parser.ips
		# Filter out non 10.* proxy_nets
		proxy_nets = [ip for ip in proxy_nets if ip.split('.')[0] == '10']
		proxy_nets_users = parser.users
		#Write to file
		with open(proxy_nets_fil, 'w') as f:
			pickle.dump(proxy_nets, f)
		with open(proxy_nets_users_fil, 'w') as f:
			pickle.dump(proxy_nets_users, f)

	#Print stats
	print 'Proxy: %s' % proxy_id
	print '\tTotal IPs: %s' % len(proxy_nets)
	print '\tValid IPs: %s' % len(proxy_nets)
	print '\tTotal Unique IP+user combination: %s' % len(proxy_nets_users)
	
	return proxy_nets, proxy_nets_users




#-------------------- DATA MANIPULATION -----------#

def getRoutersPerNode(nodes_networks, routers_per_ip):
	routers_per_node = {}
	for node,networks in nodes_networks.iteritems():
		routers = []
		for net in networks:
			router_ip = ipInc(net)
			if net.split('.')[0]=='10' and router_ip in routers_per_ip:
				router = routers_per_ip[router_ip]
				routers.extend(router)
		routers = list(set(routers)) 
		routers_per_node[node] = routers
	return routers_per_node

def getProxiesPerRouter(router_ips_per_node, proxies_per_router_ip):
	proxies_per_router = {}
	for router,ips in router_ips_per_node.iteritems():
		proxies_per_router[router] = []
		for ip in ips:
			if ip in proxies_per_router_ip:
				proxies_per_router[router].extend(proxies_per_router_ip[ip])
	proxies_per_router = {r:list(set(p)) for r,p in proxies_per_router.iteritems()}
	return proxies_per_router


def getUniqueUsersPerProxyPerRouterIP(network_users_per_proxy):
	unique_networks_users_per_proxy_per_routerip = {}
	for proxy,net_users in network_users_per_proxy.iteritems():
		for net,user in net_users:
			router_ip = ipInc(net)
			if router_ip in unique_networks_users_per_proxy_per_routerip:
				if proxy in unique_networks_users_per_proxy_per_routerip[router_ip]:
					unique_networks_users_per_proxy_per_routerip[router_ip][proxy].append((net,user))
				else:
					unique_networks_users_per_proxy_per_routerip[router_ip][proxy] = [(net,user)]
			else:
				unique_networks_users_per_proxy_per_routerip[router_ip] = {proxy:[(net,user)]}
	return unique_networks_users_per_proxy_per_routerip

#-------------------- HELPERS --------------------#


def getIPNetworksFromIPs(ips):
	"""Return a list of the unique /27 subnets based on
	   the given ips
	"""
	networks = [str(ipcalc.Network(i+'/27').network()) for i in ips]
	networks = list(set(networks))
	print 'Total Networks: %s' % len(networks)
	return networks


def ipInc(ip):
	"""Returns ip+1 assuming that the given ip_devices
	   is a subnet ip (thus no 254 possible)
	"""
	temp = ip.split('.')
	temp[-1] = str(int(temp[-1])+1)
	return '.'.join(temp)

def getLogRouterIPs(proxy_nets):
	"""Gets network IP and return router IP.
	   According to information from guifi members the ips 
	   of the routers of the nodes can be calulated adding 
	   1 to the network obtained from the logs 
	"""
	proxy_ips = [ipInc(net) for net in proxy_nets]
	nodes_devices = map(getIPNodeDeviceWeb,proxy_ips)


def getRouterIPs(ips):
	"""From a list of ips return only the ones
	   starting with 10 and finishing in 1
	"""
	router_ips = [i for i in ips if i.split('.')[0]=='10' and i.split('.')[-1] in ['1','33','65','97','129','161','193','225']]
	return router_ips


def getDBElements(zone,core):
	infra_db = InfraDB(zone, core)
	infra_db.connect()
	#traffic_ass_db = TrafficAssistantDB(zone, core)
	#traffic_ass_db.connect()

	services1 = infra_db.getServices()
	services = {g['_id']:g for g in services1}

	nodes1 = infra_db.getNodes()
	nodes = {d['_id']:d for d in nodes1}

	# In case of traffic analysis use traffic_ass
	#devices1 = traffic_ass_db.getCollection('devices')
	devices1 = infra_db.getDevices()
	devices = {d['_id']:d for d in devices1}

	radios1 = infra_db.getRadios()
	radios = {(d['_id']['device'],d['_id']['radio']):d for d in radios1}

	ifaces1 = infra_db.getIfaces()
	ifaces = {d['_id']:d for d in ifaces1}

	return services, nodes, devices, radios, ifaces


def invertListDic(dic):
	"""Invert dictionary of lists
	"""
	invert = {}
	for k,vs in dic.iteritems():
		for v in vs:
			if v in invert:
				invert[v].append(k)
			else:
				invert[v] = [k]
	return invert


def plotECDF(dic,name):

	#from numpy import *
	data = {k:len(v) for k,v in dic.iteritems()}
	df = pd.DataFrame({'X':data.keys(),'Y':data.values()})
	df = df.sort_values('Y')
	ecdf = df['Y'].value_counts()
	ecdf = ecdf.sort_index().cumsum()*1./ecdf.sum()
	#ax = ecdf.plot(drawstyle = 'steps',title=name)
	ax = ecdf.plot(title=name)
	ax.set_ylim(0,1.1)
	a = 1
	ax.set_xlabel(ax.get_xlabel(), fontsize=20, alpha=a)
	ax.set_ylabel(ax.get_ylabel(), fontsize=20, alpha=a)
	#ax.set_xlim(-2,32)
	plt.show()
	raw_input("End")

	#df.hist('networks', cumulative=True)
	

def plotBar(dic,name):
	import pandas as pd
	import operator
	from matplotlib import pyplot as plt
	plt.style.use('ggplot')

	data = {k:[len(v)] for k,v in dic.iteritems()}
	df = pd.DataFrame.from_dict(data, orient='columns')
	columns = df.columns[df.ix[df.last_valid_index()].argsort()]
	df = df[columns]
	df = df.T
	#print df
	#pdb.set_trace()
	ax = df.plot(kind='bar', title=name, legend=False)
	a = 1
	ax.set_xlabel(ax.get_xlabel(), fontsize=20, alpha=a)
	ax.set_ylabel(ax.get_ylabel(), fontsize=20, alpha=a)
	plt.xticks(rotation=0)
	#ax.set_ylim(0,1.1)
	#ax.set_xlim(-2,32)
	plt.show()
	raw_input("End")

def proxiesStackedBar(network_users_per_proxy,name):
	import pandas as pd
	import operator
	from matplotlib import pyplot as plt
	plt.style.use('ggplot')

	proxies = network_users_per_proxy.keys()
	

	data = {k:[len(v)] for k,v in network_users_per_proxy.iteritems()}
	df = pd.DataFrame.from_dict(data, orient='columns')
	columns = df.columns[df.ix[df.last_valid_index()].argsort()]
	df = df[columns]
	df = df.T

	ax = df.plot(kind='bar', title=name, legend=False)
	a = 1
	ax.set_xlabel(ax.get_xlabel(), fontsize=20, alpha=a)
	ax.set_ylabel(ax.get_ylabel(), fontsize=20, alpha=a)
	plt.xticks(rotation=0)
	#ax.set_ylim(0,1.1)
	#ax.set_xlim(-2,32)
	plt.show()
	raw_input("End")


def getNetStats(devices_nets, proxies_nets):
	print 'Networks Stats'
	networks_devices = invertListDic(devices_nets)
	print '\tNetworks of Devices: %s' % len(networks_devices)
	networks_proxies = invertListDic(proxies_nets)
	print '\tNetworks of Proxies: %s' % len(networks_proxies)
	#Keep only networks of proxies and add the corresponding
	#devices
	networks = {n:{'proxies':p,'devices':networks_devices[n]} for n,p in networks_proxies.iteritems() if n in networks_devices}
	print '\tOverlapping Networks: %s' % len(networks)
	
	#plotECDF(devices_nets, 'Networks Per Device')
	#plotECDF(proxies_nets, 'Networks Per Proxy')
	#plotECDF(networks_devices, 'Devices Per Network')
	#plotECDF(networks_proxies, 'Proxies Per Network')
	
def randomNfromList(n, mylist):
	newlist = []
	while n>0:
		temp = random.choice(mylist)
		while temp in newlist:
			temp = random.choice(mylist)
		newlist.append(temp)
		n -= 1
	return newlist


def mapDevicesProxy(devices_nets, proxies_nets):
	networks_devices = invertListDic(devices_nets)
	mapping = {}
	for proxy,nets in proxies_nets.iteritems():
		mapping[proxy] = []
		for n in nets:
			if n in networks_devices:
				mapping[proxy].extend(networks_devices[n])
	#pdb.set_trace()
	#plotECDF(mapping, 'Devices per proxy')
	for p,d in mapping.iteritems():
		print 'Proxy %s has %s devices' % (p,len(d))
	#print 'From %s devices %s are members of both proxies' % (len(devices_nets), len(list(set(mapping.values()[0]) | set(mapping.values()[1]))))
	return mapping

def devicesDic2NodesDic(devices_dic, devices, nodes):
	nodes_dic = {}
	for dev,values in devices_dic.iteritems():
		node = devices[dev]['parentNode']
		if node in nodes:
			if node in nodes_dic:
				nodes_dic[node].extend(values)
				#print "Conflict"
			else:
				#print 'Adding node info'
				nodes_dic[node] = values
		else:
			print 'Node not in zone'
	#keep unique values in each list
	nodes_dic = {node:list(set(net)) for node,net in nodes_dic.iteritems()}
	return nodes_dic

def mapping(zone, core, output=""):
	
	# INITIALIZE
	services, nodes, devices, radios, ifaces = getDBElements(zone,core)

	logs_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs','new')

	# PROXIES AND NETWORKS
	proxies = getDBZoneProxies(devices, services, logs_path)
	# SOS
	# SOS FAKE THE EXTRA NODE
	# SOS
	#proxies['3982'] = '3982-ips'
	proxies.append('3982')


	zone_ips = getDBZoneIps(devices, ifaces)
	zone_networks = getIPNetworksFromIPs(zone_ips)
	devices_networks, ips_per_device = getDBDeviceNetworks(devices, ifaces, radios)
	print  "Devices: %s" % len(devices)
	#print "Devices with networks: %s" % len(devices_networks)
	nodes_networks = devicesDic2NodesDic(devices_networks, devices, nodes)
	ips_per_node = devicesDic2NodesDic(ips_per_device, devices, nodes)

	# ROUTERS
	# find router_ips
	router_ips_per_node = {n:getRouterIPs(ips) for n,ips in ips_per_node.iteritems()}
	# keeps nodes with router ip
	router_ips_per_node = {n:l for n,l in router_ips_per_node.iteritems() if l != []}
	# Convert ips to nets
	routers_per_ip = invertListDic(router_ips_per_node)
	routers_per_node = getRoutersPerNode(nodes_networks, routers_per_ip)
	nodes_per_router = invertListDic(routers_per_node)
	routers = nodes_per_router.keys()
	print "Total routers: %s" % len(routers)


	# PROXIES
	proxies_networks_n_users  = {k:getLogNetworksNUsers(k) for k in proxies}
	proxies_networks = {k:nets for k,(nets,users) in proxies_networks_n_users.iteritems()}
	proxies_router_ips = {p:map(ipInc, n) for p,n in proxies_networks.iteritems()}
	#change id of proxy from device to node

	# SOS
	# SOS FAKE THE EXTRA NODE
	# SOS
	services['3982'] = {'parentDevice':'my_device'}
	devices['my_device'] = {'parentNode':'my_node'}

	proxies_router_ips = {devices[services[p]['parentDevice']]['parentNode']:n for p, n in proxies_router_ips.iteritems()}
	proxy_nodes = proxies_router_ips.keys()

	#proxies_router_ips = {k:getLogRouterIPs(proxies_networks[k]) for k in proxies}
	getNetStats(devices_networks, proxies_networks)
	

	proxies_per_router_ip = invertListDic(proxies_router_ips)
	proxies_per_router = getProxiesPerRouter(router_ips_per_node, proxies_per_router_ip)

	#calculate devices per proxy
	devices_per_proxy = mapDevicesProxy(devices_networks, proxies_networks)
	#change id of proxies to node id
	devices_per_proxy = { devices[services[p]['parentDevice']]['parentNode']:n for p, n in devices_per_proxy.iteritems() }


	proxies_per_device = invertListDic(devices_per_proxy)
	proxies_per_node = devicesDic2NodesDic(proxies_per_device, devices, nodes)
	

	# GET UNIQUE USERS FROM LOGS
	logs_users_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs', 'new', 'ips_usernames')
	#network_users_per_proxy = {k:getLogNetworksUsers(logs_users_path, d) for k, d in proxies.iteritems()}
	network_users_per_proxy = {k:users for k,(nets,users) in proxies_networks_n_users.iteritems()}
	
	working_proxies = network_users_per_proxy.keys()
	#the user is a tuple (IP/27,user hash)
	#find unique tuples from all the proxies proxies
	unique_networks_users = []
	for proxy, values in network_users_per_proxy.iteritems():
		unique_networks_users.extend(values)
	unique_networks_users = list(set(unique_networks_users))
	print "Unique combinations of users and networks: %s" % len(unique_networks_users)
	

	unique_networks_users_per_proxy_per_routerip = getUniqueUsersPerProxyPerRouterIP(network_users_per_proxy)

	users_per_proxy_per_router = {}
	out_of_cnml = 0
	for router_ip, users_per_proxy in unique_networks_users_per_proxy_per_routerip.iteritems():
		for proxy, users in users_per_proxy.iteritems():
			# if router_ip not in routers_per_ip it is a router not in my cnml
			# So either not set in working status or in another zone
			if router_ip in routers_per_ip:
				# Assuming all ips have one router (The case in Llucanes)
				router = routers_per_ip[router_ip][0]
				if router in users_per_proxy_per_router:
					if proxy in users_per_proxy_per_router[router]:
						users_per_proxy_per_router[router][proxy].extend(users)
					else:
						users_per_proxy_per_router[router][proxy] = users
				else:
					users_per_proxy_per_router[router] = {proxy:users}
			else:
				out_of_cnml += len(list(set(users)))


	usernumber_per_proxy_per_router = {}
	for router, users_per_proxy in users_per_proxy_per_router.iteritems():
		proxies_per_user = invertListDic(users_per_proxy)
		proxy_counts =  []
		for p in proxies_per_user.values():
			out = ""
			if len(p) > 1:
				for i in sorted(p):
					out = out + devices[services[i]['parentDevice']]['parentNode'] + ","
			else:
				out = devices[services[p[0]]['parentDevice']]['parentNode']
			proxy_counts.append(out)
		#print proxy_counts
		proxy_counts = dict(Counter(proxy_counts))

		usernumber_per_proxy_per_router[router] = proxy_counts


	pprint(usernumber_per_proxy_per_router)
	#print "Unique combinations of users and networks that exist in CNML: %s" % sum(usernumber_per_router.values())
	print "Users out of CNML: %s" % out_of_cnml


	# Randomly select nodes from the routers
	final_nodes_per_proxy_per_router = {}
	for router, nodes in nodes_per_router.iteritems():
		nodes_copy = list(nodes)
		if router in usernumber_per_proxy_per_router:
			#Check if clients more than nodes of router
			number_of_clients = sum(usernumber_per_proxy_per_router[router].values())
			if number_of_clients > len(nodes_copy):
				# If yes then fill with repeating nodes
				i = number_of_clients - len(nodes_copy)
				while i> 0:
					nodes_copy.append(random.choice(nodes_copy))
					i -= 1

			final_nodes_per_proxy_per_router[router] = {}
			for proxy, usernumber in usernumber_per_proxy_per_router[router].iteritems():
				final_nodes_per_proxy_per_router[router][proxy] = []
				while usernumber > 0:
					client = random.choice(nodes_copy)
					final_nodes_per_proxy_per_router[router][proxy].append(client)
					nodes_copy.remove(client)
					usernumber -= 1

	proxy_clients = {}
	for router, users_per_proxy in final_nodes_per_proxy_per_router.iteritems():
		proxies_per_user = invertListDic(users_per_proxy)
		for user, prox in proxies_per_user.iteritems():
			proxy_clients[user] = {'router':router, 'proxies':prox}

	userId_to_nodeId ={}
	#combine final_nodes_per_proxy_per_router and users_per_proxy_per_router
	for router, users_per_proxy in users_per_proxy_per_router.iteritems():
		for proxy, users in users_per_proxy.iteritems():
			proxy_node = devices[services[proxy]['parentDevice']]['parentNode']
			#print router,proxy_node
			nodes = []
			for pr in final_nodes_per_proxy_per_router[router].keys():
				if proxy_node in pr:
					nodes.extend(final_nodes_per_proxy_per_router[router][pr])
			users = [u for u in users if u not in userId_to_nodeId.keys()]
			#nodes = [n for n in nodes if n not in userId_to_nodeId.values()]
			#if len(users) != len(nodes):
			#	print 'Len Error'
			for user in users:
				userId_to_nodeId[user]=nodes[users.index(user)]




	#usersproxies_stats_df = getUsersProxiesBytesLog(proxies)
	#for c in usersproxies_stats_df.columns:
	#	if c not in  userId_to_nodeId.keys():
	#		usersproxies_stats_df.drop(c, axis=1, inplace=True)
	#usersproxies_stats_df.columns = [userId_to_nodeId[user] for user in usersproxies_stats_df.columns]
	#pdb.set_trace()

	if output == 'new_clients':

		fil = os.path.join(output_dir,'proxy_clients_dic')
		with open(fil,'w') as f:
			pickle.dump(proxy_clients, f)

		#bytes_per_user_fil = os.path.join(output_dir,'bytes_per_user')
		#if os.path.isfile(bytes_per_user_fil):
		#	with open(bytes_per_user_fil,'rb') as f:
		#		bytes_per_user1 = pickle.load(f)
		#else:
		#	bytes_per_user1 = getBytesPerUser(proxies)
		#	with open(bytes_per_user_fil,'w') as f:
		#		pickle.dump(bytes_per_user1, f)
		bytes_ts_per_user1, bytes_per_user1 = getBytesTSPerUser(proxies)
		bytes_per_user = {userId_to_nodeId[user]:bytes for user,bytes in bytes_per_user1.iteritems() if user in userId_to_nodeId}

		helper = []
		for client, data in proxy_clients.iteritems():
			for proxy in data['proxies']:
				for p in proxy.replace(' ', '').split(','):
					if p != '':
						print client
						helper.append({'nodeId':client, 'router':data['router'], 'proxy':p, 'bytes':bytes_per_user[client]})

		#pdb.set_trace()
		bytes_ts_per_user = []
		for user,bytes_ts in bytes_ts_per_user1.iteritems():
			if user in userId_to_nodeId:
				bytes_ts.name = userId_to_nodeId[user]
				df = pd.DataFrame(bytes_ts)
				bytes_ts_per_user.append(df)
		df_bytes_ts_per_user = pd.concat(bytes_ts_per_user, axis=1).fillna(0)
		fil = os.path.join(output_dir, 'df_bytes_ts_per_user')
		df_bytes_ts_per_user.to_pickle(fil)


		df_proxy_clients = pd.DataFrame(helper)
		# Store dataframe for proxyTrace
		fil = os.path.join(output_dir,'df_proxy_clients')
		df_proxy_clients.to_pickle(fil)

		#pdb.set_trace()

		client_ips_file = os.path.join( os.getcwd(), 'guifiAnalyzer', 'proxies', 'helpers','ips')	
		with open(client_ips_file,'w') as thefile:
			for node in df_proxy_clients['nodeId'].to_dict().values():
				ips = ips_per_node[node]
				thefile.write("%s\n" % ips[0])



		router_ips_file = os.path.join( os.getcwd(), 'guifiAnalyzer', 'proxies', 'helpers','router_ips')
		with open(router_ips_file,'w') as thefile:
			for router, ips in  router_ips_per_node.iteritems():
				thefile.write("%s\n" % ips[0])

	#plotECDF(final_nodes_per_router,'Clients Per Router')
	#plotBar(network_users_per_proxy,'Clients Per Proxy')
	#final_routers_per_node = invertListDic(final_nodes_per_router)
	#plotClientsPerRouter(df_proxy_clients)
	#plotClientsPerProxyPerRouter(df_proxy_clients)

	
	if output == "proxyPing":
		return ips_per_node


	if output == "proxyTrace":
		return ips_per_node, router_ips_per_node


	return routers, routers_per_node, ips_per_node, router_ips_per_node



def plotClientsPerRouter(df_proxy_clients):
	df = df_proxy_clients.groupby('router').count()
	df = df.sort_values('nodeId')
	ecdf = df['nodeId'].value_counts()
	ecdf = ecdf.sort_index().cumsum()*1./ecdf.sum()
	#ax = ecdf.plot(drawstyle = 'steps',title=name)
	ax = ecdf.plot(title='Clients Per Router')
	ax.set_ylim(0, 1.1)
	a = 1
	ax.set_xlabel(ax.get_xlabel(), fontsize=20, alpha=a)
	ax.set_ylabel(ax.get_ylabel(), fontsize=20, alpha=a)
	#ax.set_xlim(-2,32)
	plt.show()
	raw_input("End")

def plotClientsPerProxyPerRouter(df_proxy_clients):

	dic = {}
	for n, grp in df_proxy_clients.groupby(['proxy']):
		dic[n] = grp.groupby('router').count()['nodeId']
	df = pd.DataFrame(dic)
	dfs = {}
	for proxy in df.columns:
		ecdf = df[proxy].value_counts()
		ecdf = ecdf.sort_index().cumsum()*1./ecdf.sum()
		print ecdf
		dfs[proxy] = ecdf
	plot_df = pd.DataFrame(dfs)
	print plot_df
	plot_df = plot_df.fillna(method='pad')
	print plot_df
	ax = plot_df.plot(title='Clients Per Proxy Per Router')
	ax.set_ylim(0, 1.1)
	a = 1
	ax.set_xlabel(ax.get_xlabel(), fontsize=20, alpha=a)
	ax.set_ylabel(ax.get_ylabel(), fontsize=20, alpha=a)
	ax.set_xlim(-0.5, 20)
	plt.show()
	raw_input("End")


if __name__ == '__main__':
	reparse = raw_input('Want to reparse?(Y/N)')
	while reparse != 'Y' and reparse != 'N':
		reparse = raw_input('Want to reparse?(Y/N)')
	if reparse == 'Y':
		mapping(zone=8346, core=False, output='new_clients')
	else:
		mapping(zone=8346, core=False)

#ip='10.139.19.38'
#getIPNode(ip))
#mapDevicesProxy(8346,False)



