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

services = [s.type for s in g.services.values() if s.type in user]
totalServices = len(services)
services = Counter(services).items()
servicesNumber = len(services)
types = [typ for (typ,value) in services]
values = [float(value)/float(totalServices) for (typ,value) in services]

ind = np.arange(servicesNumber)
width = 0.35


fig = plt.figure()
fig.set_canvas(plt.gcf().canvas)
ax = fig.add_subplot(121)
rects = ax.bar(ind,values, width, color='black')
ax.set_xlim(-width,len(ind)+width)
#ax.set_ylim(0,45)
ax.set_ylabel('Frequency')
ax.set_xlabel('Service Type')
#ax.set_title(' {User Services Frequency')
xTickMarks = [str(i) for i in types]
ax.set_xticks(ind+width)
xtickNames = ax.set_xticklabels(xTickMarks)
plt.setp(xtickNames, rotation=45, fontsize=10)

services1 = [s.type for s in g.services.values() if s.type in mgmt]
totalServices1 = len(services1)
services1 = Counter(services1).items()
servicesNumber1 = len(services1)
types1 = [typ for (typ,value1) in services1]
values1 = [float(value)/float(totalServices1) for (typ,value) in services1]


ind1 = np.arange(servicesNumber1)

ax1 = fig.add_subplot(122)
rects = ax1.bar(ind1,values1, width, color='black')
ax1.set_xlim(-width,len(ind1)+width)
#ax.set_ylim(0,45)
ax1.set_ylabel('Frequency')
ax1.set_xlabel('Service Type')
#ax1.set_title(' Management Services Frequency')
xTickMarks1 = [str(i) for i in types1]
ax1.set_xticks(ind1+width)
xtickNames1 = ax1.set_xticklabels(xTickMarks1)
plt.setp(xtickNames1, rotation=0, fontsize=10)

plt.show()
figfile = os.path.join(os.getcwd(),'fig',str(root)+"services_frequency")
fig.savefig(figfile, format='png', dpi=fig.dpi)


# Other categories
for s in g.services.values():
    if s.type in mgmt:
        s.type = "Management"
    elif s.type != "Proxy":
        s.type = "Other services"
services = [s.type for s in g.services.values()]
totalServices = len(services)
services = Counter(services).items()
servicesNumber = len(services)
types = [typ for (typ,value) in services]
values = [float(value)/float(totalServices) for (typ,value) in services]
ind = np.arange(servicesNumber)
width = 0.35
fig = plt.figure()
fig.set_canvas(plt.gcf().canvas)
ax = fig.add_subplot(111)
rects = ax.bar(ind,values, width, color='black')
ax.set_xlim(-width,len(ind)+width)
#ax.set_ylim(0,45)
ax.set_ylabel('Frequency')
ax.set_xlabel('Service Type')
#ax.set_title(' Service Categories Frequency')
xTickMarks = [str(i) for i in types]
ax.set_xticks(ind+width)
xtickNames = ax.set_xticklabels(xTickMarks)
plt.setp(xtickNames, rotation=45, fontsize=10)
plt.show()
figfile = os.path.join(os.getcwd(),'fig',str(root)+"services_frequency_categories")
fig.savefig(figfile, format='png', dpi=fig.dpi )



services = [s.type for s in g.devices.values()]
totalServices = len(services)
services = Counter(services).items()
servicesNumber = len(services)
types = [typ for (typ,value) in services]
values = [float(value)/float(totalServices) for (typ,value) in services]
ind = np.arange(servicesNumber)
width = 0.35
fig = plt.figure()
fig.set_canvas(plt.gcf().canvas)
ax = fig.add_subplot(111)
rects = ax.bar(ind,values, width, color='black')
ax.set_xlim(-width,len(ind)+width)
#ax.set_ylim(0,45)
ax.set_ylabel('Frequency')
ax.set_xlabel('Device Type')
ax.set_title(' Device Types Frequency')
xTickMarks = [str(i) for i in types]
ax.set_xticks(ind+width)
xtickNames = ax.set_xticklabels(xTickMarks)
plt.setp(xtickNames, rotation=45, fontsize=10)
plt.show()
figfile = os.path.join(os.getcwd(),'fig',str(root)+"device_types_frequency")
fig.savefig(figfile, format='png', dpi=fig.dpi )