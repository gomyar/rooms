
import unittest

from rooms.master import Master
from rooms.master import RegisteredNode
from rooms.player import Player
from rooms.rpc import RPCException
from rooms.rpc import RPCWaitException
from rooms.testutils import MockContainer
from rooms.testutils import MockRpcClient
from rooms.testutils import MockGame
from rooms.testutils import MockRoom


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
        self.rpc_conn = MockRpcClient(expect={"player_joins": "TOKEN",
            "request_token": "TOKEN"})

        self.master = Master(self.container)
        self.master._create_rpc_conn = lambda h, p: self.rpc_conn

    def testNodeAttach(self):
        self.master.register_node("10.10.10.1", 8000)
        self.assertEquals(1, len(self.master.nodes))

        node = self.master.nodes.values()[0]
        self.assertEquals("10.10.10.1", node.host)
        self.assertEquals(8000, node.port)

    def testNodeDeregister(self):
        self.master.register_node("10.10.10.1", 8000)
        self.master.request_room("game1", "room1")
        self.assertEquals(1, len(self.master.nodes))
        self.assertEquals(1, len(self.master.rooms))
        self.master.deregister_node("10.10.10.1", 8000)
        self.assertEquals(0, len(self.master.nodes))
        self.assertEquals(0, len(self.master.rooms))

    def testCreateRPCNodeConn(self):
        self.master = Master(self.container)
        conn = self.master._create_rpc_conn("10.10.10.1", 8000)
        self.assertEquals("node", conn.namespace)
        self.assertEquals("10.10.10.1", conn.host)
        self.assertEquals(8000, conn.port)

    def testCreateGame(self):
        self.master.register_node("10.10.10.1", 8000)

        game_id = self.master.create_game("bob")
        self.assertEquals("bob", self.container.games['game1'].owner_id)

        self.assertEquals([{'game_id': 'game1', 'owner_id': 'bob'}],
            self.master.all_games())

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

        self.assertEquals({}, self.container.players)
        node = self.master.join_game("bob", "game1", "room1")
        self.assertEquals({'node': ("10.10.10.1", 8000), 'token': 'TOKEN'},
            node)
        self.assertEquals('room1',
            self.container.players['bob', 'game1'].room_id)

        self.assertTrue(('bob', 'game1') in self.container.players)
        self.assertEquals({
            ('bob', 'game1'): Player("bob", "game1", room_id="room1")},
            self.container.players)

        self.assertEquals([
            ('manage_room', {'game_id': 'game1', 'room_id': 'room1'}),
            ('player_joins', {'game_id': 'game1', 'room_id': 'room1',
                'username': 'bob'})
        ], self.rpc_conn.called)

        self.assertEquals([{'game_id': 'game1', 'room_id': 'room1',
            'username': 'bob'}], self.master.players_in_game("game1"))

    def testManageRoom(self):
        self.master.register_node("10.10.10.1", 8000)
        self.master.create_game("bob")
        self.master.nodes['10.10.10.1', 8000].client = self.rpc_conn

        self.master.request_room("game1", "room1")

        self.assertEquals({('game1', 'room1'): ('10.10.10.1', 8000)},
            self.master.rooms)
        self.assertEquals(self.master.rooms.items(),
            self.master.managed_rooms())
        self.assertEquals([
            ('manage_room', {'game_id': 'game1', 'room_id': 'room1'}),
            ], self.rpc_conn.called)

    def testManageRoomAlreadyManaged(self):
        self.master.register_node("10.10.10.1", 8000)
        self.master.create_game("bob")
        self.master.nodes['10.10.10.1', 8000].client = self.rpc_conn

        self.master.rooms = {('game1', 'room1'): ('10.10.10.1', 8000)}

        self.assertEquals(("10.10.10.1", 8000),
            self.master.request_room("game1", "room1"))
        self.assertEquals([], self.rpc_conn.called)

    def testJoinGameRoomAlreadyManaged(self):
        # room managed, so don't call manage_room
        self.master.register_node("10.10.10.1", 8000)
        self.master.create_game("bob")
        self.master.nodes['10.10.10.1', 8000].client = self.rpc_conn
        self.master.rooms['game1', 'room1'] = ("10.10.10.1", 8000)

        self.assertEquals({('game1', 'room1'): ('10.10.10.1', 8000)},
            self.master.rooms)
        self.assertEquals([], self.rpc_conn.called)

    def testJoinGameNoNodes(self):
        self.assertRaises(RPCWaitException, self.master.join_game, "bob",
            "game1", "room1")

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

        self.assertEquals([{'host': '10.10.10.2', 'port': 8000, 'online': True},
            {'host': '10.10.10.1', 'port': 8000, 'online': True}],
            self.master.all_nodes())

    def testNodeOffliningQueueRoomRequests(self):
        self.master.create_game("bob")

        self.master.register_node("10.10.10.1", 8000)
        self.master.register_node("20.20.20.2", 8000)

        self.master.request_room("game1", "room1")
        self.master.request_room("game1", "room2")

        # receive offline signal
        self.master.offline_node("10.10.10.1", 8000)

        # receieve room request - send wait response
        self.assertRaises(RPCWaitException, self.master.join_game,
            "bob", "game1", "room1")

        # wait until room becomes available (from node)
        self.master.deregister_node("10.10.10.1", 8000)
        self.assertEquals({('game1', 'room2'): ('20.20.20.2', 8000)},
            self.master.rooms)

        # receive room request - normal room manage
        self.master.join_game("bob", "game1", "room1")

        self.assertEquals({('game1', 'room1'): ('20.20.20.2', 8000),
            ('game1', 'room2'): ('20.20.20.2', 8000)}, self.master.rooms)

    def testOfflineNonexistant(self):
        self.assertRaises(RPCException,
            self.master.offline_node,"10.10.10.1", 8000)

    def testPlayerConnects(self):
        self.master.create_game("bob")
        self.master.register_node("10.10.10.1", 8000)

        self.container.create_player("bob", "game1", "room1")

        self.assertEquals({'token': 'TOKEN', 'node': ('10.10.10.1', 8000)},
            self.master.player_connects("bob", "game1"))
        self.assertEquals({('game1', 'room1'): ('10.10.10.1', 8000)},
            self.master.rooms)

    def testManageRoomOnlyOnce(self):
        self.master.create_game("bob")
        self.master.register_node("10.10.10.1", 8000)
        self.master.register_node("10.10.10.2", 8000)

        self.master.join_game("bob", "game1", "room1")

        self.assertEquals([
            ('manage_room', {'game_id': 'game1', 'room_id': 'room1'}),
            ('player_joins', {'game_id': 'game1', 'room_id': 'room1',
                'username': 'bob'})], self.rpc_conn.called)

        self.master.request_room("game1", "room1")

        self.assertEquals([
            ('manage_room', {'game_id': 'game1', 'room_id': 'room1'}),
            ('player_joins', {'game_id': 'game1', 'room_id': 'room1',
                'username': 'bob'})], self.rpc_conn.called)

    def testAllRooms(self):
        self.master.create_game("bob")

        self.master.register_node("10.10.10.1", 8000)
        self.master.register_node("10.10.10.2", 8000)

        self.master.join_game("bob", "game1", "room1")
        self.master.join_game("ned", "game1", "room1")

        self.assertEquals({('game1', 'room1'): ('10.10.10.2', 8000)},
            self.master.rooms)
        self.assertEquals([
            ('manage_room', {'game_id': 'game1', 'room_id': 'room1'}),
            ('player_joins', {'game_id': 'game1', 'room_id': 'room1', 'username': 'bob'}),
            ('player_joins', {'game_id': 'game1', 'room_id': 'room1', 'username': 'ned'}),
        ], self.rpc_conn.called)
