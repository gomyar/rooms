
import math
import unittest
from rooms.position import Position


class PositionTest(unittest.TestCase):
    def setUp(self):
        self.position1 = Position(0, 0)
        self.position2 = Position(10, 10, 10)

    def testDistance(self):
         self.assertEquals(17.320508075688775,
            self.position1.distance_to(self.position2))

    def testOffsetPosition(self):
        self.assertEquals(Position(8, 10),
            self.position2.offset_position(2, math.pi))
        self.assertEquals(Position(10, 12),
            self.position2.offset_position(2, math.pi / 2))

    def testAngleBetween(self):
        self.assertEquals(math.pi,
            Position(10, 10).angle_between(Position(5, 10)))
        self.assertEquals(0,
            Position(10, 10).angle_between(Position(15, 10)))

    def testPositionDifferenceCoords(self):
        x, y, z = Position(10, 10, 10).difference(Position(11, 12, 13))
        self.assertEquals((-1, -2, -3), (x, y, z))

    def testInterpolate(self):
        self.assertEquals(Position(5, 0), Position(0, 0).interpolate(Position(10, 0), 5))
