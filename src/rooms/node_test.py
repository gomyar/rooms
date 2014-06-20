
import unittest
import gevent
from gevent.queue import Queue
import os
from urllib2 import HTTPError

from rooms.node import Node
from rooms.room import Room
from rooms.player import PlayerActor
from rooms.testutils import MockContainer
from rooms.testutils import MockRpcClient
from rooms.testutils import MockScript
from rooms.testutils import MockRoom
from rooms.testutils import MockTimer
from rooms.testutils import MockWebsocket
from rooms.testutils import MockActor
from rooms.testutils import MockRoomFactory
from rooms.rpc import RPCException
from rooms.position import Position
from rooms.actor import Actor
from rooms.node import PlayerConnection


class NodeTest(unittest.TestCase):
    def setUp(self):
        self.player_script = MockScript()
        self.game_script = MockScript()
        self.mock_script = MockScript()
        self.mock_rpc = MockRpcClient()
        self.node = Node("10.10.10.1", 8000, "master", 9000)
        self.node._create_token = lambda: "TOKEN1"
        self.node.scripts['player_script'] = self.player_script
        self.node.scripts['game_script'] = self.game_script
        self.node.scripts['mock_script'] = self.mock_script
        self.node.master_conn = self.mock_rpc
        self.room1 = Room("game1", "room1", Position(0, 0), Position(0, 0),
            self.node)
        self.room2 = Room("game1", "room2", Position(0, 0), Position(0, 0),
            self.node)
        self.container = MockContainer(room_factory=MockRoomFactory(self.room2))
        self.container.save_room(self.room1)
#        self.container.save_room(self.room2)
        self.node.container = self.container
        self.container.node = self.node
        MockTimer.setup_mock()

    def tearDown(self):
        MockTimer.teardown_mock()

    def testManageRoom(self):
        mock_script = MockScript()
        self.player1 = PlayerActor(self.room1, "player", mock_script,
            "bob")
        self.container.save_actor(self.player1)

        self.node.manage_room("game1", "room1")

        self.assertEquals(1, len(self.node.rooms))
        self.assertEquals([], mock_script.called)
        MockTimer.fast_forward(0)
        self.assertEquals([], mock_script.called)

    def testPlayerJoins(self):
        self.node.manage_room("game1", "room1")

        token = self.node.player_joins("ned", "game1", "room1")
        self.assertEquals("TOKEN1", token)

        player_actor = self.node.rooms['game1', 'room1'].actors['actors_0']
        room = self.node.rooms['game1', 'room1']
        self.assertEquals("ned", player_actor.username)
        self.assertEquals("room1", player_actor.room_id)
        self.assertEquals("game1", player_actor.game_id)
        self.assertEquals(1, len(self.node.player_connections))
        self.assertEquals(1, len(self.node.rooms["game1", "room1"].actors))
        self.assertEquals([
            ("player_joins", (player_actor, room), {})
        ], self.player_script.called)

    def testManageNonExistantRoom(self):
        self.node.manage_room("game1", "room2")
        self.assertEquals(2, len(self.container.dbase.dbases['rooms']))
        self.assertEquals([("room_created",
            (self.room2,), {})],
            self.game_script.called)

    def testConnectToMaster(self):
        self.node.connect_to_master()

        self.assertEquals([
            ('register_node', {'host': '10.10.10.1', 'port': 8000})],
            self.mock_rpc.called)

    def testDeregister(self):
        self.node.manage_room("game1", "room1")
        self.node.manage_room("game1", "room2")

        room1 = self.node.rooms["game1", "room1"]
        room2 = self.node.rooms["game1", "room2"]

        room1.put_actor(Actor(room1, "mock1", self.mock_script))
        room2.put_actor(Actor(room2, "mock1", self.mock_script))

        self.node.deregister()

        self.assertEquals([
            ('offline_node', {'host': '10.10.10.1', 'port': 8000}),
            ('deregister_node', {'host': '10.10.10.1', 'port': 8000})],
            self.mock_rpc.called)

        self.assertEquals(2, len(self.container.dbase.dbases['rooms']))
        self.assertEquals(2, len(self.container.dbase.dbases['actors']))

    def testOfflineBouncesAllConnectedToMaster(self):
        pass

    def testSerializeQueue(self):
        pass

    def testOfflineWaitsForSerializeQueue(self):
        pass

    def testAllPlayers(self):
        self.node.manage_room("game1", "room1")
        token = self.node.player_joins("bob", "game1", "room1")
        self.assertEquals([{'username': 'bob', 'game_id': 'game1',
            'token': 'TOKEN1', 'room_id': 'room1'}], self.node.all_players())

    def testAllRooms(self):
        self.player1 = PlayerActor(self.room1, "player", MockScript(),
            "bob")
        self.container.save_actor(self.player1)
        self.node.manage_room("game1", "room1")
        self.assertEquals([
            {'actors': [('actors_0',
              {u'actor_id': u'actors_0',
               u'actor_type': u'player',
               u'state': {},
               u'username': u'bob',
               u'vector': {u'end_pos': {u'x': 0.0, u'y': 0.0, u'z': 0.0},
                           u'end_time': 0.0,
                           u'start_pos': {u'x': 0.0,
                                          u'y': 0.0,
                                          u'z': 0.0},
                           u'start_time': 0.0}})],
              'game_id': 'game1',
              'room_id': 'room1'}],
            self.node.all_rooms())

    def testRequestToken(self):
        self.player1 = PlayerActor(self.room1, "player", MockScript(),
            "bob")
        self.container.save_actor(self.player1)

        self.node.manage_room("game1", "room1")
        token = self.node.request_token("bob", "game1")
        self.assertEquals("TOKEN1", token)

    def testRequestTokenInvalidPlayer(self):
        self.node.manage_room("game1", "room_other")
        self.player1 = PlayerActor(self.room1, "player", MockScript(),
            "bob")
        self.container.save_actor(self.player1)
        self.assertRaises(RPCException, self.node.request_token, "bob", "game1")

    def testRequestTokenNoSuchPlayer(self):
        self.node.manage_room("game1", "room_other")
        self.player1 = PlayerActor(self.room1, "player", MockScript(),
            "bob")
        self.container.save_actor(self.player1)
        self.assertRaises(RPCException, self.node.request_token, "bob", "game1")

    def testPlayerConnects(self):
        ws = MockWebsocket()
        gevent.spawn(self.node.ping, ws)

        MockTimer.fast_forward(0)
        self.assertEquals([0], ws.updates)

        MockTimer.fast_forward(1)
        self.assertEquals([0, 1], ws.updates)

        MockTimer.fast_forward(1)
        self.assertEquals([0, 1, 2], ws.updates)

        MockTimer.fast_forward(3)
        self.assertEquals([0, 1, 2, 3, 4, 5], ws.updates)

    def testActorCall(self):
        self.node.manage_room("game1", "room1")
        self.node.player_joins("bob", "game1", "room1")

        room1 = self.node.rooms["game1", "room1"]
        player_actor = room1.actors['actors_0']
        player_actor.script = MockScript()
        self.node.actor_call("game1", "bob", "player1", "TOKEN1",
            "do_something")

        # script calls happen on a gthread
        self.assertEquals([], player_actor.script.called)

        MockTimer.fast_forward(1)

        self.assertEquals([
            ('kickoff', (player_actor,), {}),
            ('do_something', (player_actor,), {})],
            player_actor.script.called)

    def testNonPlayerActorMovesNode(self):
        pass

    def testPlayerActorMovesToRoomManagedOnSameNodeAfterMasterBounce(self):
        pass

    def testPlayerConnectsQueueDisconnectsOnRedirect(self):
        # node.player_connects will fall out of the connection naturally when
        # a redirect is given
        pass

    def testActorEntered(self):
        self.node.manage_room("game1", "room1")

        actor = Actor(None, "test_actor", MockScript())
        actor._room_id = "room1"
        actor._game_id = "game1"
        self.container.save_actor(actor)

        self.node.actor_enters_node("actors_0")

        room = self.node.rooms['game1', 'room1']
        self.assertEquals(actor.actor_id, room.actors['actors_0'].actor_id)
        self.assertEquals(actor.room_id, room.actors['actors_0'].room_id)

    def testPlayerJoinsActorCreatedConnectionCreated(self):
        self.node.manage_room("game1", "room1")

        self.assertEquals(0, len(self.node.rooms['game1', 'room1'].actors))
        self.assertEquals(0, len(self.node.player_connections))

        self.assertEquals("TOKEN1",
            self.node.player_joins("ned", "game1", "room1"))

        self.assertEquals(PlayerActor,
            type(self.node.rooms['game1', 'room1'].actors['actors_0']))
        self.assertEquals("ned",
            self.node.rooms['game1', 'room1'].actors['actors_0'].username)
        self.assertEquals("actors_0",
            self.node.player_connections['ned', 'game1'].actor.actor_id)

    def testRoomManagedWithPlayerActorsPlayerConnectionsCreated(self):
        self.player1 = PlayerActor(self.room1, "player", MockScript(),
            "bob")
        self.container.save_actor(self.player1)

        self.node.manage_room("game1", "room1")

        self.assertEquals(1, len(self.node.rooms['game1', 'room1'].actors))
        self.assertEquals(1, len(self.node.player_connections))

        self.assertEquals(PlayerActor,
            type(self.node.rooms['game1', 'room1'].actors['actors_0']))
        self.assertEquals("bob",
            self.node.rooms['game1', 'room1'].actors['actors_0'].username)
        self.assertEquals("actors_0",
            self.node.player_connections['bob', 'game1'].actor.actor_id)

    def testLoadScriptsFromPath(self):
        script_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),
            "test_scripts")
        self.node.load_scripts(script_path)

        self.assertEquals("loaded", self.node.scripts['basic_actor'].call("test"))

    def testManageRoomWithPlayersAlreadyCreated(self):
        # save player
        mock_script = MockScript()
        self.player1 = PlayerActor(self.room1, "player", mock_script,
            "bob")
        self.container.save_actor(self.player1)

        # manage room
        self.node.manage_room("game1", "room1")

        # assert player actors in room
        room = self.node.rooms["game1", "room1"]
        actor = room.actors['actors_0']
        self.assertEquals("bob", actor.username)

        # assert player connections exist
        self.assertEquals(self.node.player_connections["bob", "game1"].actor,
            actor)

    def testManageRoomWithPlayersNotYetCreated(self):
        # save player
        mock_script = MockScript()
        self.player1 = PlayerActor(self.room2, "player", mock_script,
            "bob")
        self.container.save_actor(self.player1)

        # manage room
        self.node.manage_room("game1", "room2")

        # assert player actors in room
        room = self.node.rooms["game1", "room2"]
        actor = room.actors['actors_0']
        self.assertEquals("bob", actor.username)

        # assert player connections exist
        self.assertEquals(self.node.player_connections["bob", "game1"].actor,
            actor)

    def testActorMovesRoom(self):
        # manage room2
        self.node.manage_room("game1", "room1")
        self.node.manage_room("game1", "room2")

        # assert player actors in room2
        room1 = self.node.rooms["game1", "room1"]
        room2 = self.node.rooms["game1", "room2"]
        actor = room1.create_actor("npc", "mock_script")

        player_conn = PlayerConnection("game1", "bob", room1, actor, "TOKEN1")
        self.node.player_connections['player1', 'game1'] = player_conn
        queue = player_conn.new_queue()

        self.node._move_actor_room(actor, "game1", "room2", Position(10, 10))

        self.assertEquals("remove_actor", queue.get()['command'])
        #self.assertEquals({}, queue.get_nowait())

    def testStartReport(self):
        self.node.start_reporting()

        self.assertEquals([], self.mock_rpc.called)

        MockTimer.fast_forward(5)

        self.assertEquals([
            ('report_load_stats',
                {'host': '10.10.10.1', 'port': 8000, 'server_load': 0.0}),
            ]
        , self.mock_rpc.called)

        MockTimer.fast_forward(5)

        self.assertEquals([
            ('report_load_stats',
                {'host': '10.10.10.1', 'port': 8000, 'server_load': 0.0}),
            ('report_load_stats',
                {'host': '10.10.10.1', 'port': 8000, 'server_load': 0.0}),
            ]
        , self.mock_rpc.called)

        self.node.manage_room("game1", "room1")

        MockTimer.fast_forward(5)

        self.assertEquals([
            ('report_load_stats',
                {'host': '10.10.10.1', 'port': 8000, 'server_load': 0.0}),
            ('report_load_stats',
                {'host': '10.10.10.1', 'port': 8000, 'server_load': 0.0}),
            ('report_load_stats',
                {'host': '10.10.10.1', 'port': 8000, 'server_load': 0.01}),
            ]
        , self.mock_rpc.called)

    def testHandleRPCWaitExceptionOnActorEntersForNPC(self):
        self.mock_rpc.exceptions['actor_entered'] = HTTPError("/actor_enters",
            503, "Service Unavailable", {"retry-after": "3"}, None)

        self.node.manage_room("game1", "room1")

        room1 = self.node.rooms["game1", "room1"]
        actor = room1.create_actor("npc", "mock_script")

        self.node._move_actor_room(actor, "game1", "room2", Position(10, 10))

        # nothing happens
        self.mock_rpc.exceptions['actor_entered'] = HTTPError("/actor_enters",
            500, "Random Error", {}, None)

        self.node.manage_room("game1", "room1")

        room1 = self.node.rooms["game1", "room1"]
        actor = room1.create_actor("npc", "mock_script")

        self.node._move_actor_room(actor, "game1", "room2", Position(10, 10))

        # nothing happens

    def testHandleRPCWaitExceptionOnPlayerActorEnters(self):
        self.mock_rpc.exceptions['actor_entered'] = HTTPError("/actor_enters",
            503, "Service Unavailable", {"retry-after": "3"}, None)

        self.node.manage_room("game1", "room1")

        room1 = self.node.rooms["game1", "room1"]
        actor = room1.create_actor("npc", "mock_script")

        self.node._move_actor_room(actor, "game1", "room2", Position(10, 10))

        room1 = self.node.rooms["game1", "room1"]
        actor = PlayerActor(room1, "player", MockScript(), "bob", "actor1",
            "game1")
        self.room1.put_actor(actor)

        player_conn = PlayerConnection("game1", "bob", room1, actor, "TOKEN1")
        self.node.player_connections['bob', 'game1'] = player_conn
        queue = player_conn.new_queue()

        self.node._move_actor_room(actor, "game1", "room2", Position(10, 10))

        self.assertEquals({'command': 'redirect_to_master',
            'master': ['master', 9000]},
            queue.get_nowait())

    def testHandleAnyExceptionOnPlayerActorEnters(self):
        self.mock_rpc.exceptions['actor_entered'] = HTTPError("/actor_enters",
            500, "Random Error", {}, None)

        self.node.manage_room("game1", "room1")

        room1 = self.node.rooms["game1", "room1"]
        actor = room1.create_actor("npc", "mock_script")

        self.node._move_actor_room(actor, "game1", "room2", Position(10, 10))

        room1 = self.node.rooms["game1", "room1"]
        actor = PlayerActor(room1, "player", MockScript(), "bob", "actor1",
            "game1")
        self.room1.put_actor(actor)

        player_conn = PlayerConnection("game1", "bob", room1, actor, "TOKEN1")
        self.node.player_connections['bob', 'game1'] = player_conn
        queue = player_conn.new_queue()

        self.node._move_actor_room(actor, "game1", "room2", Position(10, 10))

        self.assertEquals({'command': 'redirect_to_master',
            'master': ['master', 9000]},
            queue.get_nowait())

    def testHandlePlayerActorEnters(self):
        self.mock_rpc.expect['actor_entered'] = {"node": ["10.10.10.1", 8000],
            "token": "TOKEN1"}

        self.node.manage_room("game1", "room1")

        room1 = self.node.rooms["game1", "room1"]
        actor = PlayerActor(room1, "player", MockScript(), "bob", "actor1",
            "game1")
        self.room1.put_actor(actor)

        player_conn = PlayerConnection("game1", "bob", room1, actor, "TOKEN1")
        self.node.player_connections['bob', 'game1'] = player_conn
        queue = player_conn.new_queue()

        self.node._move_actor_room(actor, "game1", "room2", Position(10, 10))

        self.assertEquals({'command': 'redirect', 'node': ['10.10.10.1', 8000],
            'token': 'TOKEN1'},
            queue.get_nowait())
