
import unittest
from StringIO import StringIO

from rpc import WSGIRPCClient
from rpc import WSGIRPCServer
from rpc import request
from rpc import websocket


class MockController(object):
    def __init__(self):
        self.called = None
        self.ws = None

    @request
    def index(self, arg1):
        self.called = arg1
        return {'result': 1}

    def notexposed(self, arg1):
        raise Exception("Should never be called")

    @websocket
    def websock(self, ws, arg1):
        self.called = arg1
        self.ws = ws
        return "OK"


class RPCTest(unittest.TestCase):
    def setUp(self):
        self.rpc_client = WSGIRPCClient("10.10.10.1", 8888)
        self.rpc_client.http_connect = self._http_connect
        self.mock_http_response = StringIO('["response"]')
        self.mock_http_url = None
        self.mock_http_kwargs = None
        self._server_code = None
        self._server_lines = None

    def _http_connect(self, url, kwargs):
        self.mock_http_url = url
        self.mock_http_kwargs = kwargs
        return self.mock_http_response

    def _server_response(self, http_code, lines):
        self._server_code = http_code
        self._server_lines = lines

    def testBasicCall(self):
        self.assertEquals(["response"], self.rpc_client.call_me(arg1="hello"))

        self.assertEquals("http://10.10.10.1:8888/call_me", self.mock_http_url)
        self.assertEquals("arg1=hello", self.mock_http_kwargs)

    def testNamespace(self):
        self.rpc_client.namespace = "dir"

        self.assertEquals(["response"], self.rpc_client.call_me(arg1="hello"))

        self.assertEquals("http://10.10.10.1:8888/dir/call_me",
            self.mock_http_url)
        self.assertEquals("arg1=hello", self.mock_http_kwargs)

    def testServer(self):
        self.mock_controller = MockController()

        self.rpc_server = WSGIRPCServer("10.10.10.1", 8888)
        self.rpc_server.add_controller("controller1", self.mock_controller)

        self.assertEquals({'index': {'args': ['arg1']},
            'websock': {'args': ['arg1']}},
            self.rpc_server.controller_methods("controller1"))

        result = self.rpc_server.handle({'PATH_INFO': '/controller1/index',
            'wsgi.input': StringIO("arg1=howdy")},
            self._server_response)

        self.assertEquals('200 OK', self._server_code)
        self.assertEquals([('content-type', 'text/javascript'),
            ('content-length', 13)], self._server_lines)
        self.assertEquals('{"result": 1}', result)

        self.assertEquals("howdy", self.mock_controller.called)

    def testNonExposedMethod(self):
        self.mock_controller = MockController()

        self.rpc_server = WSGIRPCServer("10.10.10.1", 8888)
        self.rpc_server.add_controller("controller1", self.mock_controller)

        result = self.rpc_server.handle({'PATH_INFO': '/controller1/notexposed',
            'wsgi.input': StringIO("arg1=howdy")},
            self._server_response)

        self.assertEquals('404 Not Found', self._server_code)

        result = self.rpc_server.handle({'PATH_INFO': '/controller1/nothere',
            'wsgi.input': StringIO("arg1=howdy")},
            self._server_response)

        self.assertEquals('404 Not Found', self._server_code)

        result = self.rpc_server.handle({'PATH_INFO': '/nothere/nothere',
            'wsgi.input': StringIO("arg1=howdy")},
            self._server_response)

        self.assertEquals('404 Not Found', self._server_code)

        result = self.rpc_server.handle({'PATH_INFO': '/',
            'wsgi.input': StringIO("arg1=howdy")},
            self._server_response)

        self.assertEquals('404 Not Found', self._server_code)

        result = self.rpc_server.handle({'PATH_INFO': '',
            'wsgi.input': StringIO("arg1=howdy")},
            self._server_response)

        self.assertEquals('404 Not Found', self._server_code)

        result = self.rpc_server.handle({'PATH_INFO': '/1/2/3',
            'wsgi.input': StringIO("arg1=howdy")},
            self._server_response)

        self.assertEquals('404 Not Found', self._server_code)

    def testWebsocket(self):
        self.mock_controller = MockController()

        self.rpc_server = WSGIRPCServer("10.10.10.1", 8888)
        self.rpc_server.add_controller("controller1", self.mock_controller)

        self.assertEquals({'index': {'args': ['arg1']},
            'websock': {'args': ['arg1']}},
            self.rpc_server.controller_methods("controller1"))

        result = self.rpc_server.handle({'PATH_INFO': '/controller1/websock',
            'wsgi.input': StringIO("arg1=howdy"), 'wsgi.websocket': 'WSOBJ'},
            self._server_response)

        self.assertEquals('200 OK', self._server_code)
        self.assertEquals([('content-type', 'text/javascript'),
            ('content-length', 4)], self._server_lines)
        self.assertEquals('"OK"', result)

        self.assertEquals("howdy", self.mock_controller.called)
        self.assertEquals("WSOBJ", self.mock_controller.ws)

