
import unittest

from rooms.room import Room
from rooms.position import Position


def created(actor):
    actor.state['created'] = True


class RoomTest(unittest.TestCase):
    def setUp(self):
        self.room = Room("game1", "room1", Position(0, 0), Position(50, 50))

    def testInitialSetup(self):
        self.assertEquals(50, self.room.width)
        self.assertEquals(50, self.room.height)
        self.assertEquals(Position(0, 0, 0), self.room.topleft)
        self.assertEquals(Position(50, 50, 0), self.room.bottomright)
        self.assertEquals(Position(25, 25, 0), self.room.center)

    def testCreateActor(self):
        actor = self.room.create_actor("rooms.room_test")
        self.assertTrue(actor.state.created)
        self.assertFalse(actor._gthread is None)
        self.assertEquals(created, actor.script._script_module.created)
        self.assertEquals(self.room, actor.room)
