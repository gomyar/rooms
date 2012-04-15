
import unittest
import mock
import time

from actor import Actor

class ActorTest(unittest.TestCase):
    def setUp(self):
        self.actor = Actor("actor1", 10, 10)
        self.now = 0.0
        time.time = mock.Mock(return_value=self.now)

    def testSetPath(self):
        self.actor.set_path([(0.0, 0.0), (1.0, 0.0), (3.0, 0.0)])
        self.assertEquals([(0.0, 0.0, 0.0), (1.0, 0.0, 0.005),
            (3.0, 0.0, 0.015)], self.actor.path)

    def testXFromPath(self):
        self.actor.path = [ (0.0, 0.0, 0.0), (1.0, 0.0, 1.0), (2.0, 0.0, 2.0),
            (3.0, 0.0, 3.0), (4.0, 0.0, 4.0) ]

        self.assertEquals(0.0, self.actor.x())

        time.time = mock.Mock(return_value=0.5)
        self.assertEquals(0.5, self.actor.x())

        time.time = mock.Mock(return_value=1.5)
        self.assertEquals(1.5, self.actor.x())

        time.time = mock.Mock(return_value=2.5)
        self.assertEquals(2.5, self.actor.x())

        time.time = mock.Mock(return_value=4.5)
        self.assertEquals(4.0, self.actor.x())

    def testYFromPath(self):
        self.actor.path = [ (0.0, 0.0, 0.0), (0.0, 1.0, 1.0), (0.0, 2.0, 2.0),
            (0.0, 3.0, 3.0), (0.0, 4.0, 4.0) ]

        self.assertEquals(0.0, self.actor.y())

        time.time = mock.Mock(return_value=0.5)
        self.assertEquals(0.5, self.actor.y())

        time.time = mock.Mock(return_value=1.5)
        self.assertEquals(1.5, self.actor.y())

        time.time = mock.Mock(return_value=2.5)
        self.assertEquals(2.5, self.actor.y())

        time.time = mock.Mock(return_value=4.5)
        self.assertEquals(4.0, self.actor.y())
