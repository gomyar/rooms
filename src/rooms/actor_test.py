
import unittest

from rooms.actor import Actor
from rooms.position import Position
from rooms.testutils import MockRoom
from rooms.testutils import MockTimer
from rooms.timer import Timer
from rooms.vector import Vector


def kickoff(actor):
    actor.state.log.append('a')
    Timer.sleep(1)
    actor.state.log.append('b')
    Timer.sleep(1)
    actor.state.log.append('c')


class ActorTest(unittest.TestCase):
    def setUp(self):
        self.actor = Actor(MockRoom("game1", "room1"))
        self.actor.script.load_script("rooms.actor_test")
        self.actor.state.log = []
        self.actor.room = MockRoom("game1", "room1")
        self.actor._send_update = self._actor_update
        self._updates = []
        MockTimer.setup_mock()

    def tearDown(self):
        MockTimer.teardown_mock()

    def _actor_update(self, update):
        self._updates.append(update)

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

        self.assertEquals([{'vector': Vector(Position(0, 0), 0,
            Position(10, 0), 1)}], self._updates)
