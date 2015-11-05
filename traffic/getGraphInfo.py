#getGraphInfo.py
#
#

# Import prepare modules
import prepareGraphInfoDB as pgidb
import graphDevicesInfoDB as gdidb




# Import Databases
from ..db.infraDB import InfraDB
from ..db.trafficAssistantDB import TrafficAssistantDB
from ..db.trafficDB import TrafficDB


# Rest of imports
import datetime


from crontab import CronTab


def initializeInfraDB(zone,core, populate = False):
	infraDB = InfraDB(zone,core)
	infraDB.connect()
	if populate:
		infraDB.populate()
	return infraDB


def initializeTrafficAssistantDB(zone, core, populate = False):
	trafficAssistantDB = TrafficAssistantDB(zone,core)
	trafficAssistantDB.connect()
	if populate:
		pgidb.graphInfo(zone, core)
	return trafficAssistantDB



def initializeTrafficDB(zone, core):
	#trafficDB = TrafficDB(zone,core)
	#trafficDB.connect()
	#return trafficDB
	pass





#now = datetime.datetime.now()
#zone = raw_input('Enter Zone')
zone = 2444
core = False
pgidb.graphInfo(zone, core)
gdidb.graphDevicesInfo(zone, core)
#gdidb.showDevicesInfo(zone, core)

#cron = file_cron = CronTab(user=True)
#for job in cron:
#	print job
#	cron.remove(job)
#job  = cron.new(command='/usr/bin/python /home/manos/Documents/crontest.py')
#job.minute.during(now.minute,now.minute+2).every(1)
#job.hour.on(now.hour)
#job.day.on(now.day)
#job.month.on(now.month)
#job.enable()
#cron.write_to_user( user=True )



#infraDB = storeInfraDB.createDB(root,core)
#storeInfraDB.populateDB(infraDB,root,core)
#pgi.graphInfo(root, core)
#pgidb.graphInfo(root, core)
# Check why guifiwrapper is ran twice


#gdi.graphDevicesInfo(root, core)
#gdidb.graphDevicesInfo(root, core)
#gdidb.showDevicesInfo(root, core)

#TODO
#separate devices that have no data from prepareGraphInfo
#introduce ifaces in linksTables from graphInfo and check how
#	to introduce link id in the deviceTable when there are
#	multiple ifaces 
#check if client devices (1 iface, 1 link) report always 0 traffic in out


# devices, workingDevices, clientDevices, boneDevices