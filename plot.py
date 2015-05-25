#!/usr/bin/env python

import datetime as dt
import numpy as np
import matplotlib.pyplot as plt
#import matplotlib.dates as mdates
#import matplotlib.cbook as cbook

#from matplotlib import pyplot as plt
from matplotlib.dates import date2num

from collections import Counter


from guifiwrapper import *

root = 2413
g = CNMLWrapper(root)


nodeD = [n.totalLinks for n in g.nodes.values()]
data = Counter(nodeD).items()
data = sorted(data,key=lambda x: x[0])

x = [degree for (degree, freq) in data]
y = [freq for (degree,freq) in data]
y = np.cumsum(y)

plt.scatter(x, y)
plt.show()



def creationDateECDF():
    # For now it works for proxies
    # All creation dates
    proxies = [(dt.datetime.strptime(p.created, '%Y%m%d %I%M')).date() for p in g.services.values() if p.type=='Proxy']


    # Tuple of date, no of occurences
    data = proxies
    data = Counter(data).items()
    data = sorted(data,key=lambda x: x[0])

    x = [date2num(date) for (date, value) in data]
    y = [value for (date, value) in data]
    y = np.cumsum(y)
    #total = y[-1]
    #y = [temp/total for temp in y ]

    plt.plot_date(x=x, y=y)
    plt.title("Page impressions on example.com")
    plt.ylabel("Page impressions")
    #plt.grid(True)
    #plt.ylim((0,3))
    #plt.step(x, y)
    plt.show()


    if False:

        fig = plt.figure()

        graph = fig.add_subplot(111)

        # Plot the data as a red line with round markers
        graph.plot(x,y,'r-o')

        # Set the xtick locations to correspond to just the dates you entered.
        graph.set_xticks(x)

        # Set the xtick labels to correspond to just the dates you entered.
        graph.set_xticklabels(
                [date.strftime("%Y-%m-%d") for (date, value) in data]
                )

        plt.show()

    if False:

        years    = mdates.YearLocator()   # every year
        months   = mdates.MonthLocator()  # every month
        yearsFmt = mdates.DateFormatter('%Y')


        # load a numpy record array from yahoo csv data with fields date,
        # open, close, volume, adj_close from the mpl-data/example directory.
        # The record array stores python datetime.date as an object array in
        # the date column
        datafile = cbook.get_sample_data('goog.npy')
        r = np.load(datafile).view(np.recarray)

        fig, ax = plt.subplots()
        ax.plot(r.date, r.adj_close)


        # format the ticks
        ax.xaxis.set_major_locator(years)
        ax.xaxis.set_major_formatter(yearsFmt)
        ax.xaxis.set_minor_locator(months)

        datemin = datetime.date(r.date.min().year, 1, 1)
        datemax = datetime.date(r.date.max().year+1, 1, 1)
        ax.set_xlim(datemin, datemax)

        # format the coords message box
        def price(x): return '$%1.2f'%x
        ax.format_xdata = mdates.DateFormatter('%Y-%m-%d')
        ax.format_ydata = price
        ax.grid(True)

        # rotates and right aligns the x labels, and moves the bottom of the
        # axes up to make room for them
        fig.autofmt_xdate()

        plt.show()