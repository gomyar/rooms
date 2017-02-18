
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
from rooms.position import Position


class NodeTest(unittest.TestCase):
    def setUp(self):
        self.dbase = MockDbase()

        self.container = Container(self.dbase, None)

        self.node = Node(self.container, 'alpha', '192.168.0.11')
        self.container.node = self.node

        self.mock_script = Script("room_script", self)

        self.room = Room('game1', 'room1', None, self.mock_script)
        self.room.initialized = True

        self.player1 = PlayerActor(self.room, "test_player", self.mock_script,
                                   'bob', game_id='game1', actor_id='id1')
        self.room.put_actor(self.player1)

        self.container.save_room(self.room)
        self.container.save_player(self.player1)

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
        self.dbase.dbases['rooms']['rooms_0']['initialized'] = False

        self.assertEquals(0, len(self.node.rooms))
        self.container.request_create_room('game1', 'room1')
        self.node.load_next_pending_room()
        self.assertEquals(1, len(self.node.rooms))

        # test run init script if room.initialized == False
        room = self.node.rooms['game1', 'room1']
        self.assertTrue(room.state['testcreated'])
        self.assertEquals(1, len(room.actors))
        self.assertEquals('test', room.actors.values()[0].actor_type)

    def testLoadRoomAlreadyInitialized(self):
        self.dbase.dbases['rooms']['rooms_0']['state']['testcreated'] = False

        self.assertEquals(0, len(self.node.rooms))
        self.container.request_create_room('game1', 'room1')
        self.node.load_next_pending_room()
        self.assertEquals(1, len(self.node.rooms))

        # test run init script if room.initialized == False
        room = self.node.rooms['game1', 'room1']
        self.assertFalse(room.state['testcreated'])
        self.assertEquals(1, len(room.actors))
        self.assertTrue(room.start_actors.called)

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
        self.container.request_create_room('game1', 'room1')
        self.node.load_next_pending_room()
        self.assertEquals(1, len(self.node.rooms))

        self.assertFalse(self.room.state['testcreated'])
        self.assertEquals(1, len(self.room.actors))
        self.assertEquals('test_player',
            self.room.actors.values()[0].actor_type)
        self.assertTrue(self.room.start_actors.called)

    def testPlayerEntersRoom(self):
        # poll for limbo player_actor in managed room
        self.container.request_create_room('game1', 'room1')
        self.node.load_next_pending_room()

        self.assertEquals(1, len(self.node.rooms['game1', 'room1'].actors))

    def testPlayerConnects(self):
        # set up db objects
        self.container.create_player(self.room, 'test', MockScript(), 'bob',
            'game1')

        # init room (plus player)
        self.container.request_create_room('game1', 'room1')
        self.node.load_next_pending_room()

        room = self.node.rooms['game1', 'room1']

        # call websocket
        ws = MockWebsocket()

        WebsocketTest().call(self.node.player_connects, ws, 'game1', 'bob')

        # messages in queue propagated to websocket
        MockTimer.fast_forward(1)
        room.vision._send_command("id1", {'do': 'somthing'})
        MockTimer.fast_forward(1)

        self.assertEquals({u'do': u'somthing'}, ws.updates[2])

    def testPlayerDisconnted(self):
        self.container.request_create_room('game1', 'room1')
        self.node.load_next_pending_room()

        room = self.node.rooms['game1', 'room1']

        ws = MockWebsocket()

        WebsocketTest().call(self.node.player_connects, ws, 'game1', 'bob')

        MockTimer.fast_forward(1)
        room.vision._send_command("id1", {'command': 'disconnect'})
        MockTimer.fast_forward(1)

        self.assertEquals({u'command': u'disconnect'}, ws.updates[2])
        # empty queue means actor was disconnected
        self.assertEquals({}, self.room.vision.actor_queues)

    def testPlayerMovesRoomSameNode(self):
        self.room2 = Room('game1', 'room2', None, self.mock_script)
        self.room.initialized = True

        self.container.save_room(self.room2)

        self.container.request_create_room('game1', 'room1')
        self.container.request_create_room('game1', 'room2')

        self.node.load_next_pending_room()
        self.node.load_next_pending_room()

        room = self.node.rooms['game1', 'room1']
        room2 = self.node.rooms['game1', 'room2']

        ws = MockWebsocket()
        WebsocketTest().call(self.node.player_connects, ws, 'game1', 'bob')

        MockTimer.fast_forward(0)
        room.move_actor_room(self.player1, "room2", Position(0, 0))
        MockTimer.fast_forward(1)

        self.assertEquals({u'actor_id': u'id1', u'command': u'remove_actor'},
            ws.updates[2])
        self.assertEquals({u'command': u'move_room', u'room_id': u'room2'},
            ws.updates[3])

        # listening to messages from room2 queue
        room2.vision._send_command("id1", {'do': "something"})
        MockTimer.fast_forward(1)

        self.assertEquals(
            {u'do': u'something'},
            ws.updates[6])

    def testPlayerMovesRoomNotCurrentlyConnected(self):
        # if the player script moves the player to a different room, but the
        # player isn't currently connected, it throws an exception, it shouldnt
        pass

    def testPlayerMovesRoomOtherNode(self):
        self.container.request_create_room('game1', 'room1')
        self.node.load_next_pending_room()

        room = self.node.rooms['game1', 'room1']

        ws = MockWebsocket()
        WebsocketTest().call(self.node.player_connects, ws, 'game1', 'bob')

        MockTimer.fast_forward(0)
        room.move_actor_room(self.player1, "room2", Position(0, 0))
        MockTimer.fast_forward(1)

        self.assertEquals(
            {'command': 'redirect_to_master'}, ws.updates[-1])

    def testWrongPlayerConnects(self):
        self.dbase.dbases['actors'] = {'actors_1': {'room_id': "room2"}}
        self.container.create_player(None, 'test', MockScript(), 'bob', 'game1')
        self.dbase.dbases['actors']['actors_1']['room_id'] = "room1"
        try:
            ws = MockWebsocket()
            self.node.player_connects(ws, 'game1', 'bob')
        except Exception, e:
            self.assertEquals('No room for player: game1, bob', str(e))

    def testShutdownRoomsAndActorsSaved(self):
        self.container.request_create_room('game1', 'room1')
        self.node.load_next_pending_room()

        self.node.shutdown()

        self.assertEquals({'rooms_0': {u'__type__': u'Room',
                            '_id': 'rooms_0',
                            'active': False,
                            u'game_id': u'game1',
                            u'initialized': True,
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
        self.container.request_create_room('game1', 'room1')
        self.node.load_next_pending_room()

        ws = MockWebsocket()

        WebsocketTest().call(self.node.player_connects, ws, 'game1', 'bob')

        MockTimer.fast_forward(1)

        ' assert room in node'
        self.node.shutdown()

        MockTimer.fast_forward(1)

        # there's an extra actor update that shouldn't be there
        self.assertEquals(4, len(ws.updates))
        self.assertEquals(
            {u'command': u'sync',
             u'data': {u'now': 0,
                       u'player_actor': {u'actor_id': u'id1',
                            u'actor_type': u'test_player',
                            u'docked_with': None,
                            u'exception': None,
                            u'game_id': u'game1',
                            u'parent_id': None,
                            u'script': u'',
                            u'speed': 1.0,
                            u'state': {},
                            u'username': u'bob',
                            u'vector': {u'end_pos': {u'x': 0.0, u'y': 0.0,
                                                        u'z': 0.0},
                                        u'end_time': 0.0,
                            u'start_pos': {u'x': 0.0, u'y': 0.0, u'z': 0.0},
                                            u'start_time': 0},
                            u'visible': True},
                       u'room_id': u'room1',
                       u'username': u'bob'}}
        , ws.updates[0])

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
