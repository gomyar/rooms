
import unittest

from room import Room
from area import Area


class RoomTest(unittest.TestCase):
    def setUp(self):
        self.area = Area()
        self.area.rooms['room1'] = Room("room1")
        self.area.rooms['room2'] = Room("room2")
        self.area.rooms['room3'] = Room("room3")

        self.area.create_door(self.area.rooms['room1'],
            self.area.rooms['room2'], (0, 0), (10, 0))
        self.area.create_door(self.area.rooms['room1'],
            self.area.rooms['room3'], (10, 0), (0, 0))

    def testDoorsExist(self):
        self.assertTrue(self.area.rooms['room1'].has_door_to("room2"))
        self.assertTrue(self.area.rooms['room1'].has_door_to("room3"))
        self.assertFalse(self.area.rooms['room3'].has_door_to("room2"))
