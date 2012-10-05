
import unittest

from pointmap_geography import PointmapGeography
from rooms.room import Room


class PointmapGeogTest(unittest.TestCase):
    def setUp(self):
        self.geog = PointmapGeography(point_spacing=10)
        self.room = Room("room1", (0, 0), 50, 50)

    def testGetPath(self):
        path = self.geog.get_path(self.room, (10, 10), (20, 20))
        self.assertEquals(25, len(self.geog._pointmaps[self.room]._points))
        self.assertEquals([(1, 1), (2, 2)], path)

        path = self.geog.get_path(self.room, (10, 10), (20, 40))
        self.assertEquals([(1, 1), (2, 2), (2, 3), (2, 4)], path)
