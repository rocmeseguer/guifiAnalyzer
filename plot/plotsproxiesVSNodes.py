#!/usr/bin/env python

import datetime as dt
import numpy as np
import matplotlib.pyplot as plt
#import matplotlib.dates as mdates
#import matplotlib.cbook as cbook

#from matplotlib import pyplot as plt
from matplotlib.dates import date2num

from statsmodels.distributions.empirical_distribution import ECDF

from collections import Counter

import pandas as pd

from ..guifiwrapper import *


#root = 3671
root = 18672
zonename = 'valencia'


import os
basedir = os.path.join(os.getcwd(),'figs')
basenodesproxiesdir = os.path.join(basedir,'nodesNproxies')
zonedir = os.path.join(basenodesproxiesdir,zonename)
for d in [basedir,basenodesproxiesdir,zonedir]:
    if not os.path.exists(d):
        os.makedirs(d)



def data2TimeSeries(data):
    data = Counter(data).items()
    data = sorted(data,key=lambda x: x[0])
    dates = [d[0] for d in data]
    values = [d[1] for d in data]
    ts = pd.Series(values,index=dates)
    ts = ts.cumsum()
    ts = ts.asfreq(freq="D",method='pad')
    return ts


g = CNMLWrapper(root)

subzones = g.zone.subzones
print subzones
zoneset = []
for z in subzones:
    #print g.zones[z].workingZone.totalNodes
    if g.zones[z].workingZone.totalNodes> 100:
        zoneset.append(z)
print zoneset

for z in zoneset:
    g = CNMLWrapper(z)

    proxies = [p.created.date() for p in g.services.values() if p.type=='Proxy']
    if proxies:
        proxiesCS = data2TimeSeries(proxies)
        nodes = [n.created.date() for n in g.nodes.values()]
        nodesCS = data2TimeSeries(nodes)

        #proxiesCS = proxiesTS.cumsum()
        #nodesCS = nodesTS.cumsum()
        data = {'proxies_creation':proxiesCS,'nodes_creation':nodesCS}
        df = pd.DataFrame(data).astype('float64')
        df['proxiesPer20Nodes'] = df.proxies_creation/(df.nodes_creation/20)

        fig, axes = plt.subplots(nrows=3, ncols=1)
        for i, c in enumerate(df.columns):
            df[c].plot(ax=axes[i], figsize=(12, 10), title=c+" "+g.zone.title)
        #df['proxiesPer100Nodes'].plot(figsize=(12, 10), title='proxiesPer100Nodes'+" "+g.zone.title)
        #plt.show()

        basenodesproxiesdir = os.path.join(basedir,'')
        figfile = os.path.join(zonedir,str(g.zone.id)+'nodesNproxies')
        fig.savefig(figfile, format='png', dpi=fig.dpi)
        plt.close(fig)



