
import unittest

from .intersect import intersect


class IntersectTest(unittest.TestCase):
    def test_intersect(self):
        self.assertEquals(True, intersect(10, 10, 50, 50, 20, 30, 30, 20))
        # no endpoint intersects
        self.assertEquals(False, intersect(10, 10, 50, 50, 20, 30, 40, 40))
        self.assertEquals(False, intersect(10, 10, 50, 50, 20, 30, 40, 41))
        self.assertEquals(False, intersect(10, 10, 50, 50, 0, 14, 14, 0))
        self.assertEquals(False, intersect(10, 10, 50, 50, 41, 60, 60, 41))
        self.assertEquals(True, intersect(50, 50, 10, 10, 30, 10, 10, 30))

        # we... don't? want to see an intersect if the lines are colinear
        self.assertEquals(False, intersect(10, 10, 50, 50, 20, 20, 60, 60))
        self.assertEquals(False, intersect(10, 10, 20, 20, 30, 30, 40, 40))
        self.assertEquals(False, intersect(10, 10, 20, 20, 10, 20, 20, 30))

        self.assertEquals(True, intersect(10, 10, 50, 50, 10, 11, 50, 49))

        # we don't want the lines to intersect if the endpoints are equal
        self.assertEquals(False, intersect(10, 10, 100, 10, 10, 10, 10, 100))
        self.assertEquals(False, intersect(10, 20, 100, 100, 20, 10, 100, 100))
