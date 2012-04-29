
import unittest

from basicrect_geography import BasicRectGeography
from basicrect_geography import Rect
from room import Room
from room import RoomObject
from basicrect_geography import _is_north
from basicrect_geography import _is_south
from basicrect_geography import _is_east
from basicrect_geography import _is_west


class BasicRectGeographyTest(unittest.TestCase):
    def setUp(self):
        self.basicrect = BasicRectGeography()
        self.room = Room()

    def testCrossRoom(self):
        path = self.basicrect.get_path(self.room, (10, 10), (40, 40))

        self.assertEquals([(10, 10), (40, 40)], path)

    def testSomethingInWay(self):
        self.room.add_object(RoomObject(10, 10), (20, 20))

        path = self.basicrect.get_path(self.room, (10, 10), (40, 40))

        self.assertEquals([(10, 10), (20, 20), (30, 20), (40, 40)], path)

        path = self.basicrect.get_path(self.room, (5, 10), (40, 40))

        self.assertEquals([(10, 10), (20, 22), (20, 30), (40, 40)], path)

    def testPositionsAreEastOrNorth(self):
        self.assertTrue(_is_north((0, 0), (-5, -10)))
        self.assertTrue(_is_north((0, 0), (5, -10)))
        self.assertTrue(_is_west((0, 0), (-15, -10)))
        self.assertTrue(_is_east((0, 0), (15, -10)))
        self.assertTrue(_is_east((0, 0), (15, -5)))
        self.assertTrue(_is_east((0, 0), (15, 5)))
        self.assertTrue(_is_east((0, 0), (15, 10)))

    def testIntersectsRectWall(self):
        rect = Rect(0, 0, 10, 10)
        line = [ (5, 5), (15, 5) ]
        self.assertEquals((10, 5), rect.line_intersects_rect(line))
        line = [ (5, 5), (5, 15) ]
        self.assertEquals((5, 10), rect.line_intersects_rect(line))

        line = [ (5, 5), (15, 10) ]
        self.assertEquals((10, 7), rect.line_intersects_rect(line))
        line = [ (5, 5), (15, 8) ]
        self.assertEquals((10, 6), rect.line_intersects_rect(line))

        line = [ (5, 5), (8, 15) ]
        self.assertEquals((6, 10), rect.line_intersects_rect(line))

        line = [ (5, 5), (0, -5) ]
        self.assertEquals((2, 0), rect.line_intersects_rect(line))

        line = [ (5, 5), (-5, 0) ]
        self.assertEquals((0, 2), rect.line_intersects_rect(line))

    def testLineLength(self):
        rect = Rect(0, 0, 10, 10)
        self.assertEquals(10, rect.lengthof((0, 0), (10, 0)))
        self.assertEquals(20, rect.lengthof((0, 0), (0, 20)))
        self.assertEquals(28, int(rect.lengthof((0, 0), (20, 20))))

    def testSubdivide(self):
        self.room.add_object(RoomObject(10, 10), (20, 20))
        rects = self.basicrect.subdivide(self.room)

        self.assertEquals(8, len(rects))
        self.assertEquals([
            Rect(0, 0, 20, 20),
            Rect(0, 21, 20, 30),
            Rect(0, 31, 20, 50),
            Rect(21, 0, 30, 20),
            Rect(31, 0, 50, 20),
            Rect(31, 21, 50, 30),
            Rect(21, 31, 30, 50),
            Rect(31, 31, 50, 50),
        ], rects)

    def testRectOverlaps(self):
        self.assertTrue(Rect(0, 0, 50, 50).overlaps(Rect(25, 25, 70, 70)))
        self.assertTrue(Rect(30, 30, 50, 50).overlaps(Rect(25, 25, 70, 70)))
        self.assertFalse(Rect(80, 80, 50, 50).overlaps(Rect(25, 25, 70, 70)))

        self.assertTrue(Rect(0, 0, 50, 50).overlaps(Rect(0, 0, 50, 50)))
