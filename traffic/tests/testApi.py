#
#testapi.py

from ..lib.pyGuifiAPI import *
from ..lib.pyGuifiAPI.error import GuifiApiError
import urllib
import re
r = re.compile('http:\/\/([^\/]*).*')

from ..guifiwrapper.cnmlUtils import *

# https://guifi.net/api?command=guifi.service.get&service_id=37668
# https://github.com/guifi/drupal-guifi/commit/c155cb310144a849adec03a73ded0f67b71f6850
conn = authenticate()
sid  = 37668
data = {'command':'guifi.service.get','service_id':sid}
params = urllib.urlencode(data)
(codenum, response) = conn.sendRequest(params)
if codenum == constants.ANSWER_GOOD:
   result =  response['service']['var']['url']
   print result
   print r.match(result).group(1)
else:
    extra = response['extra'] if 'extra' in response else None
    raise GuifiApiError(response['str'], response['code'], extra)

#print data