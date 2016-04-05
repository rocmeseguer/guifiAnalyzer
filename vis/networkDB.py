#!/usr/bin/env python
#
# network.py
from guifiAnalyzer.db.infrastructure import InfraDB
from guifiAnalyzer.db.traffic_assistant import TrafficAssistantDB

from guifiAnalyzer.proxies import getIPNetworks


import networkx
from networkx.readwrite import json_graph
# Community detection
# https://bitbucket.org/taynaud/python-louvain/ 
from guifiAnalyzer.lib.pythonLouvain import community

import matplotlib.pyplot as plt

import pandas

import functools
import os
import json
import http_server
import random
import math

import pdb

def node2Gnode(graph, digraph, infra, ass_devices, nodes_networks, node):
    node_id = node['_id']
    if node_id in nodes_networks:
        networks = nodes_networks[node_id]
    else:
        networks = []
    node_type = "client"
    graphServer = "NA"
    devices = list(node['devices'])
    for d in devices:
        if d['_id'] in ass_devices and ass_devices[d['_id']]['graphServer']!= None:
            graphServer = ass_devices[d['_id']]['graphServer']
            break
    links = infra.parseNodeLinks(node)
    # Add to graph only nodes with links
    if len(links) == 0:
        return
    if len(links) > 1:
        node_type = 'supernode'
    services = node['services']
    proxy = 0
    for s in services:
        if s['type'] == 'Proxy':
            proxy = 1
    digraph.add_node(node_id, 
                    {'name': node_id, 
                    'status': node['status'],
                    'type': node_type,
                    'isproxy' : proxy,
                    'graphServer' : graphServer,
                    'zone' : node['parentZone'],
                    'networks' : networks})
    graph.add_node(node_id, 
                    {'name': node_id, 
                    'status': node['status'],
                    'type': node_type,
                    'isproxy': proxy,
                    'graphServer' : graphServer,
                    'zone' : node['parentZone'],
                    'networks' : networks})


def link2Gedge(graph, digraph, traffic_df, link):
    if link['nodeA'] and link['nodeB']:
        if link['type'] == 'wds':
            #draw one link for both wds with 
            #standard weight
            traffic_in1 = float('nan')
            if link['deviceA'] != None:
                traffic_in1 = traffic_df.loc[link['_id'], link['deviceA']]['trafficIn']
            traffic_in = 1 if math.isnan(traffic_in1) or traffic_in1<1 else int(traffic_in1)
            traffic_out1 = float('nan')
            if link['deviceB'] != None:
                traffic_out1 = traffic_df.loc[link['_id'], link['deviceB']]['trafficOut']
            traffic_out = 1 if math.isnan(traffic_out1) != float('nan') or traffic_out1<1 else int(traffic_out1)
            digraph.add_edge(
                link['nodeA'], link['nodeB'], 
                        {'id': link['_id']+'A', 
                        'type': link['type'], 
                        #'direction': 'a',
                        #'group': link['status'],
                        'weight': traffic_in})
            digraph.add_edge(
                link['nodeB'], link['nodeA'], 
                        {'id': link['_id']+'B', 
                        'type': link['type'], 
                        #'direction': 'b',
                        #'group': link['status'],
                        'weight': traffic_out})
            graph.add_edge(
                link['nodeA'], link['nodeB'], 
                        {'id': link['_id'], 
                        'type': link['type'], 
                        #'direction': 'b',
                        #'group': link['status'],
                        'weight': traffic_out+traffic_in,
                        'traffic_in': traffic_in,
                        'traffic_out': traffic_out})
        elif link['type'] == 'ap/client':
            # draw the links using the client info
            index = 'A' if link['radioModeA'] == 'client' else 'B'
            opindex = 'A' if link['radioModeA'] == 'ap' else 'B'
            if  not link['device'+index]:
                traffic_in = 1
                traffic_out = 1
            else:
                traffic_in1 = traffic_df.loc[link['_id'], link['device'+index]]['trafficIn']
                traffic_in = 1 if math.isnan(traffic_in1) or traffic_in1<1 else int(traffic_in1)
                traffic_out1 = traffic_df.loc[link['_id'], link['device'+index]]['trafficOut']
                traffic_out = 1 if math.isnan(traffic_out1) != float('nan') or traffic_out1<1 else int(traffic_out1)
            digraph.add_edge(
                link['node'+index], link['node'+opindex], 
                        {'id': link['_id']+' out', 
                        'type': link['type'], 
                        #'group': link['status'],
                        'weight': traffic_out})
            digraph.add_edge(
                link['nodeB'], link['nodeA'], 
                        {'id': link['_id']+'in', 
                        'type': link['type'], 
                        #'group': link['status'],
                        'weight': traffic_in})
            graph.add_edge(
                link['node'+index], link['node'+opindex], 
                        {'id': link['_id'], 
                        'type': link['type'], 
                        #'group': link['status'],
                        'weight': traffic_out+traffic_in,
                        'traffic_in': traffic_in,
                        'traffic_out': traffic_out})




def createGraph(root, core):
    infraDB = InfraDB(root, core)
    infraDB.connect()
    trafficAssDB = TrafficAssistantDB(root, core)
    trafficAssDB.connect()

    nodes = infraDB.getNodes()
    links = trafficAssDB.getCollection('links')
    ass_devices = {d['_id']:d for d in trafficAssDB.getCollection('devices')}
    df_file = os.path.join( os.getcwd(), 'guifiAnalyzerOut', 'results', str(root)+'_generic_df')
    traffic_df = pandas.read_pickle(df_file)
    # Normalize
    #for i in ['trafficIn','trafficOut']:
        #traffic_df[i] -= traffic_df[i].min()
        #traffic_df[i] /= traffic_df[i].max()
        #traffic_df[i] *= 10
        #traffic_df[i] /= 100000 
    ip_networks = getIPNetworks.mapDevicesProxy(root,core)

    graph = networkx.Graph()
    digraph = networkx.DiGraph()

    map(functools.partial(node2Gnode, graph, digraph, infraDB, ass_devices,ip_networks), nodes)
    map(functools.partial(link2Gedge, graph, digraph, traffic_df), links)
    return (graph, digraph)


    #graph.add_node(1, {'id':'a','type':'supernode'}, color='red')
    #graph.add_node(2, {'id':'b','color':'blue'}, type='node')
    #graph.add_node(3, {'id':'c','type':'node'}, color='blue')
    #graph.add_edge(1,2, {'id':'a','type':'wds'}, color='green')
    #graph.add_edge(3,2, {'id':'b','type':'ap'}, color='yellow')


    # graph.add_nodes_from([1,2,3,4,5,6])
    # graph.add_edges_from([(1,2),(3,4),(5,6),(1,6),(4,5)])
    # A=to_agraph(graph)        # convert to a graphviz graph
    # A.layout()            # neato layout
    # A.draw("k5.ps")       # write postscript in k5.ps with neato layout


def graphStats(graph):

    pathlengths = []

    #print("source vertex {target:length, }")
    for v in graph.nodes():
        spl = networkx.single_source_shortest_path_length(graph, v)
        #print('%s %s' % (v,spl))
        for p in spl.values():
            pathlengths.append(p)

    print('')
    print(
        "average shortest path length %s" %
         (sum(pathlengths) / len(pathlengths)))

    # histogram of path lengths
    dist = {}
    for p in pathlengths:
        if p in dist:
            dist[p] += 1
        else:
            dist[p] = 1

    print('')
    # print("length #paths")
    # verts=dist.keys()
    # for d in sorted(verts):
    #   print('%s %d' % (d,dist[d]))

    #print("radius: %d" % radius(graph))
    #print("diameter: %d" % diameter(graph))
    #print("eccentricity: %s" % eccentricity(graph))
    #print("center: %s" % center(graph))
    #print("periphery: %s" % periphery(graph))
    #print("density: %s" % density(graph))

    # draw_shell(graph,with_labels=True)
    # plt.show()

    # write_gexf(graph,"test.gexf")
    #write_pajek(graph, "test.net")
def save(G, fname):
    json.dump(dict(nodes=[[n, G.node[n]] for n in G.nodes()],
                   links=[[u, v, G.edge[u][v]] for u,v in G.edges()]),
              open(fname, 'w'), indent=2)

def drawGraph(graph, is_connected=False):
    print 'Nodes: %s' % graph.order()
    print 'Links: %s' % graph.size()
    connected_str = "_connected" if is_connected else ""
    outputfile = os.path.join( os.getcwd(), 'guifiAnalyzerOut',
        'd3', str(root)+corename+connected_str+'.json')
    #outputgexf = os.path.join( os.getcwd(), 'guifiAnalyzerOut',
    #    'results', str(root)+corename+connected_str+'.gexf')
    #networkx.write_gexf(graph, outputgexf)
    # For undirected
    d = json_graph.node_link_data(graph)
    json.dump(d, open(outputfile, 'w'))
    # For directed
    #save(graph,outputfile)
    html = os.path.join( os.getcwd(), 'guifiAnalyzerOut',
        'd3', 'test.html')
    #http_server.load_url(html)
    http_server.load_url('guifiAnalyzerOut/d3/test.html')




def plot_log_degree(G):
    degree_sequence=sorted(networkx.degree(G).values(),reverse=True) # degree sequence
    #print "Degree sequence", degree_sequence
    dmax=max(degree_sequence)

    plt.loglog(degree_sequence,'b-',marker='o')
    plt.title("Degree rank plot")
    plt.ylabel("degree")
    plt.xlabel("rank")
    plt.show()


def plot_communities(G):

    partition = community.best_partition(G)

    #drawing
    size = float(len(set(partition.values())))
    pos = networkx.spring_layout(G)
    count = 0.
    for com in set(partition.values()) :
        count = count + 1.
        list_nodes = [nodes for nodes in partition.keys()
                                    if partition[nodes] == com]
        networkx.draw_networkx_nodes(G, pos, list_nodes, node_size = 20,
                                    node_color = str(count / size))


    networkx.draw_networkx_edges(G,pos, alpha=0.5)
    plt.show()


def kcliques_to_html(G):
    kcliques = list(networkx.k_clique_communities(G, 2))
    #pdb.set_trace()
    kcliques_colors = [random.randint(0,1000000)*len(l) for l in kcliques]
    for clique in kcliques:
        color = kcliques_colors[kcliques.index(clique)]
        for node in clique:
            G.node[node]['kclique'] = color

def components_to_html(G):
    comps = list(networkx.connected_components(G))
    comps_colors = [random.randint(0,1000000)*len(l) for l in comps]
    for comp in comps:
       color = comps_colors[comps.index(comp)]
       for node in comp:
           G.node[node]['component'] = color

def between_central_to_html(G):
    bc = networkx.betweenness_centrality(G=G, normalized=True)
    for node,value in bc.iteritems():
        G.node[node]['bc'] = value*100





def getTrafficConnectedComponentGraph(G):
    H = G.copy()
    to_remove = []
    for (s,d) in H.edges(): 
       if H[s][d]['weight'] <= 2:
           to_remove.extend([(s,d)])
    H.remove_edges_from(to_remove)
    #print list(networkx.connected_components(H))
    print networkx.number_connected_components(H)
    Gc = max(networkx.connected_component_subgraphs(H), key=len)
    #drawGraph(Gc, connected=True)
    return Gc





def addOneHopNeighbours(graph,conn_graph):
    new_graph = conn_graph.copy()
    nodeslist = graph.nodes(data=True)
    nodes = {n:d for (n, d) in nodeslist}
    for node in conn_graph:
        neigh = graph.neighbors(node)
        ccneigh = conn_graph.neighbors(node)
        extraneigh = [item for item in neigh if item not in ccneigh]
        for neighbor in extraneigh:
            nodedata = nodes[node]
            new_graph.add_node(node, nodedata)
            edgedata = graph.get_edge_data(node, neighbor)
            new_graph.add_edge(node, neighbor, edgedata)
    #pdb.set_trace()
    return new_graph



root = 8346
#root = 18668
#root = 2444
#root = 2435
core = False
#core = True
corename = '_core' if core else ''


G, DiG = createGraph(root, core)

#plot_communities(G)
#between_central_to_html(G)
drawGraph(G)


if False:
# Connected components and neighbors
    Gc = getTrafficConnectedComponentGraph(G)
    for (s,d) in G.edges():
        if Gc.has_edge(s,d):
            G[s][d]['incc'] = 1
        else:
            G[s][d]['incc'] = 0



    Gc1 = addOneHopNeighbours(G, Gc)
    Gc2 = addOneHopNeighbours(G,Gc1)


    #for (s,d) in Gc.edges():
    #    G[s][d]['incc'] = True
    drawGraph(Gc2, True)


