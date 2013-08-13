
import urllib2
import urllib
import simplejson
import urlparse
import traceback
import sys
from urllib2 import URLError, HTTPError

from gevent import pywsgi
from geventwebsocket.handler import WebSocketHandler

import logging
log = logging.getLogger("rooms.wsgirpc")


class _MethodStub(object):
    def __init__(self, rest_object, rest_method, client):
        self.rest_object = rest_object
        self.rest_method = rest_method
        self.client = client

    def __call__(self, *args, **kwargs):
        if args:
            raise Exception("We don't support non-keyword args in "
                "call to %s (%s), must have param=" % (self.rest_method, args))
        try:
            response = urllib2.urlopen("http://%s:%s%s/%s" % (
                self.client.host, self.client.port, self.rest_object,
                self.rest_method), urllib.urlencode(kwargs)).read()
            return simplejson.loads(response)
        except HTTPError, he:
            errorstr = "".join(he.readlines())
            print str(he)
            print errorstr
            raise
        except URLError, ue:
            print str(ue)
            raise
        except Exception, e:
            errorstr = "".join(e.readlines())
            print str(e)
            print errorstr
            raise


class WSGIRPCClient(object):
    def __init__(self, host, port, namespace=None):
        self.host = host
        self.port = port
        self.namespace = namespace

    def __getattr__(self, name):
        if self.namespace:
            return _MethodStub("/%s" % self.namespace, name, self)
        else:
            return _MethodStub("", name, self)

    def __eq__(self, rhs):
        return type(rhs) is WSGIRPCClient and self.host == rhs.host and \
            self.port == rhs.port and self.namespace == rhs.namespace


def _json_return(response, returned):
    if returned:
        returned = simplejson.dumps(returned)
    else:
        returned = "[]"
    response('200 OK', [
        ('content-type', 'text/javascript'),
        ('content-length', len(returned)),
    ])
    return returned


class WSGIRPCServer(object):
    def __init__(self, host, port, exposed_methods=None,
            exposed_objects=None):
        self.host = host
        self.port = port
        self.exposed_methods = exposed_methods or dict()
        self.exposed_objects = exposed_objects or dict()

    def start(self):
        self.wsgi_server = pywsgi.WSGIServer((self.host, int(self.port)),
            self.handle, handler_class=WebSocketHandler)
        self.wsgi_server.start()

    def handle(self, environ, response):
        try:
            path = environ['PATH_INFO'].strip('/').split('/')
            params = dict(urlparse.parse_qsl(environ['wsgi.input'].read()))

            log.debug("Calling %s: %s", path, params)

            if path[0] in self.exposed_objects:
                rest_call = path[1]
                rest_object = self.exposed_objects[path[0]]
                rest_call = getattr(rest_object, rest_call)
                returned = rest_call(**params)
                return _json_return(response, returned)
            elif path[0] in self.exposed_methods:
                rest_call = self.exposed_methods[path[0]]
                returned = rest_call(**params)
                return _json_return(response, returned)
            else:
                response('404 Not Found', [])
                return "Path Not Found: %s" % (path,)
        except URLError, ue:
            returned = "Cannot connect to: %s" % (path,)
            response('500', [
                ('content-type', 'text/javascript'),
                ('content-length', len(returned)),
            ])
        except:
            log.exception("Exception calling %s", environ)
            exc_type, exc_value, exc_traceback = sys.exc_info()
            trace = traceback.format_exception(exc_type, exc_value,
                exc_traceback)
            returned = "Server Error calling %s(%s):\n" % ("/".join(path),
                ", ".join(["%s=%s" % (n, v) for n, v in params.items()]))
            returned += "".join(trace)
            response('500', [
                ('content-type', 'text/javascript'),
                ('content-length', len(returned)),
            ])
            return returned




if __name__ == "__main__":

    from gevent import monkey
    monkey.patch_socket()

    class A:
        def f(self):
            return "F"

    a = A()
    server = WSGIRPCServer("localhost", 8000, exposed_objects={'a':a}, exposed_methods={'b':a.f})
    server.start()
    server.wsgi_server.serve_forever()
