#
#testapi.py

from ..lib.pyGuifiAPI import *
from ..lib.pyGuifiAPI.error import GuifiApiError
import urllib


from ..guifiwrapper.cnmlUtils import *

# https://guifi.net/api?command=guifi.service.get&service_id=37668
conn = authenticate()
sid  = 37668
data = {'command':'guifi.service.get','service_id':sid}
params = urllib.urlencode(data)
(codenum, response) = conn.sendRequest(params)
if codenum == constants.ANSWER_GOOD:
   print response['service']['var']['url']
else:
    extra = response['extra'] if 'extra' in response else None
    raise GuifiApiError(response['str'], response['code'], extra)
#print data