#testMongo.py

from pymongo import MongoClient

import ..guifiwrapper.guifiwrapper as gi
import ..guifiwrapper.cnmlUtils as cnmlUtils


client = MongoClient('mongodb://localhost:27017/')

g = gi.CNMLWrapper(2444)

# Prepare nodes to add them in MongoDB
for i,node in g.nodes:
	mNode = vars(node)
	# Use node id as MongoDB id
	mNode['_id'] = i
	# Delete old id element
	del mNode['id']
	# Keep id of parentZone
	mNode['parentZone'] = mNode['parentZone'].id
	# Keep an array of device ids
	mNode['devices'] = [d for d in mNode['devices']]

#index working nodes or store only working nodes and working in general?
#index devices?