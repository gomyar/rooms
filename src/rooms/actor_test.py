
import unittest

from rooms.actor import Actor
from rooms.position import Position
from rooms.testutils import MockRoom
from rooms.testutils import MockTimer
from rooms.timer import Timer
from rooms.vector import Vector
from rooms.room import Door
from rooms import actor


def kickoff(actor):
    actor.state.log.append('a')
    Timer.sleep(1)
    actor.state.log.append('b')
    Timer.sleep(1)
    actor.state.log.append('c')


class ActorTest(unittest.TestCase):
    def setUp(self):
        MockTimer.setup_mock()
        self.mock_room = MockRoom("game1", "room1")
        self.actor = Actor(self.mock_room, "mock_actor",
            "rooms.actor_test")
        self.actor.state.log = []
        self.actor.room = self.mock_room

    def tearDown(self):
        MockTimer.teardown_mock()

    def testCreation(self):
        self.assertEquals(Vector(Position(0, 0), 0, Position(0, 0), 0),
            self.actor.vector)
        self.assertEquals("rooms.actor_test", self.actor.script.script_name)

    def testActorId(self):
        actor1 = Actor(self.mock_room, "mock_actor", "rooms.actor_test", None)
        self.assertEquals(None, actor1.actor_id)

        actor2 = Actor(self.mock_room, "mock_actor", "rooms.actor_test",
            actor_id="actor2")
        self.assertEquals("actor2", actor2.actor_id)

        actor1 = Actor(self.mock_room, "mock_actor", "rooms.actor_test")
        actor1._id = "actor3"
        self.assertEquals("actor3", actor1.actor_id)

    def testKickoff(self):
        self.actor.kick()
        self.assertEquals([], self.actor.state.log)

        MockTimer.fast_forward(1)

        self.assertEquals(['a', 'b'], self.actor.state.log)
        self.assertEquals(1, Timer.now())

        MockTimer.fast_forward(1)

        self.assertEquals(['a', 'b', 'c'], self.actor.state.log)
        self.assertEquals(2, Timer.now())

    def testSetPath(self):
        self.assertEquals(Position(0, 0), self.actor.position)

        self.actor.move_to(Position(10, 0))

        self.assertEquals([
            Position(0, 0),
            Position(10, 0),
        ], self.actor.path)

        MockTimer.fast_forward(1)

        self.assertEquals([(self.actor, {'vector': Vector(Position(0, 0), 0,
            Position(10, 0), 10.0)})], self.mock_room._updates)

        self.assertEquals(Position(1.0, 0), self.actor.position)

    def testMoveToSpecifyPath(self):
        self.assertEquals(Position(0, 0), self.actor.position)

        self.actor.move_to(Position(10, 0), [Position(0, 0), Position(5, 0),
            Position(10, 0)])

        self.assertEquals([
            Position(0, 0),
            Position(5, 0),
            Position(10, 0),
        ], self.actor.path)

        MockTimer.fast_forward(1)

        self.assertEquals((self.actor, {'vector': Vector(Position(0, 0), 0,
            Position(5, 0), 5.0)}), self.mock_room._updates[0])

        MockTimer.fast_forward(5)

        self.assertEquals((self.actor, {'vector': Vector(Position(5, 0), 5.0,
            Position(10, 0), 10.0)}), self.mock_room._updates[1])

    def testSpeed(self):
        self.actor.speed = 2

        self.actor.move_to(Position(10, 0), [Position(0, 0), Position(5, 0),
            Position(10, 0)])

        self.assertEquals([
            Position(0, 0),
            Position(5, 0),
            Position(10, 0),
        ], self.actor.path)

        MockTimer.fast_forward(1)

        self.assertEquals((self.actor, {'vector': Vector(Position(0, 0), 0,
            Position(5, 0), 2.5)}), self.mock_room._updates[0])

    def testMoveWait(self):
        self.assertEquals(Position(0, 0), self.actor.position)

        self.actor.move_wait(Position(10, 0))

        self.assertEquals([
            Position(0, 0),
            Position(10, 0),
        ], self.actor.path)

        MockTimer.fast_forward(1)

        self.assertEquals(20, MockTimer.slept())

    def testActorEnters(self):
        door = Door("room2", Position(0, 0), Position(10, 10))
        self.actor.enter(door)

        self.assertEquals((self.actor, door), self.mock_room._actor_enters[0])
