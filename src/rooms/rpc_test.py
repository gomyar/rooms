
import unittest
from StringIO import StringIO

from rpc import WSGIRPCClient


class RPCTest(unittest.TestCase):
    def setUp(self):
        self.rpc_client = WSGIRPCClient("10.10.10.1", 8888)
        self.rpc_client.http_connect = self._http_connect
        self.mock_http_response = StringIO('["response"]')
        self.mock_http_url = None
        self.mock_http_kwargs = None

    def _http_connect(self, url, kwargs):
        self.mock_http_url = url
        self.mock_http_kwargs = kwargs
        return self.mock_http_response

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

