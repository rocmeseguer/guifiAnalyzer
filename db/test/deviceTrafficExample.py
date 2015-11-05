

#db.collection.find({'traffic.50.No':{'$gte':199980}})
# Search how to search for example for specific mins if mins are
# field name


# Everytime i insert new data check if I inserted all of them. If sth is missing fill it with 
# 0s

# 2 collections one with one document and general info like when experiment started finished etc.
# one with all devices and measurements

{
	'_id' : deviceId
	'measurements' : 20,
	'total' : 1920,
	'traffic' : {
		'month' : {
			'_id' : 02,
			'total_measurements' : ...
			'actual_measurements' : ...
			'total' :  ...
			'day' : {}
				'dd/mm/yy-h' :{
					'measurements' : ...
					'total' : ...
					'data':{
						'00': {},
						'05':{},
						'10':{},
						'15':{},
						'20':{},
						'25':{},
						'30':{},
						'35':{},
						'40':{},
						'45':{},
						'50':{},
						'55':{}
					}
				}
				'dd/mm/yy-h' :{
					'measurements' : ...
					'total' : ...
					'data':{
						'00': {},
						'05':{},
						'10':{},
						'15':{},
						'20':{},
						'25':{},
						'30':{},
						'35':{},
						'40':{},
						'45':{},
						'50':{},
						'55':{}
					}
				}
				.
				.
				.
	}

		}
		




}