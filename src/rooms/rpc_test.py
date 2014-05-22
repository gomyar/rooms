
import unittest
import os

from StringIO import StringIO

from rpc import WSGIRPCClient
from rpc import WSGIRPCServer
from rpc import request
from rpc import websocket
from rpc import RPCWaitException


class MockController(object):
    def __init__(self):
        self.called = None
        self.ws = None

    @request
    def index(self, arg1):
        '''docstr'''
        self.called = arg1
        return {'result': 1}

    @request
    def urlbased(self, urlparam1, urlparam2, kwarg1=None, kwarg2=None):
        self.called = (urlparam1, urlparam2, kwarg1, kwarg2)
        return {'result': 1}

    def notexposed(self, arg1):
        raise Exception("Should never be called")

    @websocket
    def websock(self, ws, arg1):
        '''docstr'''
        self.called = arg1
        self.ws = ws
        return "OK"

    @request
    def bounce(self):
        raise RPCWaitException("unavailable")


class MockControllerException(object):
    @request
    def callme(self):
        raise Exception("Test exception")


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
        self.assertEquals(["response"], self.rpc_client.call("call_me",
            arg1="hello"))

        self.assertEquals("http://10.10.10.1:8888/call_me", self.mock_http_url)
        self.assertEquals("arg1=hello", self.mock_http_kwargs)

    def testNamespace(self):
        self.rpc_client.namespace = "dir"

        self.assertEquals(["response"], self.rpc_client.call("call_me",
            arg1="hello"))

        self.assertEquals("http://10.10.10.1:8888/dir/call_me",
            self.mock_http_url)
        self.assertEquals("arg1=hello", self.mock_http_kwargs)

    def testServer(self):
        self.mock_controller = MockController()

        self.rpc_server = WSGIRPCServer("10.10.10.1", 8888)
        self.rpc_server.add_controller("controller1", self.mock_controller)

        self.assertEquals({'index': {'args': ['arg1'], 'doc': 'docstr',
                'type': 'request'},
            'bounce': {'args': [], 'doc': '', 'type': 'request'},
            'websock': {'args': ['arg1'], 'doc': 'docstr',
                'type': 'websocket'},
            'urlbased': {'args': ['urlparam1', 'urlparam2', 'kwarg1', 'kwarg2'],
                'doc': '',
                'type': 'request'},
            },
            self.rpc_server.controller_methods("controller1"))

        result = self.rpc_server.handle({'PATH_INFO': '/controller1/index',
            'wsgi.input': StringIO("arg1=howdy")},
            self._server_response)

        self.assertEquals('200 OK', self._server_code)
        self.assertEquals([('content-type', 'application/json'),
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

        result = self.rpc_server.handle({'PATH_INFO': '/nonexistant',
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

        self.assertEquals({'index': {'args': ['arg1'], 'doc': 'docstr',
            'type': 'request'},
            'bounce': {'args': [], 'doc': '', 'type': 'request'},
            'websock': {'args': ['arg1'], 'doc': 'docstr',
                'type': 'websocket'},
            'urlbased': {'args': ['urlparam1', 'urlparam2', 'kwarg1', 'kwarg2'],
                'doc': '', 'type': 'request'},
            },
            self.rpc_server.controller_methods("controller1"))

        result = self.rpc_server.handle({'PATH_INFO': '/controller1/websock',
            'QUERY_STRING': 'arg1=howdy', 'wsgi.websocket': 'WSOBJ'},
            self._server_response)

        self.assertEquals('200 OK', self._server_code)
        self.assertEquals([('content-type', 'application/json'),
            ('content-length', 4)], self._server_lines)
        self.assertEquals('"OK"', result)

        self.assertEquals("howdy", self.mock_controller.called)
        self.assertEquals("WSOBJ", self.mock_controller.ws)

    def testRequestException(self):
        self.mock_controller = MockControllerException()

        self.rpc_server = WSGIRPCServer("10.10.10.1", 8888)
        self.rpc_server.add_controller("controller1", self.mock_controller)

        result = self.rpc_server.handle({'PATH_INFO': '/controller1/callme',
            'wsgi.input': StringIO("")},
            self._server_response)

        self.assertEquals('500', self._server_code)
        self.assertEquals([('content-type', 'text/javascript'),
            ('content-length', 432)], self._server_lines)
        self.assertTrue(
            'Server Error calling controller1/callme():\nTraceback' in result)

    def testRPCFileIndexRedirect(self):
        self.rpc_server = WSGIRPCServer("10.10.10.1", 8888)

        result = self.rpc_server.handle({'PATH_INFO': '/',
            'wsgi.input': StringIO("")},
            self._server_response)

        self.assertEquals('302 Found', self._server_code)
        self.assertEquals([('location', '/rpc/index.html')],
            self._server_lines)

    def testRPCFiles(self):
        self.rpc_server = WSGIRPCServer("10.10.10.1", 8888)

        result = self.rpc_server.handle({'PATH_INFO': '/rpc/index.html',
            'wsgi.input': StringIO("")},
            self._server_response)

        self.assertEquals('200 OK', self._server_code)
        self.assertEquals([('content-type', ('text/html', None))],
            self._server_lines)

    def testWaitExceptionTemporarilyUnavailable(self):
        self.mock_controller = MockController()

        self.rpc_server = WSGIRPCServer("10.10.10.1", 8888)
        self.rpc_server.add_controller("controller1", self.mock_controller)

        result = self.rpc_server.handle({'PATH_INFO': '/controller1/bounce',
            'wsgi.input': StringIO("")},
            self._server_response)

        self.assertEquals('503 Service Unavailable', self._server_code)
        self.assertEquals([('retry-after', '3')], self._server_lines)

    def testFileRootController(self):
        self.rpc_server = WSGIRPCServer("10.10.10.1", 8888)
        self.rpc_server.add_file_root("/assets", os.path.join(
            os.path.dirname(__file__), "assets/test/assets1"))
        self.rpc_server.add_file_root("/", os.path.join(
            os.path.dirname(__file__), "assets/test/root"))

        result = self.rpc_server.handle({'PATH_INFO': '/assets/test.html',
            'wsgi.input': StringIO("")},
            self._server_response)

        self.assertEquals('200 OK', self._server_code)
        self.assertEquals([('content-type', ('text/html', None))],
            self._server_lines)
        self.assertEquals(["<html>test</html>\n"], result)

    def testUrlParams(self):
        self.mock_controller = MockController()

        self.rpc_server = WSGIRPCServer("10.10.10.1", 8888)
        self.rpc_server.add_controller("controller1", self.mock_controller)

        result = self.rpc_server.handle({'PATH_INFO':
                '/controller1/urlbased/value1/value2',
            'wsgi.input': StringIO("kwarg1=howdy&kwarg2=there")},
            self._server_response)

        self.assertEquals('200 OK', self._server_code)
        self.assertEquals([('content-type', 'application/json'),
            ('content-length', 13)], self._server_lines)
        self.assertEquals('{"result": 1}', result)

        self.assertEquals(("value1", "value2", "howdy", "there"),
            self.mock_controller.called)


