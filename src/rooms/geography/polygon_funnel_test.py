
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

        self.geography.polygons = [
            polygon1,
            polygon2,
        ]

        self.geography.connect_polygons()

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
