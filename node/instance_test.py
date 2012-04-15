import unittest
import time

import mock
from eventlet.queue import LightQueue

from instance import Instance

class InstanceTest(unittest.TestCase):
    def setUp(self):
        self.instance = Instance()
        self.queue = LightQueue()
        self.instance.register("1", self.queue)
        self.now = 0.0
        time.time = mock.Mock(return_value=self.now)

    def testBasicCommand(self):
        self.assertEquals('actor_joined', self.queue.get_nowait()['command'])

        self.instance.call("walk_to", kwargs={ 'player_id': '1', 'x': 20, 'y': 10})

        self.assertEquals('actor_update', self.queue.get_nowait()['command'])

