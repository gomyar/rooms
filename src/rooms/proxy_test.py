
import unittest

from rooms.proxy import Proxy


class ProxyTest(unittest.TestCase):
    def setUp(self):
        self.proxy = Proxy("localhost", 80, "master", 8000)

    def testPlayerJoins(self):
#        self.fail()
        pass
