
import unittest
import os

from rooms.master import Master
from rooms.master import RegisteredNode
from rooms.player import PlayerActor
from rooms.container import Container
from rooms.rpc import RPCException
from rooms.rpc import RPCWaitException
from rooms.testutils import MockDbase
from rooms.testutils import MockRpcClient
from rooms.testutils import MockGame
from rooms.testutils import MockRoom
from rooms.testutils import MockActor
from rooms.testutils import MockScript
from rooms.testutils import MockTimer


class MockNodeRpcClient(object):
    def __init__(self):
        self.called = []

    def player_joins(self, username, game_id, room_id, param=None):
        self.called.append(('player_joins', username, game_id, room_id, param))
        return "TOKEN"

    def manage_room(self, game_id, room_id):
        self.called.append(('manage_room', game_id, room_id))


class MasterTest(unittest.TestCase):
    def setUp(self):
        self.dbase = MockDbase()
        self.container = Container(self.dbase, None)
        self.rpc_conn = MockRpcClient(expect={"player_joins": "TOKEN",
            "request_token": "TOKEN"})

        self.master = Master(self.container)
        self.master._create_rpc_conn = lambda h, p: self.rpc_conn
        self.master.scripts['game_script'] = MockScript(
            expect={"start_room": "room1"})
        MockTimer.setup_mock()

    def tearDown(self):
        MockTimer.teardown_mock()

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
        self.assertEquals("node_control", conn.namespace)
        self.assertEquals("10.10.10.1", conn.host)
        self.assertEquals(8000, conn.port)

    def testCreateGame(self):
        self.master.register_node("10.10.10.1", 8000)

        game_id = self.master.create_game("bob")
        self.assertEquals("bob",
            self.container.dbase.dbases['games']['games_0']['owner_id'])

        self.assertEquals([{'game_id': 'games_0', 'owner_id': 'bob'}],
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

        self.assertEquals({}, self.container.dbase.dbases['actors'])
        node = self.master.join_game("bob", "games_0")
        self.assertEquals({'node': ("10.10.10.1", 8000), 'token': 'TOKEN',
            'url': 'http://10.10.10.1:8000/assets/index.html?token=TOKEN&game_id=games_0&username=bob'},
            node)

        self.assertEquals([
            ('manage_room', {'game_id': 'games_0', 'room_id': 'room1'}),
            ('player_joins', {'game_id': 'games_0', 'room_id': 'room1',
                'username': 'bob'})
        ], self.rpc_conn.called)

    def testJoinGameNonexistant(self):
        self.master.register_node("10.10.10.1", 8000)
        self.assertRaises(Exception, self.master.join_game, "bob",
            "nonexistant")

    def testPlayersInGame(self):
        self.container.save_actor(PlayerActor(
            MockRoom("game1", "room1"), 'player', MockScript(), "bob"))
        self.assertEquals([{'game_id': 'game1', 'room_id': 'room1',
            'username': 'bob'}], self.master.players_in_game("game1"))

    def testManageRoom(self):
        self.master.register_node("10.10.10.1", 8000)
        self.master.create_game("bob")
        self.master.nodes['10.10.10.1', 8000].client = self.rpc_conn

        self.master.request_room("game1", "room1")

        self.assertEquals(('10.10.10.1', 8000),
            self.master.rooms['game1', 'room1'].node)
        self.assertEquals("game1",
            self.master.rooms['game1', 'room1'].game_id)
        self.assertEquals("room1",
            self.master.rooms['game1', 'room1'].room_id)

        self.assertEquals([
            {'node': ('10.10.10.1', 8000), 'game_id': 'game1',
                'room_id': 'room1', 'online': True}],
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
        self.master.create_game("bob")
        self.assertRaises(RPCWaitException, self.master.join_game, "bob",
            "games_0")

    def testJoinGamePlayerAlreadyJoined(self):
        self.master.register_node("10.10.10.1", 8000)
        self.master.create_game("bob")
        self.master.nodes['10.10.10.1', 8000].client = self.rpc_conn

        # Player exists
        self.container.save_actor(PlayerActor(
            MockRoom("games_0", "room1"), 'player', MockScript(), "bob"))

        self.assertRaises(RPCException, self.master.join_game, "bob", "games_0")

    def testJoinGameTwoGamesTwoNodes(self):
        self.master.register_node("10.10.10.1", 8000)
        game_1 = self.master.create_game("bob")
        node1 = self.master.join_game("bob", "games_0")

        self.master.register_node("10.10.10.2", 8000)
        game_2 = self.master.create_game("bob")
        node2 = self.master.join_game("bob", "games_1")

        self.assertEquals({'node': ("10.10.10.1", 8000), 'token': 'TOKEN',
            'url': 'http://10.10.10.1:8000/assets/index.html?token=TOKEN&game_id=games_0&username=bob'},
            node1)
        self.assertEquals({'node': ("10.10.10.2", 8000), 'token': 'TOKEN',
            'url': 'http://10.10.10.2:8000/assets/index.html?token=TOKEN&game_id=games_1&username=bob'},
            node2)

        self.assertEquals([
            {'host': '10.10.10.2', 'port': 8000, 'online': True, 'load': 0.0},
            {'host': '10.10.10.1', 'port': 8000, 'online': True, 'load': 0.0}],
            self.master.all_nodes())

    def testNodeOffliningQueueRoomRequests(self):
        self.assertEquals("games_0", self.master.create_game("bob"))

        self.master.register_node("10.10.10.1", 8000)
        self.master.register_node("20.20.20.2", 8000)

        self.master.request_room("games_0", "room1")

        self.master.report_load_stats("10.10.10.1", 8000, 0.1, '{}')

        self.master.request_room("games_0", "room2")

        # receive offline signal
        self.master.offline_node("10.10.10.1", 8000)

        # receieve room request - send wait response
        self.assertRaises(RPCWaitException, self.master.join_game,
            "bob", "games_0")

        # wait until room becomes available (from node)
        self.master.deregister_node("10.10.10.1", 8000)

        self.assertEquals(('20.20.20.2', 8000),
            self.master.rooms['games_0', 'room2'].node)
        self.assertEquals("games_0",
            self.master.rooms['games_0', 'room2'].game_id)
        self.assertEquals("room2",
            self.master.rooms['games_0', 'room2'].room_id)

        # receive room request - normal room manage
        self.master.join_game("bob", "games_0")

        self.assertEquals(('20.20.20.2', 8000),
            self.master.rooms['games_0', 'room1'].node)
        self.assertEquals("games_0",
            self.master.rooms['games_0', 'room1'].game_id)
        self.assertEquals("room1",
            self.master.rooms['games_0', 'room1'].room_id)

        self.container.save_actor(PlayerActor(
            MockRoom("games_0", "room1"), 'player', MockScript(), "bob"))

        # offline the second node
        self.master.deregister_node("20.20.20.2", 8000)

        # attempt player connect
        self.assertRaises(RPCWaitException, self.master.player_connects,
            "bob", "games_0")

    def testOfflineNonexistant(self):
        self.assertRaises(RPCException,
            self.master.offline_node,"10.10.10.1", 8000)

    def testPlayerConnects(self):
        self.master.create_game("bob")
        self.master.register_node("10.10.10.1", 8000)

        player = self.container.create_player(MockRoom("game1", "room1"),
            "player", MockScript(), "bob", "game1")

        self.assertEquals({'token': 'TOKEN', 'node': ('10.10.10.1', 8000)},
            self.master.player_connects("bob", "game1"))
        self.assertEquals(('10.10.10.1', 8000),
            self.master.rooms['game1', 'room1'].node)
        self.assertEquals("game1",
            self.master.rooms['game1', 'room1'].game_id)
        self.assertEquals("room1",
            self.master.rooms['game1', 'room1'].room_id)

    def testManageRoomOnlyOnce(self):
        self.master.create_game("bob")
        self.master.register_node("10.10.10.1", 8000)
        self.master.register_node("10.10.10.2", 8000)

        self.master.join_game("bob", "games_0")

        self.assertEquals([
            ('manage_room', {'game_id': 'games_0', 'room_id': 'room1'}),
            ('player_joins', {'game_id': 'games_0', 'room_id': 'room1',
                'username': 'bob'})], self.rpc_conn.called)

        self.master.request_room("games_0", "room1")

        self.assertEquals([
            ('manage_room', {'game_id': 'games_0', 'room_id': 'room1'}),
            ('player_joins', {'game_id': 'games_0', 'room_id': 'room1',
                'username': 'bob'})], self.rpc_conn.called)

    def testAllRooms(self):
        self.master.create_game("bob")

        self.master.register_node("10.10.10.1", 8000)
        self.master.register_node("10.10.10.2", 8000)

        self.master.join_game("bob", "games_0")
        self.master.join_game("ned", "games_0")

        self.assertEquals(('10.10.10.2', 8000),
            self.master.rooms['games_0', 'room1'].node)
        self.assertEquals("games_0",
            self.master.rooms['games_0', 'room1'].game_id)
        self.assertEquals("room1",
            self.master.rooms['games_0', 'room1'].room_id)

        self.assertEquals([
            ('manage_room', {'game_id': 'games_0', 'room_id': 'room1'}),
            ('player_joins', {'game_id': 'games_0', 'room_id': 'room1', 'username': 'bob'}),
            ('player_joins', {'game_id': 'games_0', 'room_id': 'room1', 'username': 'ned'}),
        ], self.rpc_conn.called)

    def testReportServerLoad(self):
        self.master.create_game("bob")

        self.master.register_node("10.10.10.1", 8000)

        self.master.report_load_stats("10.10.10.1", 8000, 0.5, '{}')

        self.assertEquals(0.5,
            self.master.nodes["10.10.10.1", 8000].server_load())

    def testReportConnectedPlayers(self):
        self.master.scripts['game_script'].expect = {"start_room": "map1.room2"}
        self.master.create_game("bob")

        self.master.register_node("10.10.10.1", 8000)
        self.master.register_node("10.10.10.2", 8000)

        self.master.join_game("bob", "games_0")
        self.master.scripts['game_script'].expect = {"start_room": "map1.room1"}
        self.master.join_game("ned", "games_0")

        self.master.report_load_stats("10.10.10.1", 8000, 0.5,
            '{"games_0.map1.room2": {"connected_players": 1}}')

        self.assertEquals(0,
            self.master.rooms["games_0", "map1.room1"].connected_players)
        self.assertEquals(1,
            self.master.rooms["games_0", "map1.room2"].connected_players)


    def testRoomOfflineQueueRoomRequests(self):
        self.master.scripts['game_script'].expect = {"start_room": "map1.room1"}
        self.assertEquals("games_0", self.master.create_game("bob"))

        self.master.register_node("10.10.10.1", 8000)

        self.master.request_room("games_0", "map1.room1")
        self.master.request_room("games_0", "map1.room2")

        self.master.rooms["games_0", "map1.room1"].online = False

        # receieve room request - send wait response
        self.assertRaises(RPCWaitException, self.master.join_game,
            "bob", "games_0")

        self.container.save_actor(PlayerActor(
            MockRoom("games_0", "map1.room1"), 'player', MockScript(), "bob"))
        self.assertRaises(RPCWaitException, self.master.player_connects,
            "bob", "games_0")

        self.master.scripts['game_script'].expect = {"start_room": "map1.room2"}
        self.master.join_game("ned", "games_0")

        self.container.save_actor(PlayerActor(
            MockRoom("games_0", "map1.room2"), 'player', MockScript(), "ned"))
        self.master.player_connects("ned", "games_0")

    def testRoomManagerRemovesUnneededRoomsOnBusyNodes(self):
        self.master.register_node("10.10.10.1", 8000)

        self.master.request_room("games_0", "room1")
        self.master.request_room("games_0", "room2")

        self.master.rooms["games_0", "room1"].connected_players = 1
        self.master.nodes['10.10.10.1', 8000].load = 0.1

        # Dont deactivate if uptime < 15 seconds
        self.master.run_cleanup_rooms()

        self.assertEquals(
            [('manage_room', {'game_id': 'games_0', 'room_id': 'room1'}),
            ('manage_room', {'game_id': 'games_0', 'room_id': 'room2'}),
#            ('deactivate_room', {'game_id': 'games_0', 'room_id': 'room2'}),
            ]
        , self.rpc_conn.called)
        self.assertTrue(self.master.rooms["games_0", "room1"].online)
        self.assertTrue(self.master.rooms["games_0", "room2"].online)

        # Node must have been up for 30 seconds before allowing room deactivate
        MockTimer.fast_forward(16)

        self.master.run_cleanup_rooms()

        self.assertEquals(
            [('manage_room', {'game_id': 'games_0', 'room_id': 'room1'}),
            ('manage_room', {'game_id': 'games_0', 'room_id': 'room2'}),
            ('deactivate_room', {'game_id': 'games_0', 'room_id': 'room2'}),
            ]
        , self.rpc_conn.called)
        self.assertTrue(("games_0", "room1") in self.master.rooms)
        self.assertFalse(("games_0", "room2") in self.master.rooms)

    def testRoomManagerRemovesUnneededRoomsOnBusyNodesByUpTime(self):
        self.master.register_node("10.10.10.1", 8000)

        self.master.request_room("games_0", "room1")
        MockTimer.fast_forward(10)
        self.master.request_room("games_0", "room2")

        self.master.rooms["games_0", "room1"].connected_players = 0
        self.master.rooms["games_0", "room2"].connected_players = 0

        # Dont deactivate if uptime < 15 seconds
        self.master.run_cleanup_rooms()

        self.assertEquals(
            [('manage_room', {'game_id': 'games_0', 'room_id': 'room1'}),
            ('manage_room', {'game_id': 'games_0', 'room_id': 'room2'}),
#            ('deactivate_room', {'game_id': 'games_0', 'room_id': 'room2'}),
            ]
        , self.rpc_conn.called)

        # Node must have been up for 15 seconds before allowing room deactivate
        MockTimer.fast_forward(10)

        self.master.run_cleanup_rooms()

        self.assertEquals(
            [('manage_room', {'game_id': 'games_0', 'room_id': 'room1'}),
            ('manage_room', {'game_id': 'games_0', 'room_id': 'room2'}),
            ('deactivate_room', {'game_id': 'games_0', 'room_id': 'room1'}),
            ]
        , self.rpc_conn.called)

        # Node must have been up for 15 seconds before allowing room deactivate
        MockTimer.fast_forward(10)

        self.master.run_cleanup_rooms()

        self.assertEquals(
            [('manage_room', {'game_id': 'games_0', 'room_id': 'room1'}),
            ('manage_room', {'game_id': 'games_0', 'room_id': 'room2'}),
            ('deactivate_room', {'game_id': 'games_0', 'room_id': 'room1'}),
            ('deactivate_room', {'game_id': 'games_0', 'room_id': 'room2'}),
            ]
        , self.rpc_conn.called)

    def testAllGamesForPlayer(self):
        self.master.register_node("10.10.10.1", 8000)

        game_id = self.master.create_game("bob")
        game = self.container.load_game('games_0')
        self.assertEquals("games_0", game_id)
        self.master.join_game("ned", "games_0")

        self.assertEquals("games_0",
            self.master.all_managed_games_for("bob")[0]['game_id'])

    def testAllPlayersForPlayer(self):
        player = PlayerActor(
            MockRoom("game1", "room1"), 'player', MockScript(), "bob")
        self.container.save_actor(player)

        self.assertEquals([], self.master.all_players_for("ned"))
        self.assertEquals("bob", self.master.all_players_for("bob")[0]['username'])

    def testLoadScriptsFromPath(self):
        script_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),
            "test_scripts")
        self.master.load_scripts(script_path)

        self.assertEquals("loaded", self.master.scripts['basic_actor'].call("test", MockActor()))
        self.assertEquals(
            {'move_to':
                {'args': ['actor', 'x', 'y'], 'doc': '', 'type': 'request'},
            'ping': {'args': ['actor'], 'doc': '', 'type': 'request'},
            'test': {'args': ['actor'], 'doc': '', 'type': 'request'}}
        , self.master.inspect_script("basic_actor"))
