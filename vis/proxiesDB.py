#!/usr/bin/env python
#
# network.py
from guifiAnalyzer.db.infrastructure import InfraDB

from guifiAnalyzer.proxies import getIPNetworks
# Community detection
# https://bitbucket.org/taynaud/python-louvain/ 
from guifiAnalyzer.lib.pythonLouvain import community

import http_server

import networkx
from networkx.readwrite import json_graph


import matplotlib.pyplot as plt

import functools
import os
import json
import random

import pdb

import pickle

def node2Gnode(graph, digraph, infra, routers, routers_per_node, proxy_clients, node):
    node_id = node['_id']
    proxies = 'N'
    router = ''
    isrouter = 1 if node_id in routers else 0
    if isrouter:
        router  = node_id
    else:
    # find the router from the list
        if node_id in routers_per_node:
            router = routers_per_node[node_id]
    
    if node_id in proxy_clients:
        proxies = proxy_clients[node_id]['proxies']
    # Discover node links radios etc to assign attributes
    devices = list(node['devices'])
    radios = []
    for d in devices:
        radios.extend(d['radios'])
    links = infra.parseNodeLinks(node)
    # Add to graph only nodes with links
    if len(links) == 0:
        return
    # decide supernodes
    node_type = 'supernode' if len(radios) > 1 else 'client'
    # Check services
    services = node['services']
    isproxy = 0
    graphServer = 0
    for s in services:
        if s['type'] == 'Proxy':
            isproxy = 1
        if s['type'] == 'SNPgraphs':
            graphServer = 1
    digraph.add_node(node_id, 
                    {'name': node_id, 
                    'status': node['status'],
                    'type': node_type,
                    'isproxy' : isproxy,
                    'isrouter' : isrouter,
                    'proxies' : proxies,
                    'router' :router,
                    'graphServer' : graphServer,
                    'zone' : node['parentZone']})
    graph.add_node(node_id, 
                    {'name': node_id, 
                    'status': node['status'],
                    'type': node_type,
                    'isproxy': isproxy,
                    'isrouter' : isrouter,
                    'proxies' : proxies,
                    'router' :router,
                    'graphServer' : graphServer,
                    'zone' : node['parentZone']})


def link2Gedge(graph, digraph, link):
    if link['nodeA'] and link['nodeB']:
        if link['type'] == 'wds':
            digraph.add_edge(
                link['nodeA'], link['nodeB'], 
                        {'id': link['_id']+'A', 
                        'type': link['type'] 
                        #'direction': 'a',
                        #'group': link['status'],
                        })
            digraph.add_edge(
                link['nodeB'], link['nodeA'], 
                        {'id': link['_id']+'B', 
                        'type': link['type'] 
                        #'direction': 'b',
                        #'group': link['status'],
                        })
            graph.add_edge(
                link['nodeA'], link['nodeB'], 
                        {'id': link['_id'], 
                        'type': link['type'] 
                        #'direction': 'b',
                        #'group': link['status'],
                        })
        elif link['type'] == 'ap/client':
            # draw the links using the client info
            index = 'A' 
            opindex = 'B'
            digraph.add_edge(
                link['node'+index], link['node'+opindex], 
                        {'id': link['_id']+' out', 
                        'type': link['type'] 
                        #'group': link['status'],
                        })
            digraph.add_edge(
                link['nodeB'], link['nodeA'], 
                        {'id': link['_id']+'in', 
                        'type': link['type'] 
                        #'group': link['status'],
                        })
            graph.add_edge(
                link['node'+index], link['node'+opindex], 
                        {'id': link['_id'], 
                        'type': link['type'] 
                        #'group': link['status'],
                        })




def createGraph(root, core):
    infraDB = InfraDB(root, core)
    infraDB.connect()

    nodes = list(infraDB.getNodes())
    nodes1 = {d['_id']:d for d in nodes}
    links = infraDB.getLinks()
    links1 = {d['_id']:d for d in links}
    # Delete links where the second node is not in the db
    wrong_links = [n for n,v in links1.iteritems() if v['nodeA'] not in nodes1 or v['nodeB'] not in nodes1]
    for l in wrong_links:
        del(links1[l])


    proxy_clients = {}
    fil = os.path.join(os.getcwd(), 'guifiAnalyzerOut', 'results','getIPNetworks','proxy_clients_dic')
    with open(fil,'r') as f:
        proxy_clients = pickle.load(f)

    routers, routers_per_node, ips_per_node, router_ips_per_node = getIPNetworks.mapping(root,core)
    graph = networkx.Graph()
    digraph = networkx.DiGraph()

    map(functools.partial(node2Gnode, graph, digraph, infraDB, routers, routers_per_node, proxy_clients), nodes)
    map(functools.partial(link2Gedge, graph, digraph), links1.values())

    # SOS
    # SOS FAKE THE EXTRA NODE AND LINKS
    # SOS

    graph.add_node('my_node', 
                    {'name': 'my_node', 
                    'status': 2,
                    'type': 'supernode',
                    'isproxy': 1,
                    'isrouter' : 0,
                    'proxies' : '',
                    'router' : 'N',
                    'graphServer' : 0,
                    'zone' : '8346'})


    graph.add_edge(
                'my_node', '4890', 
                        {'id': '1', 
                        'type': 'wds' 
                        #'direction': 'b',
                        #'group': link['status'],
                        })

    graph.add_edge(
                'my_node', '11697', 
                        {'id': '1', 
                        'type': 'wds' 
                        #'direction': 'b',
                        #'group': link['status'],
                        })

    graph.add_edge(
                'my_node', '7193', 
                        {'id': '1', 
                        'type': 'wds' 
                        #'direction': 'b',
                        #'group': link['status'],
                        })



    for  i in ['4890','11697','7193']:
        graph.node[i]['isproxy'] = 0
        graph.node[i]['isrouter'] = 1
        if  graph.node[i]['proxies'] == "N":
            graph.node[i]['proxies'] = 'my_node'
        else:
            graph.node[i]['proxies'] += 'my_node'


    G = max(networkx.connected_component_subgraphs(graph), key=len)
    ips_per_node = keepConnectedNodes(ips_per_node,G)
    router_ips_per_node = keepConnectedNodes(router_ips_per_node,G)

    print "Total routers: %s" % len(router_ips_per_node)

    return G, ips_per_node, router_ips_per_node



def keepConnectedNodes(dic, connected):
    nodes = connected.nodes()
    new_dic = {k:v for k,v in dic.iteritems() if k in nodes}
    return new_dic

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

def drawGraph(graph, root, corename, is_connected=False):
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
    http_server.load_url('guifiAnalyzerOut/d3/proxies1.html')


def plot_log_degree(G):
    degree_sequence=sorted(networkx.degree(G).values(),reverse=True) # degree sequence
    #print "Degree sequence", degree_sequence
    dmax=max(degree_sequence)

    plt.loglog(degree_sequence,'b-',marker='o')
    plt.title("Degree rank plot")
    plt.ylabel("degree")
    plt.xlabel("rank")
    plt.show()
    raw_input("End")

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
    raw_input("End")



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




if __name__ == '__main__' :
    root = 8346 #Llucanes
    #root = 8350 #Osona Sud 
    #root = 18668
    #root = 2444
    #root = 2435
    core = False
    #core = True
    corename = '_core' if core else ''


    G,_,_ = createGraph(root, core)


    drawGraph(G, root, corename)


    #plot_communities(G)
    #between_central_to_html(G)
    #plot_log_degree(G)






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


