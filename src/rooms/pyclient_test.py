
import unittest

from rooms.pyclient import RoomsConnection


class MockMaster(object):
    pass


class PyClientTest(unittest.TestCase):
    def setUp(self):
        self.client = RoomsConnection()
        self.master = MockMaster()
        self.client.master = self.master

    def testCreateGame(self):
        self.client.create_game("bob", info="someinfo")

    def testGameConnection(self):
        self.client.join_game("bob", "game1", "area1", "room1")
