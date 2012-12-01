
import unittest
import mock
import time

from actor import Actor
from script import expose
from script import command
from room import Room


@expose(go=True)
def mock_me(actor):
    self._mock_me_called = True

@expose()
def mock_you(actor, from_actor):
    actor._test_value = "Called with actor %s" % (actor.actor_id,)


@command()
def scripty_cally(player, param1, param2="value2"):
    return "Hello %s %s" % (param1, param2)


class ActorTest(unittest.TestCase):
    def setUp(self):
        self.room = Room()
        self.actor = Actor("actor1", (10, 10))
        self.mock_actor = Actor("mock")
        self.actor.room = self.room
        self.now = 0.0
        time.time = mock.Mock(return_value=self.now)

    def testSetPath(self):
        self.actor.set_waypoints([(0.0, 0.0), (3.0, 0.0), (9.0, 0.0)])
        self.assertEquals([(0.0, 0.0, 0.0), (3.0, 0.0, 0.02),
            (9.0, 0.0, 0.06)], self.actor.path.path)

    def testAllowedMethod(self):
        self.mock_actor.load_script("rooms.actor_test")
        self.assertFalse(self.mock_actor._can_call(self.actor,
            "mock_me"))
        self.assertEquals([{'name':'mock_me'}, {'name':'mock_you'}],
            self.mock_actor.exposed_methods(self.actor))

        self.actor.state.go = True

        self.assertTrue(self.mock_actor._can_call(self.actor,
            "mock_me"))
        self.assertEquals([{'name':'mock_me'}, {'name':'mock_you'}],
            self.mock_actor.exposed_methods(self.actor))

    def testMethodCallthroughScript(self):
        self.actor.load_script("rooms.actor_test")
        self.mock_actor.load_script("rooms.actor_test")

        self.mock_actor.interface_call("mock_you", self.actor)
        self.mock_actor._process_queue_item()
        self.assertEquals("Called with actor mock", self.mock_actor._test_value)

        self.actor.command_call("scripty_cally", "1", "2")

        self.assertEquals(("scripty_cally", [self.actor, '1', '2'], {}),
            self.actor.call_queue.queue[0])

    def testDel(self):
        self.actor.load_script("rooms.actor_test")
        del(self.actor)

    def testDocking(self):
        self.actor2 = Actor("actor2", (50, 10))
        self.room.put_actor(self.actor2, (50, 10))
        self.actor.dock(self.actor2)

        self.assertEquals([(10, 10), (10, 10)], self.actor2.path.basic_path_list())
        self.actor.move_to(50, 50)

        self.assertEquals([(10, 10), (50, 50)], self.actor.path.basic_path_list())
        self.assertEquals([(10, 10), (50, 50)], self.actor2.path.basic_path_list())

    def testUndocking(self):
        self.actor2 = Actor("actor2", (50, 10))
        self.room.put_actor(self.actor2, (50, 10))
        self.actor.dock(self.actor2)

        self.actor.undock(self.actor2)

        self.assertEquals(None, self.actor2.docked_with)
        self.assertEquals(set(), self.actor.docked)

    def testIntercept(self):
        self.actor2 = Actor("actor2")
        self.room.put_actor(self.actor2, (50, 10))

        self.actor2.set_waypoints([(50, 10), (50, 50)])

        self.actor.intercept(self.actor2)

        self.assertEquals([(10, 10), (25, 50)], self.actor.path.path)
