
import unittest
import math

from rooms.room import Room
from rooms.room import RoomObject
from rooms.position import Position as P
from rooms.testutils import MockNode
from .polygon_funnel import PolygonFunnelGeography
from .polygon_funnel import Vertex
from .polygon_funnel import Segment
from .polygon_funnel import get_vertices
from .polygon_funnel import get_next_node
from .polygon_funnel import get_nodes_for
from .polygon_funnel import complete_segments
from .polygon_funnel import get_all_vertices
from .polygon_funnel import get_vertices_between
from .polygon_funnel import _angle
from .polygon_funnel import _diff


class PolygonFunnelTest(unittest.TestCase):
    def setUp(self):
        self.geography = PolygonFunnelGeography()
        self.room = Room("game1", "room1", MockNode())
        self.room.coords(-50, -50, 50, 50)
        self.room.geog = self.geography

    def test_get_object_vertices(self):
        room_object = RoomObject("test", P(50, 50), 20, 20)
        vertices, segments = get_vertices(room_object)
        self.assertEquals(4, len(vertices))
        self.assertEquals(2, len(segments))

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

        s1, s2 = segments
        self.assertEquals(Segment(v1, v2, v4), s1)
        self.assertEquals(Segment(v3, v4, v2), s2)

        self.assertEquals([[v2, v4]], v1.segments)
        self.assertEquals([[v3, v4], [v4, v1]], v2.segments)
        self.assertEquals([[v4, v2]], v3.segments)
        self.assertEquals([[v1, v2], [v2, v3]], v4.segments)


    def test_angles(self):
        obj = RoomObject("test", P(0, 0), 20, 20)
        def V(x, y):
            return Vertex(obj, P(x, y))
        self.assertEquals(0, _angle(V(0, 0), V(10, 0)))
        self.assertEquals(math.pi / 4, _angle(V(0, 0), V(10, 10)))
        self.assertEquals(math.pi / 2, _angle(V(0, 0), V(0, 10)))
        self.assertEquals(math.pi * 3 / 4, _angle(V(0, 0), V(-10, 10)))
        self.assertEquals(math.pi, _angle(V(0, 0), V(-10, 0)))
        self.assertEquals(math.pi * 5 / 4, _angle(V(0, 0), V(-10, -10)))
        self.assertEquals(math.pi * 6 / 4, _angle(V(0, 0), V(0, -10)))
        self.assertEquals(math.pi * 7 / 4, _angle(V(0, 0), V(10, -10)))

        self.assertEquals(math.pi / 4, _diff(V(0, 0), V(10, 0), V(10, 10)))
        self.assertEquals(math.pi / 4, _diff(V(0, 0), V(0, 10), V(-10, 10)))
        self.assertEquals(math.pi / 2, _diff(V(0, 0), V(10, -10), V(10, 10)))
        self.assertAlmostEquals(math.pi, _diff(V(0, 0), V(10, 2), V(-10, -2)))

        self.assertAlmostEquals(6.0838480021972625, _diff(V(0, 0), V(-1, 10), V(1, 10)))

    def test_segments_complete(self):
        obj = RoomObject("test", P(0, 0), 20, 20)
        def V(x, y):
            return Vertex(obj, P(x, y))
        self.room.room_objects.append(obj)

        v1 = V(0, 0)
        v1.segments = [
            [V(10, -10), V(10, 10)],
            [V(10, 10), V(-10, 10)],
            [V(-10, 10), V(-10, -10)],
            [V(-10, -10), V(10, -10)],
        ]

        self.assertTrue(complete_segments(v1))

        self.assertEquals(None, get_next_node(self.room, v1))

    def test_get_all_vertices(self):
        obj = RoomObject("test", P(0, 0), 20, 20)
        def V(x, y):
            return Vertex(obj, P(x, y))
        self.room.room_objects.append(obj)

        vertices = get_all_vertices(self.room)
        self.assertEquals([
            V(-10, -10),
            V(10, -10),
            V(10, 10),
            V(-10, 10),
            # plus room corners
            V(-50.0, -50.0),
            V(50.0, -50.0),
            V(50.0, 50.0),
            V(-50.0, 50.0),
        ], vertices)

        # test for second object
        obj = RoomObject("test", P(20, 20), 10, 10)
        self.room.room_objects.append(obj)

        vertices = get_all_vertices(self.room)
        self.assertEquals([
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
            # plus room corners
            V(-50.0, -50.0),
            V(50.0, -50.0),
            V(50.0, 50.0),
            V(-50.0, 50.0),
        ], vertices)

    def test_get_vertices_between(self):
        obj = RoomObject("test", P(0, 0), 20, 20)
        def V(x, y):
            return Vertex(obj, P(x, y))
        self.room.room_objects.append(obj)

        v1 = V(0, 0)
        v2 = V(10, 10)
        v3 = V(-10, 10)
        v4 = V(5, 15)
        v5 = V(-5, 20)

        # order is important
        vertices = get_vertices_between([v1, v2, v3, v5, v4], v1, v2, v3)
        self.assertEquals(2, len(vertices))

        # order is important
        self.assertEquals([v4, v5], vertices)

        vertices = get_vertices_between([v1, v2, v3, v5, v4], v1, v2, v4)
        self.assertEquals([], vertices)

    def test_next_node(self):
        obj = RoomObject("test", P(0, 0), 20, 20)
        def V(x, y):
            return Vertex(obj, P(x, y))
        self.room.room_objects.append(obj)

        vertices, segments = get_vertices(obj)
        v1, v2, v3, v4 = vertices

        node = get_next_node(self.room, v1)
        self.assertEquals(Segment(v1, v4, V(-50, 50)), node)

        v1.segments.append([v4, V(-50, 50)])

        node = get_next_node(self.room, v1)
        self.assertEquals(Segment(v1, V(-50, 50), V(-50, -50)), node)

        v1.segments.append([V(-50, 50), V(-50, -50)])
        self.assertEquals(Segment(v1, V(-50, -50), V(50, -50)), get_next_node(self.room, v1))

        v1.segments.append([V(-50, -50), V(50, -50)])
        self.assertEquals(Segment(v1, V(50, -50), v2), get_next_node(self.room, v1))

        v1.segments.append([V(50, -50), v2])
        self.assertEquals(None, get_next_node(self.room, v1))

    def test_get_nodes_for(self):
        obj = RoomObject("test", P(0, 0), 20, 20)
        def V(x, y):
            return Vertex(obj, P(x, y))
        self.room.room_objects.append(obj)

        vertices, segments = get_vertices(obj)
        v1, v2, v3, v4 = vertices

        nodes = get_nodes_for(self.room, v1)
        self.assertEquals(nodes, [
            Segment(v1, v4, V(-50, 50)),
            Segment(v1, V(-50, 50), V(-50, -50)),
            Segment(v1, V(-50, -50), V(50, -50)),
            Segment(v1, V(50, -50), v2),
        ], nodes)

    def test_create_polymap(self):
        self.room.room_objects.append(RoomObject("test", P(50, 50), 20, 20))

        self.geography.init(self.room)

        self.assertEquals(8, len(self.geography.nodes))
