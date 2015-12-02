from ..traffic import TrafficDB
from ..traffic_assistant import TrafficAssistantDB
from datetime import datetime


#from pprint import pprint
#from collections import Counter
import pandas
from matplotlib import pyplot


trafficDB = TrafficDB(2444, False)
trafficDB.connect()

traffic_assDB = TrafficAssistantDB(2444, False)
traffic_assDB.connect()

link_id = "54034"

link_infra = traffic_assDB.getLink(link_id)


def getDeviceLinkTrafficDF(device_id):
	device_infra = traffic_assDB.getDevice(device_id)
	traffic_documents = trafficDB.getDeviceDocumentsAscending(device_id)
	traffic_in = []
	traffic_out = []
	dates = []
	data_frame = None
	if traffic_documents:
		for doc in traffic_documents:
			date = doc['_id'].split(':')[1]
			snmp_key = device_infra['links'][link_id]
			for i in range(0,12,1):
				minutes = str(i*5) if i > 1 else '0'+str(i*5)
				date_time = date+minutes
				date_time = datetime.strptime(date_time, "%y%m%d%H%M")
				dates.extend([date_time])
				if snmp_key in doc['measurements'][i]['data']['traffic']:
					traffic_in.extend([float(doc['measurements'][i]['data']['traffic'][snmp_key]['traffic_in'])])
					traffic_out.extend([float(doc['measurements'][i]['data']['traffic'][snmp_key]['traffic_out'])])
				else:
					traffic_in.extend([float('NaN')])
					traffic_out.extend([float('NaN')])
		ts_in = pandas.Series(traffic_in, index=dates, name='trafficIn')
		ts_out = pandas.Series(traffic_out, index=dates, name='trafficOut')
		data_frame = pandas.concat([ts_in, ts_out], join='outer', axis=1)
	return data_frame

devices = [link_infra['deviceA'], link_infra['deviceB']]

dfs = [getDeviceLinkTrafficDF(devices[0]), getDeviceLinkTrafficDF(devices[1])]


#data_frame = pandas.DataFrame(time_series).astype('float64')
#data_frame = pandas.DataFrame(time_series)

df = dfs[0]

for df in dfs:
	if isinstance(df, pandas.DataFrame):	
		fig, ax = pyplot.subplots()
		df.plot(ax=ax)


#fig, axes = pyplot.subplots(nrows=2, ncols=1)
#for i, c in enumerate(data_frame.columns):
#    data_frame[c].plot(
#        ax=axes[i],
#        figsize=(
#            12,
#            10),
#        title=c + " 2444")
        #df['proxiesPer100Nodes'].plot(figsize=(12, 10), title='proxiesPer100Nodes'+" "+g.zone.title)
pyplot.show()