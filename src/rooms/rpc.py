
import os
import urllib2
import urllib
import json
import urlparse
import traceback
import sys
import inspect
from urllib2 import URLError, HTTPError
from functools import wraps
from mimetypes import guess_type

from gevent import pywsgi
from geventwebsocket.handler import WebSocketHandler

import logging
log = logging.getLogger("rooms.wsgirpc")


class RPCException(Exception):
    pass


class RPCWaitException(Exception):
    def __init__(self, message):
        super(RPCWaitException, self).__init__(message)


class WSGIRPCClient(object):
    def __init__(self, host, port, namespace=None):
        self.host = host
        self.port = port
        self.namespace = namespace or ""

    def __eq__(self, rhs):
        return type(rhs) is WSGIRPCClient and self.host == rhs.host and \
            self.port == rhs.port and self.namespace == rhs.namespace

    def http_connect(self, url, params):
        return urllib2.urlopen(url, params)

    def call(self, method, **kwargs):
        try:
            url = "http://%s:%s/%s" % (self.host, self.port,
                os.path.join(self.namespace, method))
            response = self.http_connect(url, urllib.urlencode(kwargs)).read()
            return json.loads(response)
        except HTTPError, he:
            errorstr = "".join(he.readlines())
            log.exception("HTTPError calling %s(%s), %s", method, kwargs,
                errorstr)
            raise
        except URLError, ue:
            log.exception("URLError calling %s(%s), %s", method, kwargs,
                str(ue))
            raise
        except Exception, e:
            log.exception("Exception calling %s(%s), %s", method, kwargs,
                str(e))
            raise


def _json_return(response, returned):
    if returned:
        returned = json.dumps(returned)
    else:
        returned = "[]"
    response('200 OK', [
        ('content-type', 'application/json'),
        ('content-length', len(returned)),
    ])
    return returned


def request(func):
    @wraps(func)
    def wrapped(*args, **kwargs):
        return func(*args, **kwargs)
    wrapped.is_request = True
    wrapped.args = inspect.getargspec(func).args
    return wrapped


def websocket(func):
    @wraps(func)
    def wrapped(ws, *args, **kwargs):
        return func(ws, *args, **kwargs)
    wrapped.is_websocket = True
    wrapped.args = inspect.getargspec(func).args[1:]
    return wrapped


class WSGIRPCServer(object):
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.controllers = dict()

    def add_controller(self, name, controller):
        self.controllers[name] = controller

    def controller_methods(self, name):
        controller = self.controllers[name]
        methods = {}
        for field, method in inspect.getmembers(controller, \
                predicate=inspect.ismethod):
            func = getattr(controller, field)
            if getattr(func, "is_request", False) or \
                getattr(func, "is_websocket", False):
                methods[field] = {'args': func.args[1:],
                    'doc': func.__doc__ or "",
                    'type': 'request' if \
                        getattr(func, "is_request", False) else "websocket"}
        return methods

    def start(self):
        self.wsgi_server = pywsgi.WSGIServer((self.host, int(self.port)),
            self.handle, handler_class=WebSocketHandler)
        self.wsgi_server.start()

    def serve_forever(self):
        self.wsgi_server.serve_forever()

    def handle(self, environ, response):
        params = {}
        try:
            path = environ['PATH_INFO'].strip('/').split('/')
            if path[0] == "_list_methods":
                methods = {}
                for name, controller in self.controllers.items():
                    methods[name] = self.controller_methods(name)
                return _json_return(response, methods)
            if path[0] in self.controllers:
                controller = self.controllers[path[0]]
                func = getattr(controller, path[1], None)
                if func and  getattr(func, "is_request", False):
                    params = dict(urlparse.parse_qsl(
                        environ['wsgi.input'].read()))
                    returned = func(**params)
                    return _json_return(response, returned)
                if func and getattr(func, "is_websocket", False):
                    ws = environ["wsgi.websocket"]
                    params = dict(urlparse.parse_qsl(environ['QUERY_STRING']))
                    returned = func(ws, **params)
                    return _json_return(response, returned)
            if path == ['']:
                response('302 Found', [
                    ('location', '/_rpc/index.html'),
                ])
                return ""
            if path[0] == "_rpc":
                return self.www_file(path[1:], response)
            response('404 Not Found', [])
            return "Path Not Found: %s" % (path,)
        except RPCWaitException, we:
            response('503 Service Unavailable', [
                ('retry-after', '3'),
            ])
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

    def www_file(self, path, response):
        filepath = os.path.join(os.path.dirname(__file__), "rpc_assets", *path)
        if os.path.exists(filepath):
            response('200 OK', [('content-type', guess_type(filepath))])
            return [open(filepath).read()]
        else:
            response('404 Not Found', [])
            return "File Not Found: %s" % ("/".join(path),)

