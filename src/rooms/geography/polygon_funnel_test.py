
import unittest
import math

from rooms.room import Room
from rooms.room import RoomObject
from rooms.position import Position as P
from rooms.testutils import MockNode
from .polygon_funnel import PolygonFunnelGeography
from .polygon_funnel import Vertex
from .polygon_funnel import Polygon
from .polygon_funnel import Connection
from .polygon_funnel import angle
from .polygon_funnel import diff_angles
from .polygon_funnel import angle_max
from .polygon_funnel import angle_min
from .polygon_funnel import connect_polygons
from rooms.geography.funnel_poly_chain import stringPull
from rooms.geography.polygon_funnel import create_poly_queue


class PolygonFunnelTest(unittest.TestCase):
    def setUp(self):
        self.room = Room("game1", "room1", MockNode())
        self.room.coords(-50, -50, 50, 50)

        self.geography = PolygonFunnelGeography()

    def test_get_object_vertices(self):
        self.geography.setup(self.room)
        self.room.geog = self.geography

        room_object = RoomObject("test", P(50, 50), 20, 20)
        vertices = self.geography.get_vertices(room_object)
        self.assertEquals(4, len(vertices))

        v1, v2, v3, v4 = vertices
        self.assertEquals(P(40, 40), v1.position)
        self.assertEquals(P(60, 40), v2.position)
        self.assertEquals(P(60, 60), v3.position)
        self.assertEquals(P(40, 60), v4.position)

        self.assertEquals(v4, v1.previous)
        self.assertEquals(v2, v1.next)
        self.assertEquals(v1, v2.previous)
        self.assertEquals(v3, v2.next)
        self.assertEquals(v2, v3.previous)
        self.assertEquals(v4, v3.next)
        self.assertEquals(v3, v4.previous)
        self.assertEquals(v1, v4.next)

    def testangles(self):
        obj = RoomObject("test", P(0, 0), 20, 20)
        def V(x, y):
            return Vertex(obj, P(x, y))
        self.assertEquals(0, angle(V(0, 0), V(10, 0)))
        self.assertEquals(math.pi / 4, angle(V(0, 0), V(10, 10)))
        self.assertEquals(math.pi / 2, angle(V(0, 0), V(0, 10)))
        self.assertEquals(math.pi * 3 / 4, angle(V(0, 0), V(-10, 10)))
        self.assertEquals(math.pi, angle(V(0, 0), V(-10, 0)))
        self.assertEquals(math.pi * 5 / 4, angle(V(0, 0), V(-10, -10)))
        self.assertEquals(math.pi * 6 / 4, angle(V(0, 0), V(0, -10)))
        self.assertEquals(math.pi * 7 / 4, angle(V(0, 0), V(10, -10)))

    def test_get_all_vertices(self):
        self.geography.setup(self.room)
        self.room.geog = self.geography

        obj = RoomObject("test", P(0, 0), 20, 20)
        def V(x, y):
            return Vertex(obj, P(x, y))
        self.room.room_objects.append(obj)

        vertices = self.geography.get_all_vertices()
        self.assertEquals([
            # room corners
            V(-50.0, -50.0),
            V(50.0, -50.0),
            V(50.0, 50.0),
            V(-50.0, 50.0),
            # object
            V(-10, -10),
            V(10, -10),
            V(10, 10),
            V(-10, 10),
        ], vertices)

        # test for second object
        obj = RoomObject("test", P(20, 20), 10, 10)
        self.room.room_objects.append(obj)

        vertices = self.geography.get_all_vertices()
        self.assertEquals([
            # room corners
            V(-50.0, -50.0),
            V(50.0, -50.0),
            V(50.0, 50.0),
            V(-50.0, 50.0),
            # first object
            V(-10, -10),
            V(10, -10),
            V(10, 10),
            V(-10, 10),
            # second object
            V(15, 15),
            V(25, 15),
            V(25, 25),
            V(15, 25),
        ], vertices)

    def test_polyfill(self):
        self.geography.setup(self.room)
        self.room.geog = self.geography

        self.room.room_objects.append(RoomObject("test", P(0, 0), 20, 20))

        self.assertEquals([
            Polygon(Vertex(None, P(-50.0,-50.0)), Vertex(None, P(50.0,-50.0)), Vertex(None, P(10.0,-10.0))),
            Polygon(Vertex(None, P(-50.0,-50.0)), Vertex(None, P(10.0,-10.0)), Vertex(None, P(-10.0,-10.0))),
            Polygon(Vertex(None, P(-50.0,-50.0)), Vertex(None, P(-10.0,-10.0)), Vertex(None, P(-10.0,10.0))),
            Polygon(Vertex(None, P(-50.0,-50.0)), Vertex(None, P(-10.0,10.0)), Vertex(None, P(-50.0,50.0))),
            Polygon(Vertex(None, P(50.0,-50.0)), Vertex(None, P(50.0,50.0)), Vertex(None, P(10.0,10.0))),
            Polygon(Vertex(None, P(50.0,-50.0)), Vertex(None, P(10.0,10.0)), Vertex(None, P(10.0,-10.0))),
            Polygon(Vertex(None, P(50.0,50.0)), Vertex(None, P(-50.0,50.0)), Vertex(None, P(-10.0,10.0))),
            Polygon(Vertex(None, P(50.0,50.0)), Vertex(None, P(-10.0,10.0)), Vertex(None, P(10.0,10.0)))],
            self.geography.polyfill())

    def test_polygon_midpoint(self):
        polygon1 = Polygon(Vertex(None, P(0.0, 0.0)), Vertex(None, P(60.0, 0.0)), Vertex(None, P(0.0, 60.0)))
        polygon2 = Polygon(Vertex(None, P(0.0, 60.0)), Vertex(None, P(60.0, 0.0)), Vertex(None, P(60.0, 60.0)))

        self.assertEquals(P(20, 20), polygon1.midpoint)
        self.assertEquals(P(40, 40), polygon2.midpoint)

        self.assertEquals(28.284271247461902, polygon1.distance_to(polygon2))

    def test_create_graph(self):
        polygon1 = Polygon(Vertex(None, P(0.0, 0.0)), Vertex(None, P(60.0, 0.0)), Vertex(None, P(0.0, 60.0)))
        polygon2 = Polygon(Vertex(None, P(0.0, 60.0)), Vertex(None, P(60.0, 0.0)), Vertex(None, P(60.0, 60.0)))

        polygons = [
            polygon1,
            polygon2,
        ]

        connect_polygons(polygons)

        self.assertEquals(polygon1.connections, [
            Connection(polygon2, Vertex(None, P(60, 0)), Vertex(None, P(0, 60)))])
        self.assertEquals(polygon2.connections, [
            Connection(polygon1, Vertex(None, P(0, 60)), Vertex(None, P(60, 0)))])

    def test_point_within_polygon(self):
        polygon1 = Polygon(Vertex(None, P(0.0, 0.0)), Vertex(None, P(60.0, 0.0)), Vertex(None, P(0.0, 60.0)))
        polygon2 = Polygon(Vertex(None, P(0.0, 60.0)), Vertex(None, P(60.0, 0.0)), Vertex(None, P(60.0, 60.0)))

        self.assertTrue(polygon1.point_within(P(1, 1)))
        self.assertTrue(polygon1.point_within(P(1, 58)))
        self.assertTrue(polygon1.point_within(P(58, 1)))
        self.assertFalse(polygon1.point_within(P(-1, 1)))
        self.assertFalse(polygon1.point_within(P(1, -1)))
        self.assertFalse(polygon1.point_within(P(1, 60)))
        self.assertFalse(polygon1.point_within(P(60, 1)))

        self.assertTrue(polygon2.point_within(P(5, 59)))

    def test_polygon_equality(self):
        polygon1 = Polygon(Vertex(None, P(0.0, 0.0)), Vertex(None, P(60.0, 0.0)), Vertex(None, P(0.0, 60.0)))
        polygon2 = Polygon(Vertex(None, P(0.0, 60.0)), Vertex(None, P(0.0, 0.0)), Vertex(None, P(60.0, 0.0)))

        self.assertTrue(polygon1 == polygon2)

    def test_funnelling(self):
        def createpoly(p1, p2, p3):
            return Polygon(Vertex(None, p1), Vertex(None, p2), Vertex(None, p3))
        poly_chain = [
            createpoly(P(0, 20), P(20, 20), P(10, 30)),
            createpoly(P(0, 20), P(20, 10), P(20, 20)),
            createpoly(P(0, 20), P(0, 10), P(20, 10)),
            createpoly(P(0, 10), P(10, 0), P(20, 10)),
        ]
        connect_polygons(poly_chain)

        poly_queue = create_poly_queue(poly_chain)
        portals = [((q[1].x, q[1].y), (q[2].x, q[2].y)) for q in poly_queue]

        path = stringPull(portals, (10, 25), (10, 5))

        self.assertEquals([(10, 25), (10, 5)], path)

    def test_funnel_left(self):
        def createpoly(p1, p2, p3):
            return Polygon(Vertex(None, p1), Vertex(None, p2), Vertex(None, p3))
        poly_chain = [
            createpoly(P(10, 30), P(0, 20), P(20, 20)),
            createpoly(P(0, 20), P(0, 10), P(20, 20)),
            createpoly(P(0, 20), P(-10, 10), P(0, 10)),
            createpoly(P(-10, 10), P(0, 0), P(0, 10)),
            createpoly(P(0, 0), P(20, 0), P(0, 10)),
            createpoly(P(0, 0), P(10, -10), P(20, 0)),
        ]
        connect_polygons(poly_chain)

        poly_queue = create_poly_queue(poly_chain)
        portals = [((q[1].x, q[1].y), (q[2].x, q[2].y)) for q in poly_queue]

        path = stringPull(portals, (10, 25), (10, 5))

        self.assertEquals([(10, 25), (0, 10), (20, 0), (10, 5)], path)

    def test_funnel_left_left_left(self):
        def createpoly(p1, p2, p3):
            return Polygon(Vertex(None, p1), Vertex(None, p2), Vertex(None, p3))
        poly_chain = [
            createpoly(P(10, 30), P(0, 20), P(20, 20)),
            createpoly(P(0, 20), P(0, 10), P(20, 20)),
            createpoly(P(0, 20), P(-10, 10), P(0, 10)),
            createpoly(P(-10, 10), P(0, 0), P(0, 10)),
            createpoly(P(0, 0), P(20, 0), P(0, 10)),
            createpoly(P(0, 0), P(10, -10), P(20, 0)),

            createpoly(P(0, 0), P(0, -10), P(10, -10)),
            createpoly(P(0, 0), P(-10, -10), P(0, -10)),
        ]
        connect_polygons(poly_chain)

        poly_queue = create_poly_queue(poly_chain)
        portals = [((q[1].x, q[1].y), (q[2].x, q[2].y)) for q in poly_queue]

        path = stringPull(portals, (10, 25), (-5, -7))

        self.assertEquals([(10, 25), (0, 10), (0, 0), (-5, -7)], path)

    def test_funnel_no_polys(self):
        self.assertEquals([], self.geography.funnel_poly_chain([], P(10, 10), P(20, 20)))

    def test_funnel_same_poly(self):
        poly_chain = [
            Polygon(Vertex(None, P(0, 0)), Vertex(None, P(30, 0)), Vertex(None, P(0, 30)))
        ]
        connect_polygons(poly_chain)
        self.assertEquals([P(10, 10), P(20, 20)], self.geography.funnel_poly_chain(poly_chain, P(10, 10), P(20, 20)))

    def test_two_polys_left_occluded(self):
        def createpoly(p1, p2, p3):
            return Polygon(Vertex(None, p1), Vertex(None, p2), Vertex(None, p3))
        poly_chain = [
            createpoly(P(0, 0), P(20, 0), P(0, 20)),
            createpoly(P(0, 0), P(-20, -20), P(20, 0)),
        ]
        connect_polygons(poly_chain)
        expected = [(2, 15), (0, 0), (-15, -15)]

        poly_queue = create_poly_queue(poly_chain)
        portals = [((q[1].x, q[1].y), (q[2].x, q[2].y)) for q in poly_queue]

        path = stringPull(portals, (2, 15), (-15, -15))

        self.assertEquals(expected, path)

    def test_two_polys_right_occluded(self):
        def createpoly(p1, p2, p3):
            return Polygon(Vertex(None, p1), Vertex(None, p2), Vertex(None, p3))
        poly_chain = [
            createpoly(P(0, 0), P(0, 20), P(-20, 0)),
            createpoly(P(0, 0), P(-20, 0), P(20, -20)),
        ]
        connect_polygons(poly_chain)
        expected = [(-2, 15), (0, 0), (15, -15)]

        poly_queue = create_poly_queue(poly_chain)
        portals = [((q[1].x, q[1].y), (q[2].x, q[2].y)) for q in poly_queue]

        path = stringPull(portals, (-2, 15), (15, -15))

        self.assertEquals(expected, path)

    def test_diff_angles(self):
        self.assertEquals(math.pi / 4, diff_angles(P(0, 0), P(10, 10), P(0, 0), P(0, 10)))
        self.assertEquals(math.pi / 4, diff_angles(P(0, 0), P(-10, -10), P(0, 0), P(0, -10)))
        self.assertEquals(math.pi / 2, diff_angles(P(0, 0), P(10, -10), P(0, 0), P(10, 10)))
        self.assertEquals(-math.pi / 2, diff_angles(P(0, 0), P(10, 10), P(0, 0), P(10, -10)))
        self.assertEquals(math.pi / 2, diff_angles(P(0, 0), P(-10, 10), P(0, 0), P(-10, -10)))
        self.assertEquals(-math.pi / 2, diff_angles(P(0, 0), P(-10, -10), P(0, 0), P(-10, 10)))

    def test_angle_max_min(self):
        self.assertEquals(0.2, angle_max(0.1, 0.2))
        self.assertEquals(0.2, angle_max(0.2, 0.1))
        self.assertEquals(0.1, angle_min(0.1, 0.2))
        self.assertEquals(0.1, angle_min(0.2, 0.1))

        self.assertEquals(0.1, angle_max(0.1, math.pi * 2 * 7 / 8))
        self.assertEquals(math.pi * 2 * 7 / 8, angle_min(0.1, math.pi * 2 * 7 / 8))

    def test_narrow_then_wide_around_corner(self):
        def createpoly(p1, p2, p3):
            return Polygon(Vertex(None, p1), Vertex(None, p2), Vertex(None, p3))
        poly_chain = [
            createpoly(P(0, 20), P(10, -10), P(10, 20)),
            createpoly(P(0, 0), P(10, -10), P(0, 20)),
            createpoly(P(0, 0), P(-20, 0), P(10, -10)),
        ]
        connect_polygons(poly_chain)
        expected = [(5, 15), (0, 0), (-15, -5)]

        poly_queue = create_poly_queue(poly_chain)
        portals = [((q[1].x, q[1].y), (q[2].x, q[2].y)) for q in poly_queue]

        path = stringPull(portals, (5, 15), (-15, -5))

        self.assertEquals(expected, path)

    def test_narrow_then_wide_around_corner_2(self):
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
        expected = [(30, 25), (20, -15), (5, -30)]

        poly_queue = create_poly_queue(poly_chain)
        portals = [((q[1].x, q[1].y), (q[2].x, q[2].y)) for q in poly_queue]

        path = stringPull(portals, (30, 25), (5, -30))

        self.assertEquals(expected, path)
