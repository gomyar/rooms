
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
        self.assertEquals(Rect(10, 0, 20, 10), rects.rect_at(1, 0))

        self.assertEquals(Rect(10, 10, 20, 20), rects[15, 15])

    def testSubdivide2(self):
        rects = self.geog._subdivide(self.room2)

        self.assertEquals(25, len(rects))

        self.assertEquals(Rect(50, 5, 60, 15), rects.rect_at(0, 0))
        self.assertEquals(Rect(60, 5, 70, 15), rects.rect_at(1, 0))

        self.assertEquals(Rect(60, 15, 70, 25), rects[61, 16])

    def testSubdivideWithMapObjects(self):
        self.room.add_object("obj1", RoomObject("obj1", 10, 10), (20, 20))

        rects = self.geog._subdivide(self.room)

        self.assertEquals(21, len(rects))

        self.assertEquals(Rect(0, 0, 10, 10), rects.rect_at(0, 0))
        self.assertEquals(Rect(0, 0, 10, 10), rects[0, 0])
        self.assertEquals(Rect(0, 0, 10, 10), rects[9, 9])
        self.assertEquals(Rect(10, 10, 20, 20), rects[10, 10])
        self.assertEquals(Rect(10, 0, 20, 10), rects.rect_at(1, 0))
        self.assertEquals(Rect(10, 10, 20, 20), rects.rect_at(1, 1))
        self.assertEquals(None, rects.rect_at(2, 2))
        self.assertEquals(None, rects.rect_at(3, 3))
        self.assertEquals(Rect(40, 40, 50, 50), rects.rect_at(4, 4))

    def testSubdivideWithMapObjects2(self):
        self.room2.add_object("obj1", RoomObject("obj1", 60, 15), (20, 20))

        rects = self.geog._subdivide(self.room2)

        self.assertEquals(19, len(rects))

        self.assertEquals(Rect(50, 5, 60, 15), rects.rect_at(0, 0))
        self.assertEquals(Rect(50, 5, 60, 15), rects[50, 5])
        self.assertEquals(Rect(50, 5, 60, 15), rects[59, 14])
        self.assertEquals(Rect(60, 15, 70, 25), rects[60, 15])
        self.assertEquals(Rect(60, 5, 70, 15), rects.rect_at(1, 0))
        self.assertEquals(Rect(60, 15, 70, 25), rects.rect_at(1, 1))
        self.assertEquals(None, rects.rect_at(2, 2))
        self.assertEquals(None, rects.rect_at(3, 3))
        self.assertEquals(Rect(90, 45, 100, 55), rects.rect_at(4, 4))

    def testLinearPath(self):
        self.geog = BasicSquareGeography(rect_width=10, rect_height=10)
        self.room = Room("r1", (0, 0), 50, 50)
        self.assertEquals([(10, 10), (17, 17), (24, 24), (31, 31), (38, 38),
            (45, 45), (50, 50)], list(self.geog._line((10, 10),
            (50, 50))))


    def testReal(self):
        self.room = Room("r1", (0, 0), 400, 400)
        path = self.geog.get_path(self.room, (388, 187), (441, 264))

        self.assertEquals([(388, 187), (399, 203), (395, 215), (395, 215),
            (395, 225), (395, 225), (395, 235), (395, 235), (395, 245),
            (395, 245), (395, 255), (395, 255), (395, 265), (395, 265)], path)

    def testReal2(self):
        self.room = Room("r1", (0, 0), 400, 400)
        path = self.geog.get_path(self.room, (341, 272), (371, 184))

        self.assertEquals([(341, 272), (371, 184)], path)

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

        # Nonexistant rects around edge
        r2 = rects[0, 25]
        self.assertEquals(None,
            r2.next_rect((0, 0), (-10, -10)))

        rects.remove_rect_at(1, 2)
        self.assertEquals(rects.rect_at(2, 1),
            r1.next_rect((25, 25), (15, 15)))
        rects.remove_rect_at(2, 1)
        self.assertEquals(None,
            r1.next_rect((25, 25), (15, 15)))

    def testPath(self):
        self.geog = BasicSquareGeography()
        self.room = Room("room1", (0, 0), 500, 500)
        self.room.add_object("obj1", RoomObject("obj1", 100, 100), (100, 100))

        self.assertEquals(None, self.geog._get_rects_for(self.room)[113, 128])
        path = self.geog.get_path(self.room, (50, 200), (200, 50))

        self.assertEquals([(50, 200), (99, 150), (95, 145), (95, 145),
            (95, 135), (95, 135), (95, 125), (95, 125), (95, 115), (95, 115),
            (95, 105), (95, 105), (95, 95), (200, 50)], path)
