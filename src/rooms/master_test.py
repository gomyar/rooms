
import unittest

from rooms.master import Master
from rooms.master import RegisteredNode
from rooms.player import Player
from rooms.exception import RPCException


class MockContainer(object):
    def __init__(self):
        self.game = None
        self.index = 1
        self.player = None

    def save_game(self, game):
        self.game = game
        game.game_id = "game%s" % (self.index,)
        self.index += 1

    def save_player(self, player):
        self.player = player


class MockNodeRpcClient(object):
    def __init__(self):
        self.called = []

    def player_joins(self, username, game_id, room_id):
        self.called.append(('player_joins', username, game_id, room_id))
        return "TOKEN"

    def manage_room(self, game_id, room_id):
        self.called.append(('manage_room', game_id, room_id))


class MasterTest(unittest.TestCase):
    def setUp(self):
        self.container = MockContainer()
        self.rpc_conn = MockNodeRpcClient()

        self.master = Master(self.container)
        self.master._create_rpc_conn = lambda h, p: self.rpc_conn

    def testNodeAttach(self):
        self.master.register_node("10.10.10.1", 8000)
        self.assertEquals(1, len(self.master.nodes))

        node = self.master.nodes.values()[0]
        self.assertEquals("10.10.10.1", node.host)
        self.assertEquals(8000, node.port)

    def testCreateGame(self):
        self.master.register_node("10.10.10.1", 8000)

        game_id = self.master.create_game("bob")
        self.assertEquals(1, len(self.master.games))
        self.assertEquals("bob", self.container.game.owner_id)
        self.assertEquals(self.master.games.values()[0],
            self.container.game)
        self.assertEquals("game1", game_id)

    def testCantRegisterNodeTwice(self):
        self.master.register_node("10.10.10.1", 8000)
        self.assertRaises(RPCException, self.master.register_node,
            "10.10.10.1", 8000)

        # can register different one though
        self.master.register_node("10.10.10.2", 8000)
        self.assertEquals(2, len(self.master.nodes))

    def testJoinGame(self):
        self.master.register_node("10.10.10.1", 8000)
        self.master.create_game("bob")
        self.master.nodes['10.10.10.1', 8000].client = self.rpc_conn

        self.assertFalse(self.master.is_player_in_game("bob", "game1"))
        node = self.master.join_game("bob", "game1", "room1")
        self.assertEquals({'node': ("10.10.10.1", 8000), 'token': 'TOKEN'},
            node)
        self.assertEquals('room1', self.master.players['bob', 'game1'].room_id)

        self.assertEquals([Player("bob", "game1", room_id="room1")],
            self.master.players_in_game("game1"))
        self.assertEquals(('10.10.10.1', 8000),
            self.master.player_map["bob", "game1"])
        self.assertTrue(self.master.is_player_in_game("bob", "game1"))

        # room not yet managed
        self.assertEquals(('manage_room', 'game1', 'room1'),
            self.rpc_conn.called[0])
        # player must be added to room
        self.assertEquals(('player_joins', 'bob', 'game1', 'room1'),
            self.rpc_conn.called[1])

        self.assertEquals(("10.10.10.1", 8000),
            self.master.get_node('bob', 'game1'))

    def testManageRoom(self):
        self.master.register_node("10.10.10.1", 8000)
        self.master.create_game("bob")
        self.master.nodes['10.10.10.1', 8000].client = self.rpc_conn

        self.master.manage_room('10.10.10.1', 8000, "game1", "room1")

        self.assertEquals({('game1', 'room1'): ['10.10.10.1', 8000]},
            self.master.rooms)
        self.assertEquals(('manage_room', 'game1', 'room1'),
            self.rpc_conn.called[0])

    def testManageRoomAlreadyManaged(self):
        self.master.register_node("10.10.10.1", 8000)
        self.master.create_game("bob")
        self.master.nodes['10.10.10.1', 8000].client = self.rpc_conn

        self.master.manage_room('10.10.10.1', 8000, "game1", "room1")
        self.assertRaises(RPCException, self.master.manage_room,
            '10.10.10.1', 8000, "game1", "room1")

    def testJoinGameRoomAlreadyManaged(self):
        # room managed, so don't call manage_room

        # still call add_player
        pass

    def testJoinGameNoSuchGame(self):
        self.assertRaises(RPCException, self.master.join_game, "bob", "game1",
            "room1")

    def testJoinGamePlayerAlreadyJoined(self):
        self.master.register_node("10.10.10.1", 8000)
        self.master.create_game("bob")
        self.master.nodes['10.10.10.1', 8000].client = self.rpc_conn

        self.master.join_game("bob", "game1", "room1")

        self.assertRaises(RPCException, self.master.join_game, "bob", "game1",
            "room1")

    def testJoinGameTwoGamesTwoNodes(self):
        self.master.register_node("10.10.10.1", 8000)
        game_1 = self.master.create_game("bob")
        node1 = self.master.join_game("bob", "game1", "room1")

        self.master.register_node("10.10.10.2", 8000)
        game_2 = self.master.create_game("bob")
        node2 = self.master.join_game("bob", "game2", "room1")

        self.assertEquals({'node': ("10.10.10.1", 8000), 'token': 'TOKEN'},
            node1)
        self.assertEquals({'node': ("10.10.10.2", 8000), 'token': 'TOKEN'},
            node2)

        self.assertEquals([{'host': '10.10.10.2', 'port': 8000},
            {'host': '10.10.10.1', 'port': 8000}], self.master.all_nodes())
