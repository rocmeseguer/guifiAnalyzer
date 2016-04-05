#getGraphInfo.py
#
#

# Import prepare modules
import prepareGraphInfoDB as pgidb
import graphDevicesInfoDB as gdidb




# Import Databases
#from ..db.infraDB import InfraDB
from ..db import infrastructure
#from ..db.trafficDB import TrafficDB
from ..db import traffic
#from ..db.trafficAssistantDB import TrafficAssistantDB
from ..db import traffic_assistant


# Rest of imports
import datetime


from crontab import CronTab


def initializeInfraDB(zone,core, populate = False):
	infra_db = infrastructure.InfraDB(zone, core)
	infra_db.connect()
	if populate:
		infra_db.populate()
	return infra_db


def initializeTrafficAssistantDB(zone, core, populate = False):
	traffic_ass_db = traffic_assistant.TrafficAssistantDB(zone, core)
	traffic_ass_db.connect()
	if populate:
		pgidb.graphInfo(zone, core)
	return traffic_ass_db



def initializeTrafficDB(zone, core):
	traffic_db = traffic.TrafficDB(zone, core)
	traffic_db.connect()
	return traffic_db



#def launchMeasurement(zone,core):





#now = datetime.datetime.utcnow()
now = datetime.datetime.now()
year = now.year
month = now.month
day = now.day
hour = now.hour
minute = now.minute
#zone = raw_input('Enter Zone')
#zone = 2444
zone = 8346
#zone = 17711
#zone = 8350
core = False
initializeInfraDB(zone, core, populate=True)
#initializeTrafficAssistantDB(zone, core, populate=True)


#gdidb.graphDevicesInfo(zone, core, now)
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

def addCronJob():
    corename = '_core' if core else ''
    logfile ='/home/manos/Documents/phd/Guifi/my/guifiAnalyzerOut/log/traffic_'+str(zone)+corename+'.log'
    #cron = CronTab(user=True, log=logfile)
    cron = CronTab(user=True)
    python = '/usr/bin/python'
    module = 'guifiAnalyzer.traffic.graphDevicesInfoDB 1 '
    corearg = ' core' if core else ''
    args = str(zone)+corearg
    cmd = 'cd /home/manos/Documents/phd/Guifi/my; '+python+' -m '+module+' '+args+' >> '+logfile+' 2>&1'
    #cmd = 'cd /home/manos/Documents; '+python+' -m '+module+' '+args
    # You can even set a comment for this command
    job = cron.new(command=cmd)
    job.minute.every(5)
    #job.hour.on(now.hour)
    job.hour.during(0,23).every(1)
    job.day.on(now.day+1)
    job.month.on(now.month)
    job.enable()
    cron.write_to_user( user=True )

#addCronJob()

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
# put an one minute timeout in snprequests

# devices, workingDevices, clientDevices, boneDevices
