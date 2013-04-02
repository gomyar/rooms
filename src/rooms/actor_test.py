
import unittest
import mock
import time

import rooms.waypoint
from actor import Actor
from script import command
from script import request
from room import Room


@command
def mock_me(actor):
    self._mock_me_called = True

@command
def mock_you(actor, from_actor):
    actor._test_value = "Called with actor %s" % (actor.actor_id,)


@request
def scripty_cally(player, param1, param2="value2"):
    return "Hello %s %s" % (param1, param2)


class MockScript(object):
    def __init__(self):
        self._kickoff_called = False

    def kickoff(self, actor):
        self._kickoff_called = True

    def __contains__(self, key):
        return True


class ActorTest(unittest.TestCase):
    def setUp(self):
        self.now = 0.0
        time.time = mock.Mock(return_value=self.now)
        self.room = Room(1000, 1000)
        self.actor = Actor("actor1")
        self.actor.sleep = self._mock_sleep
        self.actor.circles.circle_id = "alliance1"
        self.mock_actor = Actor("mock")
        self.room.put_actor(self.actor, (10, 10))
        rooms.waypoint.get_now = self._mock_get_now

        self._slept = []

    def _mock_sleep(self, seconds):
        self._slept.append(seconds)

    def _mock_get_now(self):
        return self.now

    def tearDown(self):
        reload(time)
        reload(rooms.waypoint)

    def testSetPath(self):
        self.actor.speed = 150
        self.actor.set_waypoints([(0.0, 0.0), (3.0, 0.0), (9.0, 0.0)])
        self.assertEquals([(0.0, 0.0, 0.0), (3.0, 0.0, 0.02),
            (9.0, 0.0, 0.06)], self.actor.path.path)

    def testMethodCallthroughScript(self):
        self.actor.load_script("rooms.actor_test")
        self.mock_actor.load_script("rooms.actor_test")

        self.mock_actor.script.mock_you(self.mock_actor, self.actor)
        self.assertEquals("Called with actor mock", self.mock_actor._test_value)

        response = self.actor.call_command("scripty_cally", "1", "2")
        self.assertEquals("Hello 1 2", response)

    def testDel(self):
        self.actor.load_script("rooms.actor_test")
        del(self.actor)

    def testDocking(self):
        self.actor2 = Actor("actor2")
        self.room.put_actor(self.actor2, (50, 10))
        self.actor.dock(self.actor2)

        self.assertEquals([(10, 10), (10, 10)], self.actor2.path.basic_path_list())
        self.actor.move_to(50, 50)

        self.assertEquals([(10, 10), (50, 50)], self.actor.path.basic_path_list())
        self.assertEquals([(10, 10), (50, 50)], self.actor2.path.basic_path_list())

    def testUndocking(self):
        self.actor2 = Actor("actor2")
        self.room.put_actor(self.actor2, (50, 10))
        self.actor.dock(self.actor2)

        self.actor.undock(self.actor2)

        self.assertEquals(None, self.actor2.docked_with)
        self.assertEquals({}, self.actor.docked)

    def testIntercept(self):
        self.actor2 = Actor("actor2")
        self.room.put_actor(self.actor2, (50, 10))

        self.actor2.set_waypoints([(50, 10), (50, 50)])

        self.actor.intercept(self.actor2)

        self.assertEquals([(10, 10), (50, 50)],
            self.actor.path.basic_path_list())

        self.actor.set_position((40, 25))

        self.actor.intercept(self.actor2)

        self.assertEquals([(40, 25), (50.0, 49.999961853027344), (50.0, 50.0)],
            self.actor.path.basic_path_list())

    def testInterceptExample(self):
        self.room.width = 600
        self.room.height = 600
        self.actor.set_position((500, 500))

        self.actor2 = Actor("actor2")
        self.actor2.speed = 70
        self.room.put_actor(self.actor2, (100, 100))
        self.actor2.sleep = lambda t: None
        self.actor2.move_to(200, 200)

        self.assertEquals([(100, 100), (200, 200)],
            self.actor2.path.basic_path_list())

        self.actor.intercept(self.actor2)

        self.assertEquals([(500, 500, 0.0), (200, 200, 424.26406871192853)],
            self.actor.path.path)

    def testInterceptFollowsCurrentTargetNotLast(self):
        self.room.width = 600
        self.room.height = 600
        self.actor.set_position((500, 500))

        self.actor2 = Actor("actor2")
        self.actor2.speed = 70
        self.room.put_actor(self.actor2, (100, 100))
        self.actor2.sleep = lambda s: None
        self.actor2.move_to(200, 200)

        self.actor3 = Actor("actor3")
        self.actor3.speed = 70
        self.room.put_actor(self.actor3, (100, 100))
        self.actor3.sleep = lambda s: None
        self.actor3.move_to(300, 300)

        self.assertEquals([(100, 100), (200, 200)],
            self.actor2.path.basic_path_list())

        self.actor.intercept(self.actor2)

        self.assertEquals([(500, 500, 0.0), (200, 200, 424.26406871192853)],
            self.actor.path.path)

        self.actor.move_to(300, 300)

        self.assertEquals([(500, 500, 0.0), (300, 300, 282.842712474619)],
            self.actor.path.path)

        self.actor2.intercept(self.actor3)

        self.assertEquals([(500, 500, 0.0), (300, 300, 282.842712474619)],
            self.actor.path.path)

    def testFindAllies(self):
        self.actor2 = Actor("actor2")
        self.room.put_actor(self.actor2, (100, 100))
        self.actor2.circles.circle_id = "alliance1"

        self.actor3 = Actor("actor3")
        self.room.put_actor(self.actor3, (500, 500))
        self.actor3.circles.circle_id = "alliance2"

        self.actor4 = Actor("actor4")
        self.room.put_actor(self.actor4, (500, 500))
        self.actor4.circles.circle_id = "alliance2"
        self.actor4.actor_type = "test"

        self.actor.circles.circles['alliance2'] = -1

        self.assertTrue(self.actor.circles.is_enemy(self.actor3))
        self.assertEquals(set([self.actor3, self.actor4]),
            set(self.actor.find_actors(enemy=True)))
        self.assertEquals([self.actor2], list(self.actor.find_actors(
            ally=True)))

        self.assertEquals(set([self.actor3, self.actor4]),
            set(self.actor.find_actors(enemy=True, distance=700)))
        self.assertEquals([], list(self.actor.find_actors(enemy=True,
            distance=70)))

        self.assertEquals([self.actor2], list(self.actor.find_actors(ally=True,
            distance=700)))
        self.assertEquals([], list(self.actor.find_actors(ally=True,
            distance=70)))

        self.assertEquals([], list(self.actor.find_actors(ally=True,
            distance=700, actor_type="test")))
        self.assertEquals([self.actor4], list(self.actor.find_actors(enemy=True,
            distance=700, actor_type="test")))

    def testSleepOnMove(self):
        self.actor.move_to(110, 10)

        self.assertEquals([100.0], self._slept)

    def testSleepOnMoveMultiple(self):
        self.actor.move_to(160, 10)

        self.assertEquals([100.0, 50.0], self._slept)

    def testKick(self):
        script = MockScript()
        self.actor.script = script
        self.actor.run_kickoff = lambda: None

        self.assertIsNone(self.actor.kickoff_gthread)

        self.actor.kick()

        self.assertIsNotNone(self.actor.kickoff_gthread)
