
import unittest

from rooms.node import Node
from rooms.room import Room
from rooms.player import Player


class MockRoom(object):
    def __init__(self):
        self._kicked_off = False

    def kick(self):
        self._kicked_off = True


class MockContainer(object):
    def __init__(self, rooms=None, players=None):
        self.rooms = rooms or {}
        self.players = players or {}

    def load_room(self, game_id, room_id):
        return self.rooms[game_id, room_id]

    def load_player(self, player_id):
        return self.players[player_id]


class MockPlayerScript(object):
    def __init__(self):
        self.room = None
        self.player = None

    def player_joins(self, player, room):
        self.player = player
        self.room = room


class MockRpcClient(object):
    def __init__(self):
        self.registered_host = None
        self.registered_port = None

    def register_node(self, host, port):
        self.registered_host, self.registered_port = host, port


class NodeTest(unittest.TestCase):
    def setUp(self):
        self.player_script = MockPlayerScript()
        self.mock_rpc = MockRpcClient()
        self.room1 = MockRoom()
        self.player1 = Player("bob", "game1", "room1")
        self.container = MockContainer(rooms={("game1", "room1"): self.room1},
            players={"bob1": self.player1})
        self.node = Node("10.10.10.1", 8000, "master", 9000, self.container)
        self.node._create_token = lambda: "TOKEN1"
        self.node.player_script = self.player_script
        self.node.master_conn = self.mock_rpc

    def testManageRoom(self):
        self.node.manage_room("game1", "room1")

        self.assertEquals(1, len(self.node.rooms))
        self.assertTrue(self.room1._kicked_off)

    def testPlayerJoins(self):
        self.node.manage_room("game1", "room1")
        token = self.node.player_joins("bob", "game1", "room1")
        self.assertEquals("TOKEN1", token)

        self.assertEquals(1, len(self.node.players))
        self.assertEquals(self.player1, self.player_script.player)
        self.assertEquals(self.room1, self.player_script.room)

    def testConnectToMaster(self):
        self.node.connect_to_master()

        self.assertEquals("master", self.mock_rpc.registered_host)
        self.assertEquals(9000, self.mock_rpc.registered_port)
