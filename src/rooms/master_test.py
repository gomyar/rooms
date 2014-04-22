
import unittest

from rooms.master import Master
from rooms.master import RegisteredNode
from rooms.player import Player


class MockContainer(object):
    def __init__(self):
        self.game = None

    def save_game(self, game):
        self.game = game
        game.game_id = "game1"


class MockNodeRpcClient(object):
    def __init__(self):
        self.called = []

    def join_game(self, username, game_id):
        self.called.append(('join_game', username, game_id))


class MasterTest(unittest.TestCase):
    def setUp(self):
        self.container = MockContainer()
        self.node = RegisteredNode("10.10.10.1", 8000, "rooms.com", 80)

        self.master = Master(self.container)
        self.rpc_client = MockNodeRpcClient()

    def testNodeAttach(self):
        self.master.register_node("10.10.10.1", 8000, "rooms.com", 80)

        self.assertEquals(1, len(self.master.nodes))
        self.assertEquals(RegisteredNode("10.10.10.1", 8000, "rooms.com", 80),
            self.master.nodes['10.10.10.1', 8000])

    def testCreateGame(self):
        self.master.nodes['10.10.10.1', 8000] = self.node

        game_id = self.master.create_game("bob")
        self.assertEquals(1, len(self.master.games))
        self.assertEquals("bob", self.container.game.owner_id)
        self.assertEquals(self.master.games.values()[0],
            self.container.game)
        self.assertEquals("game1", game_id)

    def testJoinGame(self):
        self.master.register_node("10.10.10.1", 8000, "rooms.com", 80)
        self.master.create_game("bob")
        self.master.nodes['10.10.10.1', 8000].client = self.rpc_client

        self.assertFalse(self.master.is_player_in_game("bob", "game1"))
        node = self.master.join_game("bob", "game1")
        self.assertEquals(self.node, node)

        self.assertEquals([Player("bob", "game1")],
            self.master.players_in_game("game1"))
        self.assertEquals(('10.10.10.1', 8000),
            self.master.player_map["bob", "game1"])
        self.assertTrue(self.master.is_player_in_game("bob", "game1"))

        self.assertEquals(('join_game', 'bob', 'game1'),
            self.rpc_client.called[0])

        self.assertEquals(RegisteredNode("10.10.10.1", 8000, "rooms.com", 80),
            self.master.get_node('bob', 'game1'))

    def testJoinGameNoSuchGame(self):
        pass

    def testJoinGamePlayerAlreadyJoined(self):
        pass
