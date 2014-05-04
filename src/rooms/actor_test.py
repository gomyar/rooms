
import unittest

from rooms.actor import Actor
from rooms.position import Position
from rooms.waypoint import Path
from rooms.testutils import MockRoom


def kickoff(actor):
    actor.state.kicked += 1


class ActorTest(unittest.TestCase):
    def setUp(self):
        self.actor = Actor()
        self.actor.script.load_script("rooms.actor_test")
        self.actor.state.kicked = 0
        self.actor.room = MockRoom("game1", "room1")

    def testKickoff(self):
        self.actor.kick()
        self.actor._gthread.join()

        self.assertEquals(1, self.actor.state.kicked)

    def testSetPath(self):
        self.assertEquals(Position(0, 0), self.actor.position)

        self.actor.move_to(Position(10, 0))

        self.assertEquals(Path([
            (Position(0, 0), 0),
            (Position(10, 0), 1),
        ]), self.actor.path)
