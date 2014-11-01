
import unittest
from rooms.position import Position


class PositionTest(unittest.TestCase):
    def setUp(self):
        self.position1 = Position(0, 0)
        self.position2 = Position(10, 10, 10)

    def testDistance(self):
         self.assertEquals(17.320508075688775,
            self.position1.distance_to(self.position2))
