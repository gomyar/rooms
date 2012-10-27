import unittest
import time

import mock

from instance import Instance
from area import Area
from room import Room
from player_actor import PlayerActor
from script import command


@command
def walk_to(actor, x, y):
    actor.move_to(x, y)


class InstanceTest(unittest.TestCase):
    def setUp(self):
        self.instance = Instance()
        self.area = Area()
        self.area.load_script("rooms.instance_test")
        self.area.rooms['1'] = Room()
        self.area.entry_point_room_id = '1'
        self.area.player_script = "rooms.instance_test"
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
        self.assertEquals(20, self.instance.players['player1']['player'].x())
        self.assertEquals(20, self.instance.players['player1']['player'].y())

    def testBasicCommand(self):
        self.instance.register("player1")
        queue = self.instance.connect("player1")

        self.instance.call("walk_to", "player1", "player1",
            kwargs={ 'x': 20, 'y': 10})

        player = self.instance.players['player1']['player']

        self.assertEquals(1, player.call_queue.qsize())
        self.assertEquals(player.call_queue.queue[0],
            ("walk_to", [player], {'y': 10, 'x': 20}))

    def testNoExceptionOnPlayerDisconnect(self):
        self.instance.register("player1")
        queue = self.instance.connect("player1")
        self.instance.player_queues.pop("player1")

        self.instance.send_update("player1", {'command': 'heartbeat'})
