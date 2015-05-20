#!/usr/bin/env python
#
#network.py
from networkx import *
import matplotlib.pyplot as plt

import functools

from guifiwrapper import *

import json
from networkx.readwrite import json_graph
import http_server

def node2Gnode(graph,node):
    graph.add_node(node.id,{'name':node.id, 'group':node.status})

def link2Gedge(graph,link):
    if link.nodeA and link.nodeB:
        graph.add_edge(link.nodeA.id,link.nodeB.id,{'id':link.id, 'type':link.type, 'group':link.status})

root = 8076
#root = 3671
g = CNMLWrapper(root)
G=Graph()

map(functools.partial(node2Gnode,G),g.totalnodes.values())
map(functools.partial(link2Gedge,G),g.totallinks.values())





#G.add_node(1, {'id':'a','type':'supernode'}, color='red')
#G.add_node(2, {'id':'b','color':'blue'}, type='node')
#G.add_node(3, {'id':'c','type':'node'}, color='blue')
#G.add_edge(1,2, {'id':'a','type':'wds'}, color='green')
#G.add_edge(3,2, {'id':'b','type':'ap'}, color='yellow')


#G.add_nodes_from([1,2,3,4,5,6])
#G.add_edges_from([(1,2),(3,4),(5,6),(1,6),(4,5)])
#A=to_agraph(G)        # convert to a graphviz graph
#A.layout()            # neato layout
#A.draw("k5.ps")       # write postscript in k5.ps with neato layout

pathlengths=[]

print("source vertex {target:length, }")
for v in G.nodes():
    spl=single_source_shortest_path_length(G,v)
    #print('%s %s' % (v,spl))
    for p in spl.values():
        pathlengths.append(p)

print('')
print("average shortest path length %s" % (sum(pathlengths)/len(pathlengths)))

# histogram of path lengths
dist={}
for p in pathlengths:
    if p in dist:
        dist[p]+=1
    else:
        dist[p]=1

print('')
#print("length #paths")
#verts=dist.keys()
#for d in sorted(verts):
 #   print('%s %d' % (d,dist[d]))

#print("radius: %d" % radius(G))
#print("diameter: %d" % diameter(G))
#print("eccentricity: %s" % eccentricity(G))
#print("center: %s" % center(G))
#print("periphery: %s" % periphery(G))
#print("density: %s" % density(G))

#draw_shell(G,with_labels=True)
#plt.show()

#write_gexf(G,"test.gexf")
#write_pajek(G, "test.net")

d = json_graph.node_link_data(G)
json.dump(d, open('d3/test.json','w'))
http_server.load_url('d3/test.html')