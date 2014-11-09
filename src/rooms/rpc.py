
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
from geventwebsocket import WebSocketError

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
    def __init__(self, host, port, indexpath=None, access_control_header=None):
        self.host = host
        self.port = port
        self.indexpath = indexpath
        self.access_control_header = access_control_header
        self.controllers = dict()
        self.file_roots = {
            "rpc": os.path.join(os.path.dirname(__file__), "assets/rpc"),
            "jsclient": os.path.join(os.path.dirname(__file__),
                "assets/jsclient"),
        }

    def add_controller(self, name, controller):
        self.controllers[name] = controller

    def add_file_root(self, name, file_path):
        self.file_roots[name.strip('/')] = file_path

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
                return self._json_return(response, methods)
            if path[0] in self.controllers:
                controller = self.controllers[path[0]]
                func = getattr(controller, path[1], None)
                if func and  getattr(func, "is_request", False):
                    params = dict(urlparse.parse_qsl(
                        environ['wsgi.input'].read()))
                    returned = func(*(path[2:]), **params)
                    return self._json_return(response, returned)
                if func and getattr(func, "is_websocket", False):
                    ws = environ["wsgi.websocket"]
                    params = dict(urlparse.parse_qsl(environ['QUERY_STRING']))
                    returned = func(ws, *(path[2:]), **params)
                    return self._json_return(response, returned)
            if path[0] in self.file_roots:
                return self.www_file(self.file_roots[path[0]], path[1:],
                    response)
            if path == ['']:
                response('302 Found', [
                    ('location', self.indexpath or '/rpc/index.html'),
                ])
                return ""
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

    def www_file(self, root, path, response):
        filepath = os.path.join(root, *path)
        if os.path.exists(filepath):
            headers = [('content-type', guess_type(filepath))]
            self._add_optional_headers(headers)
            response('200 OK', headers)
            return [open(filepath).read()]
        else:
            response('404 Not Found', [])
            return "File Not Found: %s" % ("/".join(path),)

    def _json_return(self, response, returned):
        if returned != None:
            returned = json.dumps(returned)
        else:
            returned = "[]"
        headers = [
            ('content-type', 'application/json'),
            ('content-length', len(returned)),
        ]
        self._add_optional_headers(headers)
        response('200 OK', headers)
        return returned

    def _add_optional_headers(self, headers):
        if self.access_control_header:
            headers.append(('Access-Control-Allow-Origin',
                self.access_control_header))
