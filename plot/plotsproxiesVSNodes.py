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

from guifiwrapper import *


def data2TimeSeries(data):
    data = Counter(data).items()
    data = sorted(data,key=lambda x: x[0])
    dates = [d[0] for d in data]
    values = [d[1] for d in data]
    ts = pd.Series(values,index=dates)
    ts = ts.cumsum()
    ts = ts.asfreq(freq="D",method='pad')
    return ts

#root = 3671
root = 3674
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
        figfile = os.path.join(os.getcwd(),'figs','nodesNproxies','valencia',str(g.zone.id)+'nodesNproxies')
        fig.savefig(figfile, format='png', dpi=fig.dpi)
        plt.close(fig)





if False:
    index = pd.date_range(firstDate,lastDate)
    series = []
    for i in index:
        if i in data:
            series.append(series[-1]+1)
        else:
            series.append(0)
    series = pd.TimeSeries(series,index=index)
    frame = pd.DataFrame(data={"proxies":series},index=index,columns=["proxies"])

    series.plot()




    x = [date2num(date) for (date, value) in data]
    y = [value for (date, value) in data]
    y = np.cumsum(y)
    #total = y[-1]
    #y = [temp/total for temp in y ]

    # Initilaze figure to print later
    fig = plt.Figure()
    fig.set_canvas(plt.gcf().canvas)
    plt.plot_date(x=x, y=y)
    # Set graph parameters
    plt.title("Evolution of total number of "+name+"s")
    plt.ylabel("Total Number of "+name+"s")
    #plt.grid(True)
    #plt.ylim((0,3))
    #plt.step(x, y)
    plt.show()
    # Print to PDF
    figfile = os.path.join(os.getcwd(),'fig',str(root)+"_"+name+"_creation")
    #fig.savefig(figfile, format='png')



     
    #nodeDegreeECDF()
    proxies = [p.created for p in g.services.values() if p.type=='Proxy']
    creationDate(proxies,"proxy")

    nodes = [n.created for n in g.nodes.values()]
    creationDate(nodes,"node")


