
import unittest
import math

from rooms.room import Room
from rooms.room import RoomObject
from rooms.position import Position as P
from rooms.testutils import MockNode
from .polygon_funnel import PolygonFunnelGeography
from .polygon_funnel import Vertex
from .polygon_funnel import Sector
from .polygon_funnel import angle


class PolygonFunnelTest(unittest.TestCase):
    def setUp(self):
        self.room = Room("game1", "room1", MockNode())
        self.room.coords(-50, -50, 50, 50)

        self.geography = PolygonFunnelGeography()
        self.geography.setup(self.room)
        self.room.geog = self.geography

    def test_get_object_vertices(self):
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

        self.assertEquals([[v2, v4]], v1.sectors)
        self.assertEquals([[v3, v4], [v4, v1]], v2.sectors)
        self.assertEquals([[v4, v2]], v3.sectors)
        self.assertEquals([[v1, v2], [v2, v3]], v4.sectors)

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

    def test_get_vertices_betweenangles(self):
        obj = RoomObject("test", P(0, 0), 20, 20)
        def V(x, y):
            return Vertex(obj, P(x, y))
        vertices = [V(5, 5), V(15, 5), V(5, 15)]
        self.assertEquals([V(15, 5), V(5, 5)], self.geography.get_vertices_betweenangle(vertices, V(0, 0), V(5, 10), 0))

    def test_vertex_sectors(self):
        # each vertex has a list of (circle) sectors which fill all the angles for that vertex
        obj = RoomObject("test", P(0, 0), 20, 20)
        def V(x, y):
            return Vertex(obj, P(x, y))

        vertex = V(50, 50)
        vertex.add_sector(V(55, 80), V(45, 80))
        vertex.add_sector(V(10, 60), V(10, 40))
        vertex.add_sector(V(70, 30), V(85, 40))
        vertex.add_sector(V(85, 40), V(80, 55))

        self.assertEquals([
            [[V(55, 80), V(45, 80)]],
            [[V(10, 60), V(10, 40)]],
            [[V(70, 30), V(85, 40)], [V(85, 40), V(80, 55)]]
        ], vertex.sectors_gaps())

        # sectors added in order
        vertex.add_sector(V(80, 60), V(60, 80))

        self.assertEquals([
            [[V(80, 60), V(60, 80)]],  # added in order
            [[V(55, 80), V(45, 80)]],
            [[V(10, 60), V(10, 40)]],
            [[V(70, 30), V(85, 40)], [V(85, 40), V(80, 55)]]
        ], vertex.sectors_gaps())

        # adding another sector
        vertex.add_sector(V(40, 10), V(60, 10))

        self.assertEquals([
            [[V(80, 60), V(60, 80)]],
            [[V(55, 80), V(45, 80)]],
            [[V(10, 60), V(10, 40)]],
            [[V(40, 10), V(60, 10)]],  # added in order
            [[V(70, 30), V(85, 40)], [V(85, 40), V(80, 55)]]
        ], vertex.sectors_gaps())

        # add sector which joins with existing
        vertex.add_sector(V(45, 80), V(0, 90))

        self.assertEquals([
            [[V(80, 60), V(60, 80)]],
            [[V(55, 80), V(45, 80)], [V(45, 80), V(0, 90)]],  # joined with existing
            [[V(10, 60), V(10, 40)]],
            [[V(40, 10), V(60, 10)]],
            [[V(70, 30), V(85, 40)], [V(85, 40), V(80, 55)]]
        ], vertex.sectors_gaps())

        # adding a sector will fill in the gap if they join with others
        vertex.add_sector(V(10, 40), V(40, 10))

        self.assertEquals([
            [[V(80, 60), V(60, 80)]],
            [[V(55, 80), V(45, 80)], [V(45, 80), V(0, 90)]],
            [[V(10, 60), V(10, 40)], [V(10, 40), V(40, 10)], [V(40, 10), V(60, 10)]],
            [[V(70, 30), V(85, 40)], [V(85, 40), V(80, 55)]]
        ], vertex.sectors_gaps())

        # fill all the others
        vertex.add_sector(V(60, 10), V(70, 30))
        vertex.add_sector(V(80, 55), V(80, 60))
        vertex.add_sector(V(60, 80), V(55, 80))
        vertex.add_sector(V(0, 90), V(10, 60))

        self.assertEquals([[
            [V(80, 55), V(80, 60)],
            [V(80, 60), V(60, 80)],
            [V(60, 80), V(55, 80)],
            [V(55, 80), V(45, 80)],
            [V(45, 80), V(0, 90)],
            [V(0, 90), V(10, 60)],
            [V(10, 60), V(10, 40)],
            [V(10, 40), V(40, 10)],
            [V(40, 10), V(60, 10)],
            [V(60, 10), V(70, 30)],
            [V(70, 30), V(85, 40)],
            [V(85, 40), V(80, 55)],
        ]], vertex.sectors_gaps())

        # the last sector may be > pi*2

    def test_sectors_complete(self):
        obj = RoomObject("test", P(0, 0), 20, 20)
        def V(x, y):
            return Vertex(obj, P(x, y))
        self.room.room_objects.append(obj)

        v1 = V(0, 0)
        v1.sectors = [
            [V(10, -10), V(10, 10)],
            [V(10, 10), V(-10, 10)],
            [V(-10, 10), V(-10, -10)],
            [V(-10, -10), V(10, -10)],
        ]

        self.assertTrue(v1.complete_sectors())

        self.assertEquals(None, self.geography.get_next_sector(v1))

    def test_get_all_vertices(self):
        obj = RoomObject("test", P(0, 0), 20, 20)
        def V(x, y):
            return Vertex(obj, P(x, y))
        self.room.room_objects.append(obj)

        vertices = self.geography.get_all_vertices()
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

        vertices = self.geography.get_all_vertices()
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
        vertices = self.geography.get_vertices_between([v1, v2, v3, v5, v4], v1, v2, v3)
        self.assertEquals(2, len(vertices))

        # order is important
        self.assertEquals([v4, v5], vertices)

        vertices = self.geography.get_vertices_between([v1, v2, v3, v5, v4], v1, v2, v4)
        self.assertEquals([], vertices)

    def test_get_vertices_between_zero(self):
        obj = RoomObject("test", P(0, 0), 20, 20)
        def V(x, y):
            return Vertex(obj, P(x, y))
        self.room.room_objects.append(obj)

        v1 = V(0, 0)
        v2 = V(10, -10)
        v3 = V(10, 10)
        v4 = V(15, 5)
        v5 = V(20, -5)

        # order is important
        vertices = self.geography.get_vertices_between([v1, v2, v3, v5, v4], v1, v2, v3)
        self.assertEquals(2, len(vertices))

        # order is important
        self.assertEquals([v4, v5], vertices)

        vertices = self.geography.get_vertices_between([v1, v2, v3, v5, v4], v1, v2, v4)
        self.assertEquals([v5], vertices)

    def test_next_node(self):
        obj = RoomObject("test", P(0, 0), 20, 20)
        def V(x, y):
            return Vertex(obj, P(x, y))
        self.room.room_objects.append(obj)

        vertices = self.geography.get_vertices(obj)
        v1, v2, v3, v4 = vertices

        node = self.geography.get_next_sector(v1)
        self.assertEquals(Sector(v1, v4, V(-50, 50)), node)

        v1.sectors.append([v4, V(-50, 50)])

        node = self.geography.get_next_sector(v1)
        self.assertEquals(Sector(v1, V(-50, 50), V(-50, -50)), node)

        v1.sectors.append([V(-50, 50), V(-50, -50)])
        self.assertEquals(Sector(v1, V(-50, -50), V(50, -50)), self.geography.get_next_sector(v1))

        v1.sectors.append([V(-50, -50), V(50, -50)])
        self.assertEquals(Sector(v1, V(50, -50), v2), self.geography.get_next_sector(v1))

        v1.sectors.append([V(50, -50), v2])
        self.assertEquals(None, self.geography.get_next_sector(v1))

    def test_get_sectors_for(self):
        obj = RoomObject("test", P(0, 0), 20, 20)
        def V(x, y):
            return Vertex(obj, P(x, y))
        self.room.room_objects.append(obj)

        vertices = self.geography.get_vertices(obj)
        v1, v2, v3, v4 = vertices

        sectors = self.geography.get_sectors_for(v1)
        self.assertEquals(sectors, [
            Sector(v1, v4, V(-50, 50)),
            Sector(v1, V(-50, 50), V(-50, -50)),
            Sector(v1, V(-50, -50), V(50, -50)),
            Sector(v1, V(50, -50), v2),
        ], sectors)

        sectors = self.geography.get_sectors_for(v2)
        self.assertEquals(sectors, [
            Sector(v2, V(50, 50), v3),
            Sector(v2, V(50, -50), V(50, 50)),
        ], sectors)

        sectors = self.geography.get_sectors_for(v3)
        self.assertEquals(sectors, [
            Sector(v3, V(50, 50), V(-50, 50)),
            Sector(v3, V(-50, 50), v4),
        ], sectors)

        sectors = self.geography.get_sectors_for(v4)
        self.assertEquals(sectors, [
        ], sectors)

    def test_filter_occluded_polygons(self):
        obj = RoomObject("test", P(0, 0), 20, 20)
        def V(x, y):
            return Vertex(obj, P(x, y))
        vertex = V(0, 0)
        v1 = V(-10, 50)
        v2 = V(10, 50)

        # occluding Sector
        v3 = V(-10, 20)
        v4 = V(10, 20)
        v5 = V(10, 30)
        v3.sectors.append([v4, v5])

        v6 = V(-20, 20)

        vertices = [v1, v2, v6]
        all_vertices = [v1, v2, v3, v4, v5, v6]

        filtered = self.geography.filter_occluded_vertices(vertex, vertices, all_vertices)

        self.assertEquals([v6], filtered)

    def test_room_object_overlap(self):
        obj1 = RoomObject("test", P(0, 0), 20, 20)
        obj2 = RoomObject("test", P(10, 10), 20, 20)

        self.room.room_objects.append(obj1)
        self.room.room_objects.append(obj2)

        overlaps = self.geography.get_room_object_overlaps(obj1)
        self.assertEquals([
            (Vertex(obj1, P(10, 0)), obj2),
            (Vertex(obj1, P(0, 10)), obj2),
        ], overlaps)

    def test_polygon_vertex_intersect(self):
        obj = RoomObject("test", P(0, 0), 20, 20)
        self.room.room_objects.append(obj)
        obj2 = RoomObject("test", P(0, 0), 20, 20)
        self.room.room_objects.append(obj2)

        vertices = self.geography.get_vertices(obj)

        polygon = Sector(Vertex(obj2, P(-10, -20)), Vertex(obj2, P(0, -20)), Vertex(obj2, P(0, 0)))
        intersected = self.geography.get_polygon_intersects(polygon)

        self.assertEquals([
            (Vertex(None, P(-5, -10)), obj),
            (Vertex(None, P(0, -10)), obj),
        ], intersected)
