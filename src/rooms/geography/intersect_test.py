
import unittest

from .intersect import intersect, intersection_point


class IntersectTest(unittest.TestCase):
    def test_intersect(self):
        self.assertEquals(True, intersect(10, 10, 50, 50, 20, 30, 30, 20))
        self.assertEquals(True, intersect(10, 10, 50, 50, 20, 30, 40, 40))
        # self.assertEquals(True, intersect(10, 10, 50, 50, 20, 30, 50, 50))
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

    def test_intersection_point(self):
        self.assertEquals((10, 10), intersection_point((0, 0), (20, 20), (0, 20), (20, 0)))
        self.assertEquals((0, 0), intersection_point((0, 0), (10, 20), (0, 0), (20, 10)))
        self.assertEquals(None, intersection_point((10, 0), (10, 20), (20, 0), (20, 20)))
        self.assertEquals(None, intersection_point((15, 5), (10, 20), (20, 0), (15, 35)))
        self.assertEquals(None, intersection_point((0, 0), (40, 0), (5, 20), (35, 20)))
        self.assertEquals((20, 20), intersection_point((0, 0), (20, 20), (5, 0), (20, 20)))
        self.assertEquals(None, intersection_point((0, 0), (20, 21), (5, 0), (20, 20)))

        self.assertEquals((0, 15), intersection_point((0, 0), (0, 20), (15, 0), (-5, 20)))
        self.assertEquals((0, 12), intersection_point((0, 0), (0, 20), (15, 0), (-10, 20)))
        self.assertEquals((0, 12.5), intersection_point((0, 0), (0, 20), (15, 0), (-9, 20)))
        self.assertEquals((0, 12.244897959183675), intersection_point((0, 0), (0, 20), (15, 0), (-9.5, 20)))

    def test_room_object_intersections(self):
        # top left
        # top right
        # bottom left
        # bottom right
        # top middle
        # bottom middle
        # left middle
        # right middle
        # top half
        # bottom half
        # left half
        # right half
        # horizontal
        # vertical
