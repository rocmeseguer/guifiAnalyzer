#getGraphInfo.py
#
#

import prepareGraphInfo as pgi
import graphDevicesInfo as gdi
import datetime


from crontab import CronTab

now = datetime.datetime.now()


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



root = 2444
core = False
pgi.graphInfo(root, core)
gdi.graphDevicesInfo(root, core)
#gdi.showDevicesInfo(root, core)

#TODO
#separate devices that have no data from prepareGraphInfo
#introduce ifaces in linksTables from graphInfo and check how
#	to introduce link id in the deviceTable when there are
#	multiple ifaces 
#check if client devices (1 iface, 1 link) report always 0 traffic in out
