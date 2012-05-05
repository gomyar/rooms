
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

        self.assertEquals(Rect(0, 0, 10, 10), rects.rect_at(0, 0))
        self.assertEquals(Rect(10, 0, 10, 10), rects.rect_at(1, 0))

    def testSubdivide2(self):
        rects = self.geog._subdivide(self.room2)

        self.assertEquals(25, len(rects))

        self.assertEquals(Rect(50, 5, 10, 10), rects.rect_at(0, 0))
        self.assertEquals(Rect(60, 5, 10, 10), rects.rect_at(1, 0))

    def testSubdivideWithMapObjects(self):
        self.room.add_object(RoomObject(10, 10), (20, 20))

        rects = self.geog._subdivide(self.room)

        self.assertEquals(21, len(rects))

        self.assertEquals(Rect(0, 0, 10, 10), rects.rect_at(0, 0))
        self.assertEquals(Rect(0, 0, 10, 10), rects[0, 0])
        self.assertEquals(Rect(0, 0, 10, 10), rects[9, 9])
        self.assertEquals(Rect(10, 10, 10, 10), rects[10, 10])
        self.assertEquals(Rect(10, 0, 10, 10), rects.rect_at(1, 0))
        self.assertEquals(Rect(10, 10, 10, 10), rects.rect_at(1, 1))
        self.assertEquals(None, rects.rect_at(2, 2))
        self.assertEquals(None, rects.rect_at(3, 3))
        self.assertEquals(Rect(40, 40, 10, 10), rects.rect_at(4, 4))

    def testNextPoint(self):
        self.geog = BasicSquareGeography(rect_width=10, rect_height=10)
        self.room = Room("r1", (0, 0), 50, 50)

        self.assertEquals((28, 15), self.geog._next_point((20, 20), (40, 10)))

    def testLinearPath(self):
        self.geog = BasicSquareGeography(rect_width=10, rect_height=10)
        self.room = Room("r1", (0, 0), 50, 50)
        self.assertEquals([(10, 10), (17, 17), (24, 24), (31, 31), (38, 38),
            (45, 45), (50, 50)], list(self.geog._line((10, 10),
            (50, 50))))


    def testReal(self):
        self.room = Room("r1", (0, 0), 400, 400)
        path = self.geog.get_path(self.room, (388, 187), (441, 264))

        self.assertEquals([], path)

    def testNextRect(self):
        self.geog = BasicSquareGeography(rect_width=10, rect_height=10)
        self.room = Room("r1", (0, 0), 50, 50)

        rects = self.geog._get_rects_for(self.room)

        r1 = rects[25, 25]
        self.assertEquals(rects.rect_at(1, 2),
            r1.next_rect((25, 25), (15, 15)))
        self.assertEquals(rects.rect_at(2, 1),
            r1.next_rect((25, 25), (25, 15)))
        self.assertEquals(rects.rect_at(1, 2),
            r1.next_rect((25, 25), (15, 19)))
        self.assertEquals(None,
            r1.next_rect((25, 25), (26, 26)))

        rects.remove_rect_at(1, 2)
        self.assertEquals(rects.rect_at(2, 1),
            r1.next_rect((25, 25), (15, 15)))
        rects.remove_rect_at(2, 1)
        self.assertEquals(None,
            r1.next_rect((25, 25), (15, 15)))

    def testPath(self):
        self.geog = BasicSquareGeography()
        self.room = Room("room1", (0, 0), 500, 500)
        self.room.add_object(RoomObject(100, 100), (100, 100))

        self.assertEquals(None, self.geog._get_rects_for(self.room)[113, 128])
        import ipdb; ipdb.set_trace()
        path = self.geog.get_path(self.room, (50, 200), (200, 50))

        self.assertEquals([(50, 200), (90, 120), (90, 110), (90, 100),
            (200, 50)], path)