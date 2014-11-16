
import unittest

from rooms.pyclient import RoomsConnection


class MockMaster(object):
    def __init__(self):
        self._commands = {
            "master_game/join_game":
                dict(node=("localhost", 8080), token="TOKEN"),
            "master_game/create_game":
                None,
        }

    def call(self, method, **kwargs):
        return self._commands[method]


class PyClientTest(unittest.TestCase):
    def setUp(self):
        self.client = RoomsConnection()
        self.master = MockMaster()
        self.client.master = self.master
        self.client._connect_to_node = lambda host, port, token, game_id: None

    def testCreateGame(self):
        self.client.create_game("bob", info="someinfo")

    def testGameConnection(self):
        self.client.join_game("bob", "game1", "area1", "room1")
