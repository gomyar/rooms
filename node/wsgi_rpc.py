
import urllib2
import urllib
import simplejson


class _MethodStub(object):
    def __init__(self, rest_object, rest_method, client):
        self.rest_object = rest_object
        self.rest_method = rest_method
        self.client = client

    def __call__(self, **kwargs):
        response = urllib2.urlopen("http://%s:%s/%s/%s" % (
            self.client.host, self.client.port, self.rest_object,
            self.rest_method), urllib.urlencode(kwargs)).read()
        return simplejson.loads(response)

class WSGIRPCClient(object):
    def __init__(self, host, port):
        self.host = host
        self.port = port

    def __getattr__(self, name):
        return _MethodStub(name, self)
