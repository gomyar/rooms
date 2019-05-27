
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


class FunnelPolysTest(unittest.TestCase):
    def setUp(self):
        self.node = MockNode()
        self.map_source = FileMapSource(os.path.dirname(__file__))
        self.factory = RoomBuilder(self.map_source, self.node)

        self.room = self.factory.create("game1", "polyfunnel_test_map.room3")

        self.geography = PolygonFunnelGeography()

        self.geography.setup(self.room)
        self.room.geog = self.geography



    def test_funnelling(self):
        def createpoly(p1, p2, p3):
            return Polygon(Vertex(None, p1), Vertex(None, p2), Vertex(None, p3))
        poly_chain = [
            createpoly(P(-10, 30), P(0, 0), P(50, 30)),
            createpoly(P(0, 0), P(20, 0), P(50, 30)),
            createpoly(P(20, 0), P(20, -15), P(50, 30)),
            createpoly(P(20, -15), P(25, -30), P(50, 30)),
            createpoly(P(20, -15), P(25, -45), P(25, -30)),
            createpoly(P(0, -15), P(25, -45), P(20, -15)),
            createpoly(P(0, -15), P(25, -60), P(25, -45)),
            createpoly(P(-30, -5), P(25, -60), P(0, -15)),
        ]
        connect_polygons(poly_chain)
        queue = create_poly_queue(poly_chain)

        portals = [(P(0.0,0.0), P(50.0,30.0)),
                   (P(20.0,0.0), P(50.0,30.0)),
                   (P(20.0,-15.0), P(50.0,30.0)),
                   (P(20.0,-15.0), P(25.0,-30.0)),
                   (P(20.0,-15.0), P(25.0,-45.0)),
                   (P(0.0,-15.0), P(25.0,-45.0)),
                   (P(0.0,-15.0), P(25.0,-60.0))]
        portals = [((q[1].x, q[1].y), (q[2].x, q[2].y)) for q in queue]

        path = stringPull(portals, (0, 5), (-29, -6))

#        from webpolys import WebCanvas
#        mister = WebCanvas()
#        polys = [[(v.position) for v in p.vertices] for p in poly_chain]
#        mister.add_poly_list(polys)
#        mister.add_line(path)
#        mister.handle_request()

        self.assertEquals([(0, 5), (20.0, 0.0), (20.0, -15.0),
                           (0.0, -15.0), (-29, -6)], path)

    def test_real_path(self):
        from_position = P(105, -95)
        to_position = P(-5, -20)
        poly_chain = AStar(self.geography).find_path(from_position, to_position)
        connect_polygons(poly_chain)
        queue = create_poly_queue(poly_chain)
        portals = [((q[1].x, q[1].y), (q[2].x, q[2].y)) for q in queue]

        self.assertEquals([
            ((100.0, -100.0), (125.0, -125.0)),
            ((100.0, -100.0), (-125.0, -125.0)),
            ((30.0, -100.0), (-125.0, -125.0)),
            ((30.0, -85.0), (-125.0, -125.0)),
            ((-100.0, -85.0), (-125.0, -125.0)),
            ((-100.0, -35.0), (-125.0, -125.0)),
            ((-100.0, -35.0), (-125.0, 125.0)),
            ((-100.0, -35.0), (125.0, 125.0)),
            ((-100.0, -35.0), (30.0, 50.0))], portals)
        path = stringPull(portals, from_position.coords(), to_position.coords())

        self.assertEquals([
            (105.0, -95.0),
            (100.0, -100.0),
            (30.0, -100.0),
            (-100.0, -85.0),
            (-100.0, -35.0),
            (-5.0, -20.0)], path)
