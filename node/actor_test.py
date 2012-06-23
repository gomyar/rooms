
import unittest
import mock
import time

from actor import Actor
from actor import expose


class MockActor(Actor):
    def __init__(self, actor_id):
        super(MockActor, self).__init__(actor_id)
        self._mock_me_called = False
        self.state = "stop"

    @expose(state="go")
    def mock_me(self, actor):
        self._mock_me_called = True

    @expose()
    def mock_you(self, actor):
        self._mock_me_called = True


class ActorTest(unittest.TestCase):
    def setUp(self):
        self.actor = Actor("actor1", (10, 10))
        self.mock_actor = MockActor("mock")
        self.now = 0.0
        time.time = mock.Mock(return_value=self.now)

    def testSetPath(self):
        self.actor.set_path([(0.0, 0.0), (3.0, 0.0), (9.0, 0.0)])
        self.assertEquals([(0.0, 0.0, 0.0), (3.0, 0.0, 0.02),
            (9.0, 0.0, 0.06)], self.actor.path)

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

    def testAllowedMethod(self):
        self.assertFalse(self.mock_actor._can_call_method(self.actor,
            "mock_me"))
        self.assertEquals([{'name':'mock_you'}], self.mock_actor.exposed_methods(self.actor))

        self.mock_actor.state = "go"

        self.assertTrue(self.mock_actor._can_call_method(self.actor,
            "mock_me"))
        self.assertEquals([{'name':'mock_me'}, {'name':'mock_you'}],
            self.mock_actor.exposed_methods(self.actor))
