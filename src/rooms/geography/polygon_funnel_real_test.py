
import os
import unittest
from .polygon_funnel import connect_polygons
from .polygon_funnel import create_poly_queue
from .polygon_funnel import Polygon
from .polygon_funnel import Vertex
from .funnel_poly_chain import stringPull
from .polygon_funnel import PolygonFunnelGeography
from rooms.position import Position as P
from rooms.geography.astar_polyfunnel import AStar
from rooms.testutils import MockNode
from rooms.room_builder import FileMapSource
from rooms.room_builder import RoomBuilder


class PolyfunnelRealTest(unittest.TestCase):
    def setUp(self):
        self.node = MockNode()
        self.map_source = FileMapSource(os.path.dirname(__file__))
        self.factory = RoomBuilder(self.map_source, self.node)

        self.room = self.factory.create("game1", "kitchen_test.kitchen")

        self.geography = PolygonFunnelGeography()

        self.room.geog = self.geography

    def test_polys_for_kitchen(self):
        self.geography.setup(self.room)

#        from webpolys import WebCanvas
#        mister = WebCanvas()
#        polys = [[(v.position) for v in p.vertices] for p in self.geography.polygons]
#        mister.add_poly_list(polys)
#        # mister.add_line(path)
#        mister.handle_request()

        self.assertEquals([
            Polygon(Vertex(None, P(-212.39567087, -257.91731654)), Vertex(None, P(212.39567087, -257.91731654)), Vertex(None, P(212.39567087, -65.0))),
            Polygon(Vertex(None, P(-212.39567087, -257.91731654)), Vertex(None, P(212.39567087, -65.0)), Vertex(None, P(165.0, -65.0))),
            Polygon(Vertex(None, P(-212.39567087, -257.91731654)), Vertex(None, P(165.0, -65.0)), Vertex(None, P(10.0, -140.0))),
            Polygon(Vertex(None, P(-212.39567087, -257.91731654)), Vertex(None, P(10.0, -140.0)), Vertex(None, P(-90.0, -140.0))),
            Polygon(Vertex(None, P(-212.39567087, -257.91731654)), Vertex(None, P(-90.0, -140.0)), Vertex(None, P(-90.0, 80.0))),
            Polygon(Vertex(None, P(-212.39567087, -257.91731654)), Vertex(None, P(-90.0, 80.0)), Vertex(None, P(-212.39567087, 257.91731654))),
            Polygon(Vertex(None, P(212.39567087, 257.91731654)), Vertex(None, P(-212.39567087, 257.91731654)), Vertex(None, P(-90.0, 80.0))),
            Polygon(Vertex(None, P(212.39567087, 257.91731654)), Vertex(None, P(-90.0, 80.0)), Vertex(None, P(10.0, 80.0))),
            Polygon(Vertex(None, P(212.39567087, 257.91731654)), Vertex(None, P(10.0, 80.0)), Vertex(None, P(10.0, -140.0))),
            Polygon(Vertex(None, P(212.39567087, 257.91731654)), Vertex(None, P(10.0, -140.0)), Vertex(None, P(165.0, 85.0))),
            Polygon(Vertex(None, P(212.39567087, 257.91731654)), Vertex(None, P(165.0, 85.0)), Vertex(None, P(212.39567087, 85.0))),
            Polygon(Vertex(None, P(10.0, -140.0)), Vertex(None, P(165.0, -65.0)), Vertex(None, P(165.0, 85.0)))],
            self.geography.polyfill())
