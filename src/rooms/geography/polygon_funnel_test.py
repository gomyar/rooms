
import unittest

from .polygon_funnel import PolygonFunnel
from .polygon_funnel import Vertex
from .intersect import is_between

from rooms.room import Room
from rooms.testutils import MockNode
from rooms.room import RoomObject
from rooms.position import Position

def debug_plot(vertices, xleft=None, xright=None, ytop=None, ybottom=None):
    xleft = int(xleft or min(p[0].x for p in vertices) - 1)
    xright = int(xright or max(p[0].x for p in vertices) + 1)
    ytop = int(ytop or min(p[0].y for p in vertices) - 1)
    ybottom = int(ybottom or max(p[0].y for p in vertices) + 3)

    def point_at(px, py):
        if Vertex(px, py) in [v[0] for v in vertices]:
            return 'O'
        else:
            for from_v, to_v in vertices:
                if from_v and to_v and is_between(from_v, to_v, Vertex(px, py)):
                    return '.'
        return ' '

    line = ' ' + '-' * (xright - xleft - 2) + ' '
    output = [line]
    for y in range(ytop, ybottom - 2):
        line = '|'
        for x in range(xleft + 1, xright):
            line += point_at(x, y)
        line += '|'
        output.append(line)
    line = ' ' + '-' * (xright - xleft - 2) + ' '
    output.append(line)
    return "\n".join(output)



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

        self.assertEquals([((-40, 0), Vertex(-40, -10), Vertex(-40, 10))], self.geography._get_intersects_for(Vertex(-45, 0), Vertex(0, 0), False))
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

        print debug_plot(self.geography._build_edges())
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

    def test_create_edges_overlap(self):
        room_object = RoomObject("table", Position(0, 0), 40, 40)
        self.room.add_object(room_object)

        room_object_2 = RoomObject("table", Position(20, 10), 20, 20)
        self.room.add_object(room_object_2)

        self.assertEquals([
            (Vertex(-50.0, -50.0), Vertex(-50.0, 50.0)),
            (Vertex(-50.0, 50.0), Vertex(50.0, 50.0)),
            (Vertex(50.0, 50.0), Vertex(50.0, -50.0)),
            (Vertex(50.0, -50.0), Vertex(-50.0, -50.0)),
            (Vertex(20.0, -20.0), Vertex(20.0, 0.0)),
            (Vertex(-20.0, 20.0), Vertex(-20.0, -20.0)),
            (Vertex(-20.0, -20.0), Vertex(20.0, -20.0)),
            (Vertex(20.0, 0.0), Vertex(30.0, 0.0)),
            (Vertex(30.0, 0.0), Vertex(30.0, 20.0)),
            (Vertex(30.0, 20.0), Vertex(20.0, 20.0)),
            (Vertex(20.0, 20.0), Vertex(-20.0, 20.0))],
            self.geography._build_edges())

    def test_create_edges_overlap_2(self):
        room_object = RoomObject("table", Position(0, 0), 40, 40)
        self.room.add_object(room_object)

        room_object_2 = RoomObject("table", Position(-20, 10), 20, 20)
        self.room.add_object(room_object_2)

        self.assertEquals([
            (Vertex(-50.0, -50.0), Vertex(-50.0, 50.0)),
            (Vertex(-50.0, 50.0), Vertex(50.0, 50.0)),
            (Vertex(50.0, 50.0), Vertex(50.0, -50.0)),
            (Vertex(50.0, -50.0), Vertex(-50.0, -50.0)),
            (Vertex(20.0, -20.0), Vertex(20.0, 20.0)),
            (Vertex(20.0, 20.0), Vertex(-20.0, 20.0)),
            (Vertex(-20.0, -20.0), Vertex(20.0, -20.0)),
            (Vertex(-20.0, 0.0), Vertex(-20.0, -20.0)),
            (Vertex(-20.0, 20.0), Vertex(-30.0, 20.0)),
            (Vertex(-30.0, 20.0), Vertex(-30.0, 0.0)),
            (Vertex(-30.0, 0.0), Vertex(-20.0, 0.0))],
            self.geography._build_edges())

    def test_create_edges_overlap_3(self):
        room_object = RoomObject("table", Position(0, 0), 40, 40)
        self.room.add_object(room_object)

        room_object_2 = RoomObject("table", Position(-20, -10), 20, 20)
        self.room.add_object(room_object_2)

        self.assertEquals([
            (Vertex(-50.0, -50.0), Vertex(-50.0, 50.0)),
            (Vertex(-50.0, 50.0), Vertex(50.0, 50.0)),
            (Vertex(50.0, 50.0), Vertex(50.0, -50.0)),
            (Vertex(50.0, -50.0), Vertex(-50.0, -50.0)),
            (Vertex(20.0, -20.0), Vertex(20.0, 20.0)),
            (Vertex(20.0, 20.0), Vertex(-20.0, 20.0)),
            (Vertex(-20.0, 20.0), Vertex(-20.0, 0.0)),
            (Vertex(-20.0, -20.0), Vertex(20.0, -20.0)),
            (Vertex(-20.0, 0.0), Vertex(-30.0, 0.0)),
            (Vertex(-30.0, 0.0), Vertex(-30.0, -20.0)),
            (Vertex(-30.0, -20.0), Vertex(-20.0, -20.0))],
            self.geography._build_edges())

    def test_overlap_at_concave_corner(self):
        #      |
        #  '''''<----
        #  |
        #  |
        room_object = RoomObject("table", Position(0, 0), 40, 40)
        self.room.add_object(room_object)

        room_object_2 = RoomObject("table", Position(20, -20), 40, 40)
        self.room.add_object(room_object_2)

        room_object_2 = RoomObject("table", Position(25, 5), 20, 10)
        self.room.add_object(room_object_2)

        self.assertEquals([
            (Vertex(-50.0, -50.0), Vertex(-50.0, 50.0)),
            (Vertex(-50.0, 50.0), Vertex(50.0, 50.0)),
            (Vertex(50.0, 50.0), Vertex(50.0, -50.0)),
            (Vertex(50.0, -50.0), Vertex(-50.0, -50.0)),
            (Vertex(20.0, 20.0), Vertex(-20.0, 20.0)),
            (Vertex(-20.0, 20.0), Vertex(-20.0, -20.0)),
            (Vertex(-20.0, -20.0), Vertex(0.0, -20.0)),
            (Vertex(40.0, -40.0), Vertex(40.0, 0.0)),
            (Vertex(40.0, 0.0), Vertex(20.0, 0.0)),
            (Vertex(0.0, -20.0), Vertex(0.0, -40.0)),
            (Vertex(0.0, -40.0), Vertex(40.0, -40.0)),
            (Vertex(20.0, 0.0), Vertex(35.0, 0.0)),
            (Vertex(35.0, 0.0), Vertex(35.0, 10.0)),
            (Vertex(35.0, 10.0), Vertex(20.0, 10.0)),
            (Vertex(20.0, 10.0), Vertex(20.0, 20.0))],
            self.geography._build_edges())

    def test_overlap_at_clockwise_concave_corner(self):
        #
        #  ---->'''''
        #       |
        #       |
        room_object = RoomObject("table", Position(0, 0), 40, 40)
        self.room.add_object(room_object)

        room_object_2 = RoomObject("table", Position(-20, -20), 40, 20)
        self.room.add_object(room_object_2)

        room_object_2 = RoomObject("table", Position(-20, -5), 20, 10)
        self.room.add_object(room_object_2)

        print debug_plot(self.geography._build_edges())
        self.assertEquals([
            (Vertex(-50.0, -50.0), Vertex(-50.0, 50.0)),
            (Vertex(-50.0, 50.0), Vertex(50.0, 50.0)),
            (Vertex(50.0, 50.0), Vertex(50.0, -50.0)),
            (Vertex(50.0, -50.0), Vertex(-50.0, -50.0)),
            (Vertex(20.0, 20.0), Vertex(-20.0, 20.0)),
            (Vertex(-20.0, 20.0), Vertex(-20.0, -20.0)),
            (Vertex(-20.0, -20.0), Vertex(0.0, -20.0)),
            (Vertex(40.0, -40.0), Vertex(40.0, 0.0)),
            (Vertex(40.0, 0.0), Vertex(20.0, 0.0)),
            (Vertex(0.0, -20.0), Vertex(0.0, -40.0)),
            (Vertex(0.0, -40.0), Vertex(40.0, -40.0)),
            (Vertex(20.0, 0.0), Vertex(35.0, 0.0)),
            (Vertex(35.0, 0.0), Vertex(35.0, 10.0)),
            (Vertex(35.0, 10.0), Vertex(20.0, 10.0)),
            (Vertex(20.0, 10.0), Vertex(20.0, 20.0))],
            self.geography._build_edges())

    def test_long_vertex_intersects(self):
        self.geography = PolygonFunnel()

        self.room = Room("game1", "room1", MockNode())
        self.room.coords(-50, -50, 250, 50)

        self.geography.setup(self.room)
        self.room.geog = self.geography

        self.geography.vertices
        points = [
            (10, 10),
            (10, -10),
            (20, -10),
            (20, 10),
            (30, 10),
            (30, 0),
            (40, 0),
            (40, 10),
            (50, 10),
            (50, 0),
            (60, 0),
            (60, -10),
            (70, -10),
            (70, 10),
            (80, 10),
            (80, -10),
            (90, -10),
            (90, 0),
            (100, 0),
            (100, 10),
        ]
        start = Vertex(0, 10)
        current_vertex = start
        for x, y in points:
            current_vertex = Vertex(x, y, current_vertex)
            self.geography._vertices.append(current_vertex)
        current_vertex.next = start
        start.previous = current_vertex

        # add room objects (for occlusion cal only)
        self.room.room_objects.append(RoomObject("test", Position(55, 15), 110, 10))
        self.room.room_objects.append(RoomObject("test", Position(15, 10), 10, 40))
        self.room.room_objects.append(RoomObject("test", Position(35, 15), 10, 30))
        self.room.room_objects.append(RoomObject("test", Position(55, 15), 10, 30))
        self.room.room_objects.append(RoomObject("test", Position(65, 10), 10, 40))
        self.room.room_objects.append(RoomObject("test", Position(85, 10), 10, 40))
        self.room.room_objects.append(RoomObject("test", Position(95, 15), 10, 30))


        intersects = self.geography._get_intersects(Vertex(0, 0, None, Vertex(110, 0)))
        self.assertEquals(10, len(intersects))

        vertices = self.geography._get_vertex_intersects(Vertex(0, 0, None, Vertex(110, 0)))
        self.assertEquals(12, len(vertices))

        self.assertEquals((10, 0), vertices[1].coords)
        self.assertEquals((0, 0), vertices[1].previous.coords)
        self.assertEquals((10, -10), vertices[1].next.coords)

        self.assertEquals((20, 0), vertices[2].coords)
        self.assertEquals((20, -10), vertices[2].previous.coords)
        self.assertEquals((30, 0), vertices[2].next.coords)

        self.assertEquals((30, 0), vertices[3].coords)
        self.assertEquals((20, 0), vertices[3].previous.coords)
        self.assertEquals((40, 0), vertices[3].next.coords)

        self.assertEquals((40, 0), vertices[4].coords)
        self.assertEquals((30, 0), vertices[4].previous.coords)
        self.assertEquals((50, 0), vertices[4].next.coords)

        self.assertEquals((50, 0), vertices[5].coords)
        self.assertEquals((40, 0), vertices[5].previous.coords)
        self.assertEquals((60, 0), vertices[5].next.coords)

        self.assertEquals((70, 0), vertices[6].coords)
        self.assertEquals((50, 0), vertices[6].previous.coords)
        self.assertEquals((60, -10), vertices[6].next.coords)

        self.assertEquals((70, -10), vertices[7].previous.coords)
        self.assertEquals((80, 0), vertices[7].next.coords)

        self.assertEquals((70, 0), vertices[8].previous.coords)
        self.assertEquals((80, -10), vertices[8].next.coords)

        self.assertEquals((100, 0), vertices[9].previous.coords)
        self.assertEquals((110, 10), vertices[9].next.coords)

        import pprint
        pprint.pprint( vertices)

        for (x, y), _, _ in intersects:
            self.geography._vertices.append(Vertex(x, y))

        #print debug_plot(self.geography._build_edges())
        self.assertEquals(1, 2)

    def test_long_vertex_intersects_objects(self):
        self.geography = PolygonFunnel()

        self.room = Room("game1", "room1", MockNode())
        self.room.coords(-50, -50, 150, 50)

        self.geography.setup(self.room)
        self.room.geog = self.geography

        self.room.add_object(RoomObject("test", Position(55, 15), 110, 10))
        self.room.add_object(RoomObject("test", Position(15, 10), 10, 40))
        self.room.add_object(RoomObject("test", Position(35, 15), 10, 30))
        self.room.add_object(RoomObject("test", Position(55, 15), 10, 30))
#        self.room.add_object(RoomObject("test", Position(65, 10), 10, 40))
#        self.room.add_object(RoomObject("test", Position(85, 10), 10, 40))
        self.room.add_object(RoomObject("test", Position(95, 15), 10, 30))

        print debug_plot(self.geography._build_edges())
        self.assertEquals(1, 2)
