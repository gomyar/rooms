
import unittest

from room import Room
from room import RoomObject
from basicsquare_geography import BasicSquareGeography
from basicsquare_geography import Rect


class BasicSquareTest(unittest.TestCase):
    def setUp(self):
        self.geog = BasicSquareGeography()
        self.room = Room("room1", (0, 0), 50, 50)
        self.room2 = Room("room2", (50, 5), 50, 50)

    def testSubdivide(self):
        rects = self.geog._subdivide(self.room)

        self.assertEquals(25, len(rects))

        self.assertEquals(Rect(0, 0, 10, 10), rects[0, 0])
        self.assertEquals(Rect(10, 0, 10, 10), rects[1, 0])

    def testSubdivide2(self):
        rects = self.geog._subdivide(self.room2)

        self.assertEquals(25, len(rects))

        self.assertEquals(Rect(50, 5, 10, 10), rects[0, 0])
        self.assertEquals(Rect(60, 5, 10, 10), rects[1, 0])

    def testSubdivideWithMapObjects(self):
        self.room.add_object(RoomObject(10, 10), (20, 20))

        rects = self.geog._subdivide(self.room)

        self.assertEquals(21, len(rects))

        self.assertEquals(Rect(0, 0, 10, 10), rects[0, 0])
        self.assertEquals(Rect(10, 0, 10, 10), rects[1, 0])
        self.assertEquals(Rect(10, 10, 10, 10), rects[1, 1])
        self.assertEquals(None, rects[2, 2])
        self.assertEquals(None, rects[3, 3])
        self.assertEquals(Rect(40, 40, 10, 10), rects[4, 4])

    def testPath(self):
        self.room.add_object(RoomObject(10, 10), (20, 20))

        path = self.geog.get_path(self.room, (30, 30), (50, 45))

        self.assertEquals(3, len(path))
