
import unittest

from .polygon_funnel import PolygonFunnel
from .polygon_funnel import Vertex

from rooms.room import Room
from rooms.testutils import MockNode
from rooms.room import RoomObject
from rooms.position import Position


class PolygonFunnelTest(unittest.TestCase):
    def setUp(self):
        self.geography = PolygonFunnel()

        self.room = Room("game1", "room1", MockNode())
        self.room.coords(-50, -50, 50, 50)

        self.geography.setup(self.room)
        self.room.geog = self.geography

    def test_room_vertices(self):
        vertices = self.geography.vertices

        self.assertEquals(4, len(vertices))
        self.assertEquals([Vertex(-50, -50), Vertex(-50, 50), Vertex(50, 50), Vertex(50, -50)], vertices)

    def test_add_object(self):
        room_object = RoomObject("table", Position(-50, 0), 20, 20)
        self.room.add_object(room_object)

        vertices = self.geography.vertices

        self.assertEquals(8, len(vertices))
        self.assertEquals([
            Vertex(-50.0, -50.0),
            Vertex(-50.0, 50.0),
            Vertex(50.0, 50.0),
            Vertex(50.0, -50.0),
            Vertex(-50.0, -10.0),
            Vertex(-40.0, -10.0),
            Vertex(-40.0, 10.0),
            Vertex(-50.0, 10.0)],
            vertices)

        self.assertEquals(self.geography.vertex_at(-50, -50).next, Vertex(-50, -10))
        self.assertEquals(self.geography.vertex_at(-50, -50).previous, Vertex(50, -50))

        self.assertEquals(self.geography.vertex_at(-50, 50).next, Vertex(50, 50))
        self.assertEquals(self.geography.vertex_at(-50, 50).previous, Vertex(-50, 10))

        self.assertEquals(self.geography.vertex_at(50, 50).next, Vertex(50, -50))
        self.assertEquals(self.geography.vertex_at(50, 50).previous, Vertex(-50, 50))

        self.assertEquals(self.geography.vertex_at(50, -50).next, Vertex(-50, -50))
        self.assertEquals(self.geography.vertex_at(50, -50).previous, Vertex(50, 50))

        self.assertEquals(self.geography.vertex_at(-50, -10).next, Vertex(-40, -10))
        self.assertEquals(self.geography.vertex_at(-50, -10).previous, Vertex(-50, -50))

        self.assertEquals(self.geography.vertex_at(-40, -10).next, Vertex(-40, 10))
        self.assertEquals(self.geography.vertex_at(-40, -10).previous, Vertex(-50, -10))

        self.assertEquals(self.geography.vertex_at(-40, 10).next, Vertex(-50, 10))
        self.assertEquals(self.geography.vertex_at(-40, 10).previous, Vertex(-40, -10))

        self.assertEquals(self.geography.vertex_at(-50, 10).next, Vertex(-50, 50))
        self.assertEquals(self.geography.vertex_at(-50, 10).previous, Vertex(-40, 10))

    def test_is_occluded(self):
        room_object = RoomObject("table", Position(-50, 0), 20, 20)
        self.room.add_object(room_object)

        self.assertTrue(self.geography._is_vertex_occluded(Vertex(-50, 0)))
        self.assertFalse(self.geography._is_vertex_occluded(Vertex(10, 10)))
        self.assertTrue(self.geography._is_vertex_occluded(Vertex(-45, 5)))

    def test_get_intersects(self):
        room_object = RoomObject("table", Position(-50, 0), 20, 20)
        self.room.add_object(room_object)

        self.assertEquals([((-40, 0), Vertex(-40, -10), Vertex(-40, 10))], self.geography._get_intersects_for(Vertex(-45, 0), Vertex(0, 0)))
        # havent done point to point intersects yet
#        self.assertEquals([
#            ((-50.0, 10.0)),
#            ((-40.0, 8.0))], self.geography._get_intersects_for(Vertex(-50, 10), Vertex(0, 0)))

    def test_create_edges(self):
        self.assertEquals(4, len(self.geography.vertices))

        self.assertEquals(4, len(self.geography._build_edges()))
        self.assertEquals([
            (Vertex(-50.0, -50.0), Vertex(-50.0, 50.0)),
            (Vertex(-50.0, 50.0), Vertex(50.0, 50.0)),
            (Vertex(50.0, 50.0), Vertex(50.0, -50.0)),
            (Vertex(50.0, -50.0), Vertex(-50.0, -50.0))],
            self.geography._build_edges())

        room_object = RoomObject("table", Position(0, 0), 20, 20)
        self.room.add_object(room_object)

        self.assertEquals([
            (Vertex(-50.0, -50.0), Vertex(-50.0, 50.0)),
            (Vertex(-50.0, 50.0), Vertex(50.0, 50.0)),
            (Vertex(50.0, 50.0), Vertex(50.0, -50.0)),
            (Vertex(50.0, -50.0), Vertex(-50.0, -50.0)),
            (Vertex(10.0, -10.0), Vertex(10.0, 10.0)),
            (Vertex(10.0, 10.0), Vertex(-10.0, 10.0)),
            (Vertex(-10.0, 10.0), Vertex(-10.0, -10.0)),
            (Vertex(-10.0, -10.0), Vertex(10.0, -10.0))
            ], self.geography._build_edges())

    def test_create_edges_intersect(self):
        self.assertEquals(4, len(self.geography.vertices))

        self.assertEquals(4, len(self.geography._build_edges()))
        self.assertEquals([
            (Vertex(-50.0, -50.0), Vertex(-50.0, 50.0)),
            (Vertex(-50.0, 50.0), Vertex(50.0, 50.0)),
            (Vertex(50.0, 50.0), Vertex(50.0, -50.0)),
            (Vertex(50.0, -50.0), Vertex(-50.0, -50.0))],
            self.geography._build_edges())

        room_object = RoomObject("table", Position(-40, 0), 40, 40)
        self.room.add_object(room_object)

        self.assertEquals([
            (Vertex(-50.0, -50.0), Vertex(-50.0, -20.0)),
            (Vertex(-50.0, 50.0), Vertex(50.0, 50.0)),
            (Vertex(50.0, 50.0), Vertex(50.0, -50.0)),
            (Vertex(50.0, -50.0), Vertex(-50.0, -50.0)),
            (Vertex(-50.0, -20.0), Vertex(-20.0, -20.0)),
            (Vertex(-20.0, -20.0), Vertex(-20.0, 20.0)),
            (Vertex(-20.0, 20.0), Vertex(-50.0, 20.0)),
            (Vertex(-50.0, 20.0), Vertex(-50.0, 50.0))
            ], self.geography._build_edges())

        room_object_2 = RoomObject("table", Position(-20, -10), 40, 40)
        self.room.add_object(room_object_2)

        self.assertEquals([
            (Vertex(-50.0, -50.0), Vertex(-50.0, -20.0)),
            (Vertex(-50.0, 50.0), Vertex(50.0, 50.0)),
            (Vertex(50.0, 50.0), Vertex(50.0, -50.0)),
            (Vertex(50.0, -50.0), Vertex(-50.0, -50.0)),
            (Vertex(-50.0, -20.0), Vertex(-40.0, -20.0)),
            (Vertex(-20.0, 20.0), Vertex(-50.0, 20.0)),
            (Vertex(-50.0, 20.0), Vertex(-50.0, 50.0)),
            (Vertex(0.0, -30.0), Vertex(0.0, 10.0)),
            (Vertex(0.0, 10.0), Vertex(-20.0, 10.0)),
            (Vertex(-20.0, 10.0), Vertex(-20.0, 20.0)),
            (Vertex(-40.0, -20.0), Vertex(-40.0, -30.0)),
            (Vertex(-40.0, -30.0), Vertex(0.0, -30.0))
            ], self.geography._build_edges())
