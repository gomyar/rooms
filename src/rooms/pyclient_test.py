
import unittest

from rooms.pyclient import RoomsConnection


class MockMaster(object):
    def create_game(self, owner_username, **options):
        pass

    def join_game(self, username, game_id, start_area_id, start_room_id):
        return dict(host="localhost", port=8080, token="TOKEN")


class PyClientTest(unittest.TestCase):
    def setUp(self):
        self.client = RoomsConnection()
        self.master = MockMaster()
        self.client.master = self.master
        self.client._connect_to_node = lambda host, port, token: None

    def testCreateGame(self):
        self.client.create_game("bob", info="someinfo")

    def testGameConnection(self):
        self.client.join_game("bob", "game1", "area1", "room1")
