import unittest
import time

import mock
from eventlet.queue import LightQueue

from instance import Instance
from area import Area
from room import Room
from player_actor import PlayerActor


class InstanceTest(unittest.TestCase):
    def setUp(self):
        self.instance = Instance()
        self.area = Area()
        self.area.rooms['1'] = Room()
        self.area.entry_point_room_id = '1'
        self.instance.area = self.area
        self.now = 0.0
        time.time = mock.Mock(return_value=self.now)

    def testRegisterPlayer(self):
        self.instance.register("player1")
        self.assertFalse(self.instance.players['player1']['connected'])
        self.assertEquals(PlayerActor,
            type(self.instance.players['player1']['player']))
        queue = self.instance.connect("player1")
        self.assertTrue(self.instance.players['player1']['connected'])
        self.assertEquals(queue, self.instance.player_queues['player1'])

    def testActorStartPositionInRoom(self):
        self.instance.register("player1")
        self.instance.connect("player1")
        self.assertEquals(25, self.instance.players['player1']['player'].x())
        self.assertEquals(25, self.instance.players['player1']['player'].y())

    def testBasicCommand(self):
        self.instance.register("player1")
        queue = self.instance.connect("player1")
#        self.assertEquals('actor_joined',
#            self.instance.player_queues['player1'].get_nowait()['command'])

        self.instance.call("walk_to", "player1", "player1",
            kwargs={ 'x': 20, 'y': 10})

        self.assertEquals('actor_update',
            self.instance.player_queues['player1'].get_nowait()['command'])

