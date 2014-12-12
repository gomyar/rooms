
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
from rooms.testutils import MockIDFactory
from rooms.rpc import RPCException
from rooms.rpc import RPCWaitException
from rooms.position import Position
from rooms.actor import Actor
from rooms.node import PlayerConnection
from rooms.room_factory import RoomFactory
from rooms.room_factory import FileMapSource


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
        self.room1 = Room("game1", "map1.room1", Position(0, 0), Position(10, 10),
            self.node)
        self.room2 = Room("game1", "map1.room2", Position(0, 0), Position(10, 10),
            self.node)
        self.container = MockContainer(
            room_factory=RoomFactory(
            FileMapSource(os.path.join(os.path.dirname(__file__),
            "test_maps")), self.node))
        self.container.save_room(self.room1)
        self.node.container = self.container
        self.container.node = self.node
        MockTimer.setup_mock()
        MockIDFactory.setup_mock()

    def tearDown(self):
        MockTimer.teardown_mock()
        MockIDFactory.teardown_mock()

    def testManageRoom(self):
        mock_script = MockScript()
        self.player1 = PlayerActor(self.room1, "player", mock_script,
            "bob")
        self.container.save_actor(self.player1)

        self.node.manage_room("game1", "map1.room1")

        self.assertEquals(1, len(self.node.rooms))
        self.assertEquals([], mock_script.called)
        MockTimer.fast_forward(0)
        self.assertEquals([], mock_script.called)

    def testPlayerJoins(self):
        self.node.manage_room("game1", "map1.room1")

        token = self.node.player_joins("ned", "game1", "map1.room1")
        self.assertEquals("TOKEN1", token)

        player_actor = self.node.rooms['game1', 'map1.room1'].actors['id1']
        room = self.node.rooms['game1', 'map1.room1']
        self.assertEquals("ned", player_actor.username)
        self.assertEquals("map1.room1", player_actor.room_id)
        self.assertEquals("game1", player_actor.game_id)
        self.assertEquals(1, len(self.node.player_connections))
        self.assertEquals(1, len(self.node.connections))
        self.assertEquals("game1", self.node.connections['TOKEN1'].game_id)
        self.assertEquals(1, len(self.node.rooms["game1", "map1.room1"].actors))
        self.assertEquals([
            ("player_joins", (player_actor,), {})
        ], self.player_script.called)

    def testManageNonExistantRoom(self):
        self.node.manage_room("game1", "map1.room2")
        self.assertEquals(2, len(self.container.dbase.dbases['rooms']))
        self.assertEquals("room_created",
            self.game_script.called[0][0])

    def testConnectToMaster(self):
        self.node.connect_to_master()

        self.assertEquals([
            ('register_node', {'host': '10.10.10.1', 'port': 8000})],
            self.mock_rpc.called)

    def testDeregister(self):
        self.node.manage_room("game1", "map1.room1")
        self.node.manage_room("game1", "map1.room2")

        room1 = self.node.rooms["game1", "map1.room1"]
        room2 = self.node.rooms["game1", "map1.room2"]

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
        self.node.manage_room("game1", "map1.room1")
        token = self.node.player_joins("bob", "game1", "map1.room1")
        self.assertEquals([{'username': 'bob', 'game_id': 'game1',
            'token': 'TOKEN1', 'room_id': 'map1.room1'}], self.node.all_players())

    def testAllRooms(self):
        self.player1 = PlayerActor(self.room1, "player", MockScript(),
            "bob")
        self.container.save_actor(self.player1)
        self.node.manage_room("game1", "map1.room1")
        expected = [
            {'actors': [('id1',
              {u'actor_id': u'id1',
               u'actor_type': u'player',
               u'game_id': u'game1',
               u'speed': 1.0,
               u'state': {},
               u'username': u'bob',
               u'docked_with': None,
               u'docked_actors': [],
               u'visible': True,
               u'vector': {u'end_pos': {u'x': 0.0, u'y': 0.0, u'z': 0.0},
                           u'end_time': 0.0,
                           u'start_pos': {u'x': 0.0,
                                          u'y': 0.0,
                                          u'z': 0.0},
                           u'start_time': 0.0}})],
              'game_id': 'game1',
              'room_id': 'map1.room1'}]
        self.assertEquals(expected,
            self.node.all_rooms())

    def testRequestToken(self):
        self.player1 = PlayerActor(self.room1, "player", MockScript(),
            "bob")
        self.container.save_actor(self.player1)

        self.node.manage_room("game1", "map1.room1")
        token = self.node.request_token("bob", "game1")
        self.assertEquals("TOKEN1", token)

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
        self.node.manage_room("game1", "map1.room1")
        self.node.player_joins("bob", "game1", "map1.room1")

        room1 = self.node.rooms["game1", "map1.room1"]
        player_actor = room1.actors['id1']
        player_actor.script = MockScript()
        self.node.actor_call("game1", "TOKEN1", "do_something")

        # script calls happen on a gthread
        self.assertEquals([], player_actor.script.called)

        MockTimer.fast_forward(1)

        self.assertEquals([
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

    def testInvalidToken(self):
        self.node.connections['BOBSTOKEN'] = PlayerConnection('game1',
            'bob', None, None, "BOBSTOKEN")
        try:
            self.node.player_connects(None, 'game1', 'WRONGTOKEN')
        except Exception, e:
            self.assertEquals("Invalid token for player", str(e))

    def testPlayerJoinsActorCreatedConnectionCreated(self):
        self.node.manage_room("game1", "map1.room1")

        self.assertEquals(0, len(self.node.rooms['game1', 'map1.room1'].actors))
        self.assertEquals(0, len(self.node.player_connections))

        self.assertEquals("TOKEN1",
            self.node.player_joins("ned", "game1", "map1.room1"))

        self.assertEquals(PlayerActor,
            type(self.node.rooms['game1', 'map1.room1'].actors['id1']))
        self.assertEquals("ned",
            self.node.rooms['game1', 'map1.room1'].actors['id1'].username)
        self.assertEquals("id1",
            self.node.player_connections['ned', 'game1'].actor_id)

    def testRoomManagedWithPlayerActorsNoPlayerConnectionsCreated(self):
        self.player1 = PlayerActor(self.room1, "player", MockScript(),
            "bob")
        self.container.save_actor(self.player1)

        self.node.manage_room("game1", "map1.room1")

        self.assertEquals(1, len(self.node.rooms['game1', 'map1.room1'].actors))
        self.assertEquals(0, len(self.node.player_connections))

        self.assertEquals(PlayerActor,
            type(self.node.rooms['game1', 'map1.room1'].actors['id1']))
        self.assertEquals("bob",
            self.node.rooms['game1', 'map1.room1'].actors['id1'].username)

    def testLoadScriptsFromPath(self):
        script_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),
            "test_scripts")
        self.node.load_scripts(script_path)

        self.assertEquals("loaded", self.node.scripts['basic_actor'].call("test", MockActor()))

    def testManageRoomWithPlayersAlreadyCreated(self):
        # save player
        mock_script = MockScript()
        self.player1 = PlayerActor(self.room1, "player", mock_script,
            "bob")
        self.container.save_actor(self.player1)

        # manage room
        self.node.manage_room("game1", "map1.room1")

        # assert player actors in room
        room = self.node.rooms["game1", "map1.room1"]
        actor = room.actors['id1']
        self.assertEquals("bob", actor.username)

        # assert player connections exist
        self.assertEquals(self.node.player_connections, {})

    def testManageRoomWithPlayersNotYetCreated(self):
        # save player
        mock_script = MockScript()
        self.player1 = PlayerActor(self.room2, "player", mock_script,
            "bob")
        self.container.save_actor(self.player1)

        # manage room
        self.node.manage_room("game1", "map1.room2")

        # assert player actors in room
        room = self.node.rooms["game1", "map1.room2"]
        actor = room.actors['id1']
        self.assertEquals("bob", actor.username)

        # assert player connections exist
        self.assertEquals(self.node.player_connections, {})

    def testActorMovesRoom(self):
        # manage room2
        self.node.manage_room("game1", "map1.room1")
        self.node.manage_room("game1", "map1.room2")
        token = self.node.player_joins("ned", "game1", "map1.room1")

        # assert player actors in room2
        room1 = self.node.rooms["game1", "map1.room1"]
        room2 = self.node.rooms["game1", "map1.room2"]
        actor = room1.actors[self.node.connections[token].actor_id]

        queue = room1.vision.connect_vision_queue("id1")

        room1.move_actor_room(actor, "map1.room2", Position(10, 10))

        self.assertEquals("sync", queue.get_nowait()['command'])
        self.assertEquals("actor_update", queue.get_nowait()['command'])
        self.assertEquals("actor_update", queue.get_nowait()['command'])
        self.assertEquals("move_room", queue.get_nowait()['command'])
        self.assertEquals("remove_actor", queue.get_nowait()['command'])

        # maybe add another listener in the second room later

    def testStartReport(self):
        self.node.start_reporting()

        self.assertEquals([], self.mock_rpc.called)

        MockTimer.fast_forward(5)

        self.assertEquals([
            ('report_load_stats',
                {'host': '10.10.10.1', 'port': 8000, 'server_load': 0.0,
                    'node_info': '{}'}),
            ]
        , self.mock_rpc.called)

        MockTimer.fast_forward(5)

        self.assertEquals([
            ('report_load_stats',
                {'host': '10.10.10.1', 'port': 8000, 'server_load': 0.0,
                    'node_info': '{}'}),
            ('report_load_stats',
                {'host': '10.10.10.1', 'port': 8000, 'server_load': 0.0,
                    'node_info': '{}'}),
            ]
        , self.mock_rpc.called)

        self.node.manage_room("game1", "map1.room1")

        MockTimer.fast_forward(5)

        self.assertEquals([
            ('report_load_stats',
                {'host': '10.10.10.1', 'port': 8000, 'server_load': 0.0,
                    'node_info': '{}'}),
            ('report_load_stats',
                {'host': '10.10.10.1', 'port': 8000, 'server_load': 0.0,
                    'node_info': '{}'}),
            ('report_load_stats',
                {'host': '10.10.10.1', 'port': 8000, 'server_load': 0.01,
                    'node_info': '{"game1.map1.room1": {"connected_players": 0}}'}),
            ]
        , self.mock_rpc.called)

    def testHandlePlayerActorEnters(self):
        self.mock_rpc.exceptions['actor_entered'] = Exception("anything")

        self.node.manage_room("game1", "map1.room1")

        room1 = self.node.rooms["game1", "map1.room1"]
        queue = room1.vision.connect_vision_queue("id1")
        actor = room1.create_actor("npc", "mock_script")

        room1.move_actor_room(actor, "room2", Position(10, 10))

        self.assertEquals("sync", queue.get_nowait()["command"])
        self.assertEquals("actor_update", queue.get_nowait()["command"])
        self.assertEquals("actor_update", queue.get_nowait()["command"])
        self.assertEquals("move_room", queue.get_nowait()["command"])
        self.assertEquals("remove_actor", queue.get_nowait()["command"])

    def testDeactivateRoom(self):
        self.node.manage_room("game1", "map1.room1")
        self.node.manage_room("game1", "map1.room2")

        room1 = self.node.rooms["game1", "map1.room1"]
        room2 = self.node.rooms["game1", "map1.room2"]
        actor1 = room1.create_actor("npc",
            "mock_script")
        actor2 = room2.create_actor("npc",
            "mock_script")

        # expecting saves so blank dbase
        self.container.dbase.dbases = {}

        self.node.deactivate_room("game1", "map1.room2")

        self.assertEquals({('game1', 'map1.room1'): room1}, self.node.rooms)
        self.assertEquals(1, len(self.container.dbase.dbases['actors']))
        self.assertEquals(1, len(self.container.dbase.dbases['rooms']))

    def testMoveActorBetweenRoomsWhenDestinationIsOffline(self):
        pass

    def testAdminConnects(self):
        self.node.manage_room("game1", "map1.room1")
        token = self.node.request_admin_token("game1", "map1.room1")

        room1 = self.node.rooms["game1", "map1.room1"]
        self.assertEquals("map1.room1", self.node.admin_connections[token].room_id)

    def testPropagateActorEvents(self):
        self.node.manage_room("game1", "map1.room1")
        room = self.node.rooms["game1", "map1.room1"]
        queue = room.vision.connect_vision_queue("id1")
        token = self.node.player_joins("ned", "game1", "map1.room1")
        actor = room.actors.values()[0]

        self.assertEquals("sync", queue.get_nowait()['command'])
        self.assertEquals("actor_update", queue.get_nowait()['command'])
        self.assertTrue(queue.empty())

        actor.state.something = "value"
        self.assertEquals('actor_update', queue.get_nowait()['command'])

        actor.visible = False
        self.assertEquals('actor_update', queue.get_nowait()['command'])

        actor.state.something = "value"
        self.assertEquals('actor_update', queue.get_nowait()['command'])

        actor.visible = True
        self.assertEquals('actor_update', queue.get_nowait()['command'])
