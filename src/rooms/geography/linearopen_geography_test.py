
import unittest

from linearopen_geography import LinearOpenGeography
from rooms.room import Room
from rooms.position import Position
from rooms.testutils import MockNode


class LinearOpenGeographyTest(unittest.TestCase):
    def setUp(self):
        self.geography = LinearOpenGeography()
        self.room = Room("game1", "room1", MockNode())
        self.room.coords(0, 0, 100, 100)
        self.room.geog = self.geography

    def testGetPath(self):
        self.assertEquals([(10, 10), (12, 12)],
            self.geography.get_path(self.room, (10, 10), (12, 12)))
        self.assertEquals([(10, 10), (100, 10)],
            self.geography.get_path(self.room, (10, 10), (110, 10)))
        self.assertEquals([(0, 10), (100, 10)],
            self.geography.get_path(self.room, (-10, 10), (100, 10)))
