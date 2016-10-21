
import os
import unittest
from mock import Mock

from rooms.container import Container
from rooms.mongo_node import Node
from rooms.room import Room
from rooms.geography.basic_geography import BasicGeography
from rooms.testutils import MockDbase
from rooms.testutils import MockRoomBuilder
from rooms.testutils import MockRoom
from rooms.testutils import MockNode
from rooms.testutils import MockGeog
from rooms.room_builder import FileMapSource
from rooms.room_builder import RoomBuilder
from rooms.script import Script
from rooms.player import PlayerActor


class NodeTest(unittest.TestCase):
    def setUp(self):
        self.dbase = MockDbase()
        self.geography = MockGeog()

        self.container = Container(self.dbase, None)

        self.mock_script = Script("room_script", self)

        self.node = Node(self.container, 'alpha')
        self.container.node = self.node

        self.room = Room('game1', 'room1', self.node, self.mock_script)
        self.room.kick = Mock()

        self.container.load_next_pending_room = Mock(return_value=self.room)
        self.player1 = PlayerActor(self.room, "test", self.mock_script)

    @staticmethod
    def room_created(room):
        room.state['testcreated'] = True
        room.create_actor("test", None)

    def testLoadRoomNotInitialized(self):

        self.assertEquals(0, len(self.node.rooms))
        self.node.load_next_pending_room()
        self.assertEquals(1, len(self.node.rooms))

        # test run init script if room.initialized == False
        self.assertTrue(self.room.state['testcreated'])
        self.assertEquals(1, len(self.room.actors))
        self.assertEquals('test', self.room.actors.values()[0].actor_type)
        self.assertTrue(self.room.kick.called)

    def testLoadRoomAlreadyInitialized(self):
        self.room.initialized = True
        self.room.state['testcreated'] = False

        self.assertEquals(0, len(self.node.rooms))
        self.node.load_next_pending_room()
        self.assertEquals(1, len(self.node.rooms))

        # test run init script if room.initialized == False
        self.assertFalse(self.room.state['testcreated'])
        self.assertEquals(0, len(self.room.actors))
        self.assertTrue(self.room.kick.called)

    def testLoadRoomAlreadyInitializedWithActors(self):
        self.dbase.dbases['actors'] = {}
        self.dbase.dbases['actors']['actor1'] = \
            {"__type__": "Actor", "_id": "actor1", "actor_id": "actor1",
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
        self.assertTrue(self.room.kick.called)

    def testPlayerEntersRoom(self):
        # poll for limbo player_actor in managed room
        self.node.load_next_pending_room()

        self.assertEquals(1, len(self.node.rooms['game1', 'room1'].actors))

        self.container.load_limbo_actor = Mock(return_value=self.player1)
        self.node.actor_loader._load_actors()

        self.assertEquals(2, len(self.node.rooms['game1', 'room1'].actors))

    def testPlayerConnects(self):
        self.node.player_connects("bob", "game1", "TOKEN1")

        # get room for player/game_id
        # add/get player_actor to room - check token against saved token
        # establish websocket

    def testPlayerMovesRoom(self):
        # query for room node - change to pending (find_and_modify)
        # bounce to node if exists
        # else wait (refer to master? or wait at node until other room comes up)

        # addendum to this test - if a player connects to a node where the
        # playeractor just got moved and hasn't yet been picked up by the
        # normal actor load queue, the playeractor is immediately loaded
        pass

    def testPlayerConnectsTwice(self):
        # a player which connects twice should get a new player_actor the
        # first time, with a websocket connection, and a new websocket
        # connection to the same player actor the second time
        pass

    def testGetNextPendingRoom(self):
        # queryupdate mongo for next pending room:
        #   state='pending' order by 'state_changed_time'
        #   update state='active', node_id=self.id
        pass

    def testDeactivateRoom(self):
        # mark rooms as internally inactive (won't accept any more players)
        # stop gthreads
        # write state='inactive', node_id=None to room
        # disconnect players
        pass

    def testBrokenRoomRecovery(self):
        # when a node starts up, check for 'active' rooms with its node id
        # if any found, mark all as 'pending'
        pass
