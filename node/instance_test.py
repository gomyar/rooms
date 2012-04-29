import unittest
import time

import mock
from eventlet.queue import LightQueue

from instance import Instance
from area import Area
from room import Room

class InstanceTest(unittest.TestCase):
    def setUp(self):
        self.instance = Instance()
        self.queue = LightQueue()
        self.area = Area()
        self.area.rooms['1'] = Room()
        self.area.entry_point_room_id = '1'
        self.instance.area = self.area
        self.instance.player_joins("1")
        self.instance.register("1", self.queue)
        self.now = 0.0
        time.time = mock.Mock(return_value=self.now)

    def testActorStartPositionInRoom(self):
        self.assertEquals(25, self.instance.players['1']['player'].x())
        self.assertEquals(25, self.instance.players['1']['player'].y())

    def testBasicCommand(self):
        self.assertEquals('actor_joined', self.queue.get_nowait()['command'])

        self.instance.call("walk_to", "1", "1",
            kwargs={ 'x': 20, 'y': 10})

        self.assertEquals('actor_update', self.queue.get_nowait()['command'])

