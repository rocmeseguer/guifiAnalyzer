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


from guifiwrapper import *

root = 3671
g = CNMLWrapper(root)


#TODOOOOOOOOOOO
# Experiment comaping node creation and proxy creation


user = ['meteo',  'radio', 'web','VPS','tv','wol', 'Proxy', 'mail','irc',
                            'teamspeak', 'ftp' ,'asterisk', 'apt-cache','AP','IM', 'p2p',
                            'VPN','Streaming','games','cam']
mgmt = ['iperf', 'LDAP','DNS','SNPgraphs','NTP','AirControl']

# Extract user services and frequencies
#userServices = [s.type for s in g.services.values() if s.type in user]
#totalServices = len(userServices)
#userServices = Counter(userServices).items()
#userServicesNumber = len(userServices)
#userTypes = [typ for (typ,values) in userServices]
#userValues = [float(value)/float(totalServices) for (typ,value) in userServices]



# Extract mgmt services and frequencies
def serviceTypesFrequencies(typeset, name):
    services = [s.type for s in g.services.values() if s.type in typeset]
    totalServices = len(services)
    services = Counter(services).items()
    servicesNumber = len(services)
    types = [typ for (typ,values) in services]
    values = [float(value)/float(totalServices) for (typ,value) in services]

    ind = np.arange(servicesNumber)
    width = 0.35


    fig = plt.figure()
    ax = fig.add_subplot(111)
    rects = ax.bar(ind,values, width, color='black')
    ax.set_xlim(-width,len(ind)+width)
    #ax.set_ylim(0,45)
    ax.set_ylabel('Frequency')
    ax.set_xlabel('Service Type')
    #ax.set_title(name+' Services Frequency')
    xTickMarks = [str(i) for i in types]
    ax.set_xticks(ind+width)
    xtickNames = ax.set_xticklabels(xTickMarks)
    plt.setp(xtickNames, rotation=45, fontsize=10)
    plt.show()
    figfile = os.path.join(os.getcwd(),'fig',str(root)+"_"+name+"_services_frequency_ECDF")
    fig.savefig(figfile, format='png')

serviceTypesFrequencies(user, 'User')
serviceTypesFrequencies(mgmt, 'Management')

def nodeDegreeECDF():
    nodeD = [n.totalLinks for n in g.nodes.values()]
    counter = Counter(nodeD).items()
    print counter
    ecdf = ECDF(nodeD)
    print ecdf
    # Initilaze figure to print later
    fig = plt.Figure()
    fig.set_canvas(plt.gcf().canvas)
    plt.plot(ecdf.x, ecdf.y)
    # Set graph parameters
    #plt.title("Node Degree ECDF")
    plt.ylabel("Frequency")
    plt.xlabel("Node Degree")
    plt.xlim(-1,50)
    plt.show()
    # Print to PDF
    figfile = os.path.join(os.getcwd(),'fig',str(root)+"_node_degree_ECDF")
    fig.savefig(figfile, format='png')


#def plot2PDF(figure,name):




if False:
    nodeD = [n.totalLinks for n in g.nodes.values()]
    data = Counter(nodeD).items()
    data = sorted(data,key=lambda x: x[0])
    total = len(g.nodes)

    x = [degree for (degree, freq) in data]
    y = [freq for (degree,freq) in data]
    #y = np.cumsum(y)

    #plt.title("Node Degree CDF")
    plt.ylabel("Frequency")
    plt.xlabel("Total Number of Proxies")

    plt.scatter(x, y)
    plt.show()


#def  typesBars(data):


def creationDate():
    # For now it works for proxies
    # All creation dates
    #proxies = [(dt.datetime.strptime(p.created, '%Y%m%d %I%M')).date() for p in g.services.values() if p.type=='Proxy']
    proxies = [(dt.datetime.strptime(p.created, '%Y%m%d %I%M')) for p in g.services.values() if p.type=='Proxy']


    # Tuple of date, no of occurences
    data = proxies
    data = Counter(data).items()
    data = sorted(data,key=lambda x: x[0])

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
    #plt.title("Evolution of proxy service creation")
    plt.ylabel("Total Number of Proxies")
    #plt.grid(True)
    #plt.ylim((0,3))
    #plt.step(x, y)
    plt.show()
    # Print to PDF
    figfile = os.path.join(os.getcwd(),'fig',str(root)+"_proxy_creation")
    fig.savefig(figfile, format='png')



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

nodeDegreeECDF()
creationDate()