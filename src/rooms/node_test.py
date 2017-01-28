
import os
import unittest
from mock import Mock
from mock import patch

from rooms.container import Container
from rooms.node import Node
from rooms.room import Room
from rooms.testutils import MockDbase
from rooms.testutils import MockRoomBuilder
from rooms.testutils import MockRoom
from rooms.testutils import MockNode
from rooms.testutils import MockGeog
from rooms.testutils import MockScript
from rooms.testutils import MockWebsocket
from rooms.testutils import MockTimer
from rooms.testutils import WebsocketTest
from rooms.testutils import MockIDFactory
from rooms.room_builder import FileMapSource
from rooms.room_builder import RoomBuilder
from rooms.script import Script
from rooms.player import PlayerActor


class NodeTest(unittest.TestCase):
    def setUp(self):
        self.dbase = MockDbase()

        self.container = Container(self.dbase, None)

        self.mock_script = Script("room_script", self)

        self.node = Node(self.container, 'alpha', '192.168.0.11')
        self.container.node = self.node

        self.room = Room('game1', 'room1', self.node, self.mock_script)
        self.room.start_actors = Mock()

        self.container.load_next_pending_room = Mock(return_value=self.room)
        self.player1 = PlayerActor(self.room, "test", self.mock_script)

        MockTimer.setup_mock()
        MockIDFactory.setup_mock()

    def tearDown(self):
        MockTimer.teardown_mock()
        MockIDFactory.teardown_mock()

    @staticmethod
    def room_created(room):
        room.state['testcreated'] = True
        room.create_actor("test", None)

    @patch("gevent.spawn")
    def testStartNode(self, spawn):
        self.node.start()

        self.assertEquals(self.node.node_updater.update_loop,
                          spawn.call_args_list[0][0][0])
        self.assertEquals(self.node.room_loader.load_loop,
                          spawn.call_args_list[1][0][0])

    def testLoadRoomNotInitialized(self):
        self.assertEquals(0, len(self.node.rooms))
        self.node.load_next_pending_room()
        self.assertEquals(1, len(self.node.rooms))

        # test run init script if room.initialized == False
        self.assertTrue(self.room.state['testcreated'])
        self.assertEquals(1, len(self.room.actors))
        self.assertEquals('test', self.room.actors.values()[0].actor_type)
        self.assertTrue(self.room.start_actors.called)

    def testLoadRoomAlreadyInitialized(self):
        self.room.initialized = True
        self.room.state['testcreated'] = False

        self.assertEquals(0, len(self.node.rooms))
        self.node.load_next_pending_room()
        self.assertEquals(1, len(self.node.rooms))

        # test run init script if room.initialized == False
        self.assertFalse(self.room.state['testcreated'])
        self.assertEquals(0, len(self.room.actors))
        self.assertTrue(self.room.start_actors.called)

    def testLoadRoomAlreadyInitializedWithActors(self):
        self.dbase.dbases['actors'] = {}
        self.dbase.dbases['actors']['actor1'] = \
            {"__type__": "Actor", "_id": "actor1", "actor_id": "actor1",
            "_loadstate": None,
            "parent_id": None,
            "game_id": "game1", "room_id": "room1",
            "actor_type": "loaded", "model_type": "model",
            "speed": 1.0,
            "username": "ned",
            "docked_with": None,
            "visible": True,
            'state': {u'__type__': u'SyncDict'},
            "path": [], "vector": {"__type__": "Vector",
            "start_pos": {"__type__": "Position", "x": 0, "y": 0, "z": 0},
            "start_time": 0,
            "end_pos": {"__type__": "Position", "x": 0, "y": 10, "z": 0},
            "end_time": 10,
            }, "script_name": "mock_script"}

        self.room.initialized = True
        self.room.state['testcreated'] = False

        self.assertEquals(0, len(self.node.rooms))
        self.node.load_next_pending_room()
        self.assertEquals(1, len(self.node.rooms))

        self.assertFalse(self.room.state['testcreated'])
        self.assertEquals(1, len(self.room.actors))
        self.assertEquals('loaded', self.room.actors.values()[0].actor_type)
        self.assertTrue(self.room.start_actors.called)

    def testPlayerEntersRoom(self):
        # poll for limbo player_actor in managed room
        self.node.load_next_pending_room()

        self.assertEquals(1, len(self.node.rooms['game1', 'room1'].actors))

    def testPlayerConnects(self):
        self.container.create_player(None, 'test', MockScript(), 'bob', 'game1')
        self.node.load_next_pending_room()

        player_data = self.container.create_player_token("game1", "bob", 10)
        self.dbase.dbases['actors']['actors_0']['room_id'] = "room1"
        ws = MockWebsocket()

        WebsocketTest().call(self.node.player_connects, ws, player_data['token'])

        # messages in queue propagated to websocket
        MockTimer.fast_forward(1)
        self.room.vision._send_command("id1", {'do': 'somthing'})
        MockTimer.fast_forward(1)

        self.assertEquals([{u'do': u'somthing'}], ws.updates)

    def testPlayerDisconnted(self):
        self.container.create_player(None, 'test', MockScript(), 'bob', 'game1')
        self.node.load_next_pending_room()

        player_data = self.container.create_player_token("game1", "bob", 10)
        self.dbase.dbases['actors']['actors_0']['room_id'] = "room1"
        ws = MockWebsocket()

        WebsocketTest().call(self.node.player_connects, ws, player_data['token'])

        MockTimer.fast_forward(1)
        self.room.vision._send_command("id1", {'command': 'disconnect'})
        MockTimer.fast_forward(1)

        self.assertEquals([{u'command': u'disconnect'}], ws.updates)
        # empty queue means actor was disconnected
        self.assertEquals({}, self.room.vision.actor_queues)

    def testPlayerMovesRoomSameNode(self):
        self.room2 = Room('game1', 'room2', self.node, self.mock_script)

        self.node.load_next_pending_room()
        self.node.rooms['game1', 'room2'] = self.room2

        self.container.create_player(None, 'test', MockScript(), 'bob', 'game1')

        player_data = self.container.create_player_token("game1", "bob", 10)
        self.dbase.dbases['actors']['actors_1']['room_id'] = "room1"
        ws = MockWebsocket()
        WebsocketTest().call(self.node.player_connects, ws, player_data['token'])

        MockTimer.fast_forward(0)
        self.room.vision._send_command("id2", {'command': 'move_room', 'room_id': 'room2'})
        MockTimer.fast_forward(1)

        self.assertEquals([{u'command': u'move_room', u'room_id': u'room2'}], ws.updates)

        # listening to messages from room2 queue
        self.room2.vision._send_command("id2", {'do': "something"})
        MockTimer.fast_forward(1)

        self.assertEquals([
            {u'command': u'move_room', u'room_id': u'room2'},
            {u'do': u'something'}],
            ws.updates)

    def testPlayerMovesRoomOtherNode(self):
        self.node.load_next_pending_room()

        self.container.create_player(None, 'test', MockScript(), 'bob', 'game1')

        player_data = self.container.create_player_token("game1", "bob", 10)
        self.dbase.dbases['actors']['actors_1']['room_id'] = "room1"
        ws = MockWebsocket()
        WebsocketTest().call(self.node.player_connects, ws, player_data['token'])

        MockTimer.fast_forward(0)
        self.room.vision._send_command("id2", {'command': 'move_room', 'room_id': 'room2'})
        MockTimer.fast_forward(1)

        self.assertEquals([
            {'command': 'redirect_to_master'}], ws.updates)

    def testWrongPlayerConnects(self):
        self.dbase.dbases['actors'] = {'actors_1': {'room_id': "room2"}}
        self.container.create_player(None, 'test', MockScript(), 'bob', 'game1')
        self.dbase.dbases['actors']['actors_1']['room_id'] = "room1"
        try:
            player_data = self.container.create_player_token("game1", "bob", 10)
            ws = MockWebsocket()
            self.node.player_connects(ws, player_data['token'])
        except Exception, e:
            self.assertEquals('No room for player: game1, room1', str(e))

    def testShutdownRoomsAndActorsSaved(self):
        room1 = Room('game1', 'room1', self.node, MockScript())
        self.node.rooms['game1', 'room1'] = room1

        self.node.shutdown()

        self.assertEquals({'rooms_0': {u'__type__': u'Room',
                            '_id': 'rooms_0',
                            'active': False,
                            u'game_id': u'game1',
                            u'initialized': False,
                            u'last_modified': u'1970-01-01T00:00:00',
                            u'node_name': u'alpha',
                            'requested': False,
                            u'room_id': u'room1',
                            u'state': {}}}
        , self.container.dbase.dbases['rooms'])

    def testStartupCleanDBRoomsWithNodeName(self):
        self.dbase.dbases['rooms'] = {
            'rooms_0': {u'__type__': u'Room',
                        '_id': 'rooms_0',
                        'active': False,
                        u'game_id': u'game1',
                        u'initialized': False,
                        u'last_modified': u'1970-01-01T00:00:00',
                        u'node_name': u'alpha',
                        'requested': False,
                        u'room_id': u'room1',
                        u'state': {}},
            'rooms_1': {u'__type__': u'Room',
                        '_id': 'rooms_0',
                        'active': False,
                        u'game_id': u'game1',
                        u'initialized': False,
                        u'last_modified': u'1970-01-01T00:00:00',
                        u'node_name': u'beta',
                        'requested': False,
                        u'room_id': u'room1',
                        u'state': {}},
        }
        self.node.start()

        self.assertEquals(None, self.dbase.dbases['rooms']['rooms_0']['node_name'])
        self.assertEquals('beta', self.dbase.dbases['rooms']['rooms_1']['node_name'])

    def testShutdownSendDisconnectToPlayerConnections(self):
        self.container.create_player(None, 'test', MockScript(), 'bob', 'game1')
        self.node.load_next_pending_room()

        player_data = self.container.create_player_token("game1", "bob", 10)
        self.dbase.dbases['actors']['actors_0']['room_id'] = "room1"
        ws = MockWebsocket()

        WebsocketTest().call(self.node.player_connects, ws, player_data['token'])

        MockTimer.fast_forward(1)

        ' assert room in node'
        self.node.shutdown()

        MockTimer.fast_forward(1)

        self.assertEquals([
            {u'actor_id': u'id2',
                u'command': u'actor_update',
                u'data': {u'actor_id': u'id2',
                            u'actor_type': u'test',
                            u'docked_with': None,
                            u'exception': None,
                            u'game_id': u'game1',
                            u'parent_id': None,
                            u'script': u'',
                            u'speed': 1.0,
                            u'state': {},
                            u'username': None,
                            u'vector': {u'end_pos': {u'x': 0.0, u'y': 0.0, u'z': 0.0},
                                        u'end_time': 1.0,
                                        u'start_pos': {u'x': 0.0, u'y': 0.0, u'z': 0.0},
                                        u'start_time': 1},
                            u'visible': True}},
            {u'command': u'disconnect'}], ws.updates)

    def testPlayerConnectsTwice(self):
        # a player which connects twice should get a new player_actor the
        # first time, with a websocket connection, and a new websocket
        # connection to the same player actor the second time
        pass

    def testCheckTokenOnPlayerCommand(self):
        pass

    def testGetNextPendingRoom(self):
        # queryupdate mongo for next pending room:
        #   state='pending' order by 'state_changed_time'
        #   update state='active', node_id=self.id
        pass

    def testDeactivateRoom(self):
        # need to stop actor loading for that room - change ActorLoader

        # mark rooms as internally inactive (won't accept any more players)
        # stop gthreads
        # write state='inactive', node_id=None to room
        # disconnect players
        pass

    def testBrokenRoomRecovery(self):
        # when a node starts up, check for 'active' rooms with its node id
        # if any found, mark all as 'pending'
        pass

    def testOnMoveRoomTryToPickUpRoomIfNotAlreadyInService(self):
        pass

    def testOnMoveRoomIfRoomInServiceRedirectToOtherNode(self):
        pass

    def testDontLoadRoomIfMemoryGreaterThen80(self):
        pass

    def testSerializeRoomIfUnconnectedAndmemoryGreaterThen60(self):
        pass

    def testAdminConnects(self):
        # request admin token

        # connect with admin token
        pass
