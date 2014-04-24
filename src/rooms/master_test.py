
import unittest

from rooms.master import Master
from rooms.master import RegisteredNode
from rooms.player import Player
from rooms.exception import RPCException


class MockContainer(object):
    def __init__(self):
        self.game = None
        self.index = 1

    def save_game(self, game):
        self.game = game
        game.game_id = "game%s" % (self.index,)
        self.index += 1


class MockNodeRpcClient(object):
    def __init__(self):
        self.called = []

    def join_game(self, username, game_id):
        self.called.append(('join_game', username, game_id))


class MockGameScript(object):
    def player_joins(self, game, player):
        player.room_id = "room1"
        #player.create_actor("player_script")


class MasterTest(unittest.TestCase):
    def setUp(self):
        self.container = MockContainer()
        self.rpc_conn = MockNodeRpcClient()
        self.game_script = MockGameScript()

        self.master = Master(self.container, self.game_script)
        self.master._create_rpc_conn = lambda h, p: self.rpc_conn

    def testNodeAttach(self):
        self.master.register_node("10.10.10.1", 8000, "rooms.com", 80)
        self.assertEquals(1, len(self.master.nodes))

        node = self.master.nodes.values()[0]
        self.assertEquals("10.10.10.1", node.host)
        self.assertEquals(8000, node.port)
        self.assertEquals("rooms.com", node.external_host)
        self.assertEquals(80, node.external_port)

    def testCreateGame(self):
        self.master.register_node("10.10.10.1", 8000, "rooms.com", 80)

        game_id = self.master.create_game("bob")
        self.assertEquals(1, len(self.master.games))
        self.assertEquals("bob", self.container.game.owner_id)
        self.assertEquals(self.master.games.values()[0],
            self.container.game)
        self.assertEquals("game1", game_id)

    def testJoinGame(self):
        self.master.register_node("10.10.10.1", 8000, "rooms.com", 80)
        self.master.create_game("bob")
        self.master.nodes['10.10.10.1', 8000].client = self.rpc_conn

        self.assertFalse(self.master.is_player_in_game("bob", "game1"))
        node = self.master.join_game("bob", "game1")
        self.assertEquals("10.10.10.1", node.host)
        self.assertEquals(8000, node.port)

        self.assertEquals([Player("bob", "game1", room_id="room1")],
            self.master.players_in_game("game1"))
        self.assertEquals(('10.10.10.1', 8000),
            self.master.player_map["bob", "game1"])
        self.assertTrue(self.master.is_player_in_game("bob", "game1"))

        self.assertEquals(('join_game', 'bob', 'game1'),
            self.rpc_conn.called[0])

        self.assertEquals(RegisteredNode("10.10.10.1", 8000, "rooms.com", 80,
            self.rpc_conn), self.master.get_node('bob', 'game1'))

    def testJoinGameNoSuchGame(self):
        self.assertRaises(RPCException, self.master.join_game, "bob", "game1")

    def testJoinGamePlayerAlreadyJoined(self):
        self.master.register_node("10.10.10.1", 8000, "rooms.com", 80)
        self.master.create_game("bob")
        self.master.nodes['10.10.10.1', 8000].client = self.rpc_conn

        self.master.join_game("bob", "game1")

        self.assertRaises(RPCException, self.master.join_game, "bob", "game1")

    def testJoinGameTwoGamesTwoNodes(self):
        self.master.register_node("10.10.10.1", 8000, "rooms.com", 80)
        game_1 = self.master.create_game("bob")
        node1 = self.master.join_game("bob", "game1")

        self.master.register_node("10.10.10.2", 8000, "rooms.com", 80)
        game_2 = self.master.create_game("bob")
        node2 = self.master.join_game("bob", "game2")

        self.assertEquals(("10.10.10.1", 8000), (node1.host, node1.port))
        self.assertEquals(("10.10.10.2", 8000), (node2.host, node2.port))
