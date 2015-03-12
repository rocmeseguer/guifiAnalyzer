#!/usr/bin/env python
#
#network.py
from networkx import *
import matplotlib.pyplot as plt

G=Graph()
G.add_node(1, {'id':'a','type':'supernode'}, color='red')
G.add_node(2, {'id':'b','color':'blue'}, type='node')
G.add_node(3, {'id':'c','type':'node'}, color='blue')
G.add_edge(1,2, {'id':'a','type':'wds'}, color='green')
G.add_edge(3,2, {'id':'b','type':'ap'}, color='yellow')


#G.add_nodes_from([1,2,3,4,5,6])
#G.add_edges_from([(1,2),(3,4),(5,6),(1,6),(4,5)])
#A=to_agraph(G)        # convert to a graphviz graph
#A.layout()            # neato layout
#A.draw("k5.ps")       # write postscript in k5.ps with neato layout

pathlengths=[]

print("source vertex {target:length, }")
for v in G.nodes():
    spl=single_source_shortest_path_length(G,v)
    print('%s %s' % (v,spl))
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
print("length #paths")
verts=dist.keys()
for d in sorted(verts):
    print('%s %d' % (d,dist[d]))

print("radius: %d" % radius(G))
print("diameter: %d" % diameter(G))
print("eccentricity: %s" % eccentricity(G))
print("center: %s" % center(G))
print("periphery: %s" % periphery(G))
print("density: %s" % density(G))

draw(G,with_labels=True)
plt.show()

write_gexf(G,"test.gexf")
write_pajek(G, "test.net")