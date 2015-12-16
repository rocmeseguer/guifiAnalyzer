from ..traffic import TrafficDB
from ..traffic_assistant import TrafficAssistantDB
from ..infrastructure import InfraDB
from datetime import datetime

#from pprint import pprint
#from collections import Counter
import pandas
import numpy
import matplotlib
from matplotlib import pyplot
import os

import pdb

#root = 2444
#root = 8346
root = 18668
core = False
corename = '_core' if core else ''


def getIfaceRadioMode(iface_id):
	iface = infraDB.getInterface(iface_id)
	radio = infraDB.getRadio(iface['parent'])
	return radio['mode']



def getLinkRadioMode(link_id,index):
	link = infraLinks[link_id]
	iface = infraIfaces[link['interface'+index]]
	radio = infraRadios[tuple(iface['parent'].values())]
	return radio['mode']



def getDeviceLinkTrafficDF(link_id, device_id):
	device_infra = trafficAssDevices[device_id]
	#traffic_documents = trafficDB.getDeviceDocumentsAscending(device_id)
	traffic_documents = [v for k,v in trafficDevices[device_id].iteritems()] if device_id in trafficDevices else None
	traffic_in = []
	traffic_out = []
	dates = []
	error = 'No'
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
					error = 'NTKID'
		ts_in = pandas.Series(traffic_in, index=dates, name='trafficIn')
		ts_out = pandas.Series(traffic_out, index=dates, name='trafficOut')
		data_frame = pandas.concat([ts_in, ts_out], join='outer', axis=1)
	else:
		data_frame = None
		error = 'NTD'

	return (data_frame, error)


def getApClientLinkApDeviceId(link_id):
	# Keep in mind that one of both will for sure be ap
	link = trafficAssLinks[link_id]
	#device_id = link['deviceA'] if getLinkRadioMode(link_id,'A') == 'ap' else link['deviceB']
	device_id = link['deviceA'] if link['radioModeA'] == 'ap' else link['deviceB']
	return device_id

def getApClientLinkClientDeviceId(link_id):
	# Keep in mind that one of both will for sure be ap
	link = trafficAssLinks[link_id]
	device_id = link['deviceA'] if  link['radioModeA'] == 'client' else link['deviceB']
	return device_id

file_name = str(root)+corename+'_generic_df'
file_final_df = os.path.join( os.getcwd(), 'guifiAnalyzerOut', 'results', file_name)
trafficDevices = None
if  not os.path.isfile(file_final_df):
	print 'DOWNLOADING TRAFFIC DATA'
	trafficDB = TrafficDB(root, core)
	trafficDB.connect()

	traffic_assDB = TrafficAssistantDB(root, core)
	traffic_assDB.connect()

	infraDB = InfraDB(root, core)
	infraDB.connect()

	infraLinks1 = list(infraDB.getLinks())
	infraLinks = {l['_id']:l for l in infraLinks1}

	infraIfaces1 = list(infraDB.getIfaces())
	infraIfaces = {l['_id']:l for l in infraIfaces1}

	infraRadios1 = list(infraDB.getRadios())
	infraRadios = {tuple(l['_id'].values()):l for l in infraRadios1}

	trafficAssDevices1 = list(traffic_assDB.getCollection('devices'))
	trafficAssDevices = {l['_id']:l for l in trafficAssDevices1}

	trafficAssLinks1 = list(traffic_assDB.getCollection('links'))
	trafficAssLinks = {l['_id']:l for l in trafficAssLinks1}

	trafficDevices1 = list(trafficDB.database.devices.find())
	trafficDevicesIds1 =[l['_id'].split(':')[0] for l in trafficDevices1]
	trafficDevicesIds = list(set(trafficDevicesIds1))
	print len(trafficDevicesIds)
	trafficDevices = {l:{} for l in trafficDevicesIds}
	for d in trafficDevices1:
		trafficDevices[d['_id'].split(':')[0]][d['_id'].split(':')[1]]= d


	links = list(traffic_assDB.getCollection('links'))
	links = [l for l in links if l['deviceA']!=None or l['deviceB']!=None]
	linkIds = [l['_id'] for l in links]
	apclientLinks = [l for l in links if infraLinks[l['_id']]['type'] == 'ap/client']
	apclientLinkIds = [l['_id'] for l in apclientLinks]
	#wdsLinks = list(set(links)-set(apclientLinks))
	wdsLinks = [l for l in links if infraLinks[l['_id']]['type'] == 'wds']
	#links = [traffic_assDB.getLink('54034')]
	wdsDevices1 = [l['deviceA'] for l in wdsLinks]

	wdsDevices2 = [l['deviceB'] for l in wdsLinks]

	apDevices = [getApClientLinkApDeviceId(l['_id']) for l in apclientLinks ]
	#apDevices = list(set(apDevices1))
	print len(apDevices)
	clientDevices = [getApClientLinkClientDeviceId(l['_id']) for l in apclientLinks ]
	#clientDevices = list(set(clientDevices1))
	print len(clientDevices)

	devices = {'ap':apDevices,'client':clientDevices, 'wdsA':wdsDevices1, 'wdsB':wdsDevices2}



	return_tupleA = lambda x: (x['_id'], x['deviceA'])
	return_tupleB = lambda x: (x['_id'], x['deviceB'])
	final_index = [f(l) for l in apclientLinks for f in (return_tupleA, return_tupleB)]
	final_index1 = [f(l) for l in wdsLinks for f in (return_tupleA, return_tupleB)]
	final_index.extend(final_index1)
	final_index = pandas.MultiIndex.from_tuples(final_index, names=['Links','Devices'])
	final_df = pandas.DataFrame(columns=['trafficIn', 'trafficOut', 'radioMode', 'error'], index=final_index)


	


pandas.options.display.mpl_style = 'default'
#matplotlib.rc('font', family='sans-serif') 
if trafficDevices == None:
		final_df = pandas.read_pickle(file_final_df)
else:
	testedDevices = []
	for k, v in devices.iteritems():
		if k in ['wdsA', 'wdsB']:
			typ = 'wds'
		else:
			typ = k
		print k 
		for dev in v:
			if (not dev) or (dev in testedDevices):
				continue
			if k in ['ap', 'client']:
				link = apclientLinks[v.index(dev)]
			else:
				link = wdsLinks[v.index(dev)]
			df, error = getDeviceLinkTrafficDF(link['_id'], dev)
			if not isinstance(df, pandas.DataFrame):
				testedDevices.extend([dev])
				# I could have an exgtra column to note where there 
				# were no data at all / not graphed
				final_df.loc[link['_id'], dev] = [float('nan'), float('nan'), typ, error ]
				continue
			mean = df.astype('float64').mean(skipna=True, numeric_only=True)
			#pdb.set_trace()
			final_df.loc[link['_id'], dev] = [mean['trafficIn'], mean['trafficOut'], typ, error]
			testedDevices.extend([dev])
	final_df.to_pickle(file_final_df)





def get_df_statistics(df, name, stats):
	print '/////////////////'
	print 'Info %s' % name
	#print df.info()
	print 'Total Devices: %s' % (len(df))
	stats.loc[name, 'total'] = len(df)
	usable = df[(df.trafficIn > 0) | (df.trafficOut > 0)].trafficIn.count()
	print 'Total Usable Devices: %s' % (usable)
	stats.loc[name, 'correct'] = usable
	zeros = df[(df.trafficIn == 0) & (df.trafficOut == 0)].trafficIn.count()
	print 'Total Devices with zero traffic: %s' % (zeros)
	stats.loc[name, 'zeros'] = zeros
	null = df.trafficIn.isnull().sum()
	print 'Total Null %s' % (null)
	stats.loc[name, 'null'] = null
	otherrors = len(df) -usable -zeros -null
	print 'Other Errors %s' %  otherrors
	stats.loc[name, 'erorrs'] = otherrors

	print 'Error :Devices without Traffic Data %s' % (df[(df.error == 'NTD')].trafficIn.count())
	print 'Error: Device without Correct SNMP_key %s' % (df[(df.error == 'NTKID')].trafficIn.count())
	print 'Average Traffic In: %s | Total Traffic In %s | Zeros %s | Null %s' %  (df.trafficIn.mean(),
					df.trafficIn.sum(), df[df.trafficIn == 0].trafficIn.count(), df.trafficIn.isnull().sum())
	print 'Average Traffic Out: %s | Total Traffic Out %s | Zeros %s | Null %s' % (df.trafficOut.mean(), 
					df.trafficOut.sum(), df[df.trafficOut == 0].trafficOut.count(), df.trafficIn.isnull().sum())


stats_df = pandas.DataFrame(columns=['total', 'correct', 'zeros', 'null', 'error'], 
							index=['TOTAL', 'WDS', 'AP/CLIENT'])

print 'STATISTICS'
get_df_statistics(final_df, 'TOTAL', stats_df)
get_df_statistics(final_df[final_df.radioMode == 'wds'], 'WDS', stats_df)
get_df_statistics(final_df[(final_df.radioMode == 'ap') | (final_df.radioMode == 'client')],'AP/CLIENT', stats_df)
#get_df_statistics(final_df[final_df.radioMode == 'ap'], 'ap')
#get_df_statistics(final_df[final_df.radioMode == 'client'], 'client')


title = str(root) + ' core' if core else str(root)
stats_df[['correct', 'zeros', 'null','error']].plot(kind='bar', stacked=True, title=title)
#pyplot.savefig(os.path.join( os.getcwd(), 'guifiAnalyzerOut', 'results', file_name+'_stats.pdf'))
#for final_df in dfs:
#	if isinstance(df, pandas.DataFrame):	
#		fig, ax = pyplot.subplots()
#		df.plot(ax=ax)


#fig, axes = pyplot.subplots(nrows=2, ncols=1)
#for i, c in enumerate(data_frame.columns):
#    data_frame[c].plot(
#        ax=axes[i],
#        figsize=(
#            12,
#            10),
#        title=c + " 2444")
        #df['proxiesPer100Nodes'].plot(figsize=(12, 10), title='proxiesPer100Nodes'+" "+g.zone.title)
#pyplot.show()
raw_input("End")




