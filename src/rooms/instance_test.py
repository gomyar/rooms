import unittest
import time

import mock

from instance import Instance
from area import Area
from room import Room
from player_actor import PlayerActor
from player import Player
from script import command


@command
def walk_to(actor, x, y):
    actor.move_to(x, y)


class InstanceTest(unittest.TestCase):
    def setUp(self):
        self.instance = Instance()
        self.area = Area()
        self.area.load_script("rooms.instance_test")
        self.area.put_room(Room('1'), (0, 0))
        self.area.entry_point_room_id = '1'
        self.area.player_script = "rooms.instance_test"
        self.area.instance = self.instance
        self.instance.area = self.area
        self.player = Player("player1")
        self.player.room_id = "1"
        self.now = 0.0
        time.time = mock.Mock(return_value=self.now)

    def testRegisterPlayer(self):
        self.instance.register(self.player)
        self.assertFalse(self.instance.players['player1']['connected'])
        self.assertEquals(PlayerActor,
            type(self.instance.players['player1']['player']))
        queue = self.instance.connect("player1")
        self.assertTrue(self.instance.players['player1']['connected'])
        self.assertEquals(queue, self.instance.player_queues['player1'])

    def testActorStartPositionInRoom(self):
        self.instance.register(self.player)
        self.instance.connect("player1")
        self.assertEquals(25, self.instance.players['player1']['player'].x())
        self.assertEquals(25, self.instance.players['player1']['player'].y())

    def testBasicCommand(self):
        self.instance.register(self.player)
        queue = self.instance.connect("player1")

        player = self.instance.players['player1']['player']

        self.instance.call("walk_to", "player1", player.actor_id,
            kwargs={ 'x': 20, 'y': 10})

        self.assertEquals(("walk_to", [player], {'y': 10, 'x': 20}),
            player.method_call)

    def testNoExceptionOnPlayerDisconnect(self):
        self.instance.register(self.player)
        queue = self.instance.connect("player1")
        self.instance.player_queues.pop("player1")

        self.instance.send_update("player1", {'command': 'heartbeat'})
