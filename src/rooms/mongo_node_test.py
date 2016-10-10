

import unittest
from mock import Mock

from rooms.container import Container
from rooms.mongo_node import Node
from rooms.room import Room
from rooms.geography.basic_geography import BasicGeography
from rooms.testutils import MockDbase
from rooms.testutils import MockRoomFactory
from rooms.testutils import MockRoom
from rooms.testutils import MockNode


class NodeTest(unittest.TestCase):
    def setUp(self):
        self.dbase = MockDbase()
        self.room = Room('game1', 'room1', self) # script

        self.container = Mock(Container)

        self.node = Node(self.container, 'alpha')

    def testLoadRoomInitScript(self):
        room = self.container.request_create_room('game1', 'room1')
        self.container.load_next_pending_room.return_value = self.room

        self.assertEquals(0, len(self.node.rooms))
        self.node.load_next_pending_room()
        self.assertEquals(1, len(self.node.rooms))

        # test run init script

    def testPlayerConnects(self):
        self.node.player_connects("bob", "game1")

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
