
import unittest

from rooms.actor import Actor
from rooms.position import Position
from rooms.testutils import MockRoom
from rooms.testutils import MockTimer
from rooms.testutils import MockIDFactory
from rooms.timer import Timer
from rooms.vector import Vector
from rooms.room import Door
from rooms import actor
from rooms.script import Script


class ActorTest(unittest.TestCase):
    def setUp(self):
        MockTimer.setup_mock()
        MockIDFactory.setup_mock()
        self.mock_room = MockRoom("game1", "room1")
        self.actor = Actor(self.mock_room, "mock_actor", Script("actor_script",
            ActorTest))
        self.actor.state.log = []
        self.actor.room = self.mock_room

    def tearDown(self):
        MockTimer.teardown_mock()
        MockIDFactory.teardown_mock()

    @staticmethod
    def kickoff(actor):
        actor.state.log.append('a')
        Timer.sleep(1)
        actor.state.log.append('b')
        Timer.sleep(1)
        actor.state.log.append('c')

    def testCreation(self):
        self.assertEquals(Vector(Position(0, 0), 0, Position(0, 0), 0),
            self.actor.vector)
        self.assertEquals("actor_script", self.actor.script.script_name)

    def testActorId(self):
        actor1 = Actor(self.mock_room, "mock_actor", "rooms.actor_test", None)
        self.assertEquals("id2", actor1.actor_id)

        actor2 = Actor(self.mock_room, "mock_actor", "rooms.actor_test",
            actor_id="actor2")
        self.assertEquals("actor2", actor2.actor_id)

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

        self.assertEquals([self.actor, self.actor], self.mock_room._updates)

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

        self.assertEquals(self.actor, self.mock_room._updates[0])

        MockTimer.fast_forward(5)

        self.assertEquals(self.actor, self.mock_room._updates[1])

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

        self.assertEquals(self.actor, self.mock_room._updates[0])

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

    def testDocking(self):
        self.actor2 = Actor(self.mock_room, "mock_actor", Script("actor_script",
            ActorTest))
        self.actor2.state.log = []
        self.actor2.room = self.mock_room

        self.actor.dock(self.actor2)

        self.assertEquals(Position(0, 0), self.actor.position)

        self.actor.move_to(Position(10, 0))

        MockTimer.fast_forward(1)

        self.assertEquals(Position(1.0, 0), self.actor.position)
        self.assertEquals(Position(1.0, 0), self.actor2.position)
