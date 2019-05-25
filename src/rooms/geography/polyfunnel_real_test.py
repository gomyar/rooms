
import unittest
import math
import os

from rooms.testutils import MockNode
from rooms.room_builder import RoomBuilder
from rooms.room_builder import FileMapSource

from rooms.position import Position as P
from .polygon_funnel import PolygonFunnelGeography
from .polygon_funnel import Vertex
from .polygon_funnel import Polygon
from .polygon_funnel import Connection
from .polygon_funnel import angle
from .polygon_funnel import diff_angles
from .polygon_funnel import angle_max
from .polygon_funnel import angle_min
from .polygon_funnel import connect_polygons


class PolygonFunnelTest(unittest.TestCase):
    def setUp(self):
        self.node = MockNode()
        self.map_source = FileMapSource(os.path.dirname(__file__))
        self.factory = RoomBuilder(self.map_source, self.node)

        self.room = self.factory.create("game1", "polyfunnel_test_map.room3")

        self.geography = PolygonFunnelGeography()

        self.geography.setup(self.room)
        self.room.geog = self.geography

    def test_path(self):
        from_position = P(-5, -20)
        to_position = P(20, -90)

        path = self.geography.find_path(self.room, from_position, to_position)

        self.assertEquals([P(-5, -20), P(-100, -35), P(-100, -85), P(20, -90)], path)

    def test_path_back(self):
        from_position = P(20, -90)
        to_position = P(-5, -20)

        path = self.geography.find_path(self.room, from_position, to_position)

        self.assertEquals([P(20, -90), P(-100, -85), P(-100, -35), P(-5, -20)], path)

    def test_path_center_northeast(self):
        from_position = P(-5, -20)
        to_position = P(105, -95)

        path = self.geography.find_path(self.room, from_position, to_position)

        self.assertEquals([P(-5, -20), P(30, 50), P(100, 50), P(105, -95)], path)

    def test_path_northeast_center(self):
        from_position = P(105, -95)
        to_position = P(-5, -20)

        path = self.geography.find_path(self.room, from_position, to_position)

#        from webpolys import WebCanvas
#        mister = WebCanvas()
#        polys = [[(v.position) for v in p.vertices] for p in self.geography.polygons]
#        mister.add_poly_list(polys)
#        mister.add_line(path)
#        mister.handle_request()

        self.assertEquals([
            P(105.0,-95.0),
            P(100.0,-100.0),
            P(30.0,-100.0),
            P(-100.0,-85.0),
            P(-100.0,-35.0),
            P(-5.0,-20.0)], path)

    def test_between_the_cracks(self):
        self.room = self.factory.create("game1", "polyfunnel_test_map.room1")

        self.geography = PolygonFunnelGeography()

        self.geography.setup(self.room)
        self.room.geog = self.geography

        from_position = P(10, -10)
        to_position = P(10, 10)

        path = self.geography.find_path(self.room, from_position, to_position)

        self.assertEquals([P(10, -10), P(10, 10)], path)
