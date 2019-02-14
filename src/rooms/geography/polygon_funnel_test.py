
import unittest

from .polygon_funnel import PolygonFunnel


class PolygonFunnelTest(unittest.TestCase):
    def setUp(self):
        self.geography = PolygonFunnel()

    def test_room_vertices(self):
        vertices = self.geography.get_vertices(self.room)

        self.assertEquals(4, len(vertices))

