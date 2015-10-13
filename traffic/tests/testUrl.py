
import urllib2


url = "http://ifolderlinks.ru/404"
req = urllib2.Request(url)
#try:
response = urllib2.urlopen(req,timeout=3)
#except urllib2.HTTPError as e:
#    print 'The server couldn\'t fulfill the request.'
#    print 'Error code: ', e.code
print response.info()
#print response.read()

