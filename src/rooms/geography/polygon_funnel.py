

from .basic_geography import BasicGeography
from rooms.position import Position
from rooms.geography.intersect import intersection_point


class Vertex(object):
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.previous = None
        self.next = None

    @property
    def coords(self):
        return (self.x, self.y)

    def __eq__(self, rhs):
        return rhs and self.x == rhs.x and self.y == rhs.y

    def __repr__(self):
        return "Vertex(%s, %s)" % (self.x, self.y)


class PolygonFunnel(BasicGeography):
    def setup(self, room):
        self.room = room
        self._vertices = None

    @property
    def vertices(self):
        if not self._vertices:
            self._vertices = self._build_room_vertices()
        return self._vertices

    def _build_room_vertices(self):
        # room vertices go counterclockwise, object vertices go clockwise
        tl = Vertex(self.room.topleft.x, self.room.topleft.y)
        tr = Vertex(self.room.topleft.x + self.room.width, self.room.topleft.y)
        br = Vertex(self.room.bottomright.x, self.room.bottomright.y)
        bl = Vertex(self.room.bottomright.x - self.room.width, self.room.bottomright.y)

        tl.next = bl
        bl.next = br
        br.next = tr
        tr.next = tl
        tl.previous = tr
        tr.previous = br
        br.previous = bl
        bl.previous = tl

        return [tl, bl, br, tr]

    def _build_room_object_vertices(self, room_object):
        tl = Vertex(room_object.topleft.x, room_object.topleft.y)
        tr = Vertex(room_object.topleft.x + room_object.width, room_object.topleft.y)
        br = Vertex(room_object.bottomright.x, room_object.bottomright.y)
        bl = Vertex(room_object.bottomright.x - room_object.width, room_object.bottomright.y)

        tl.next = tr
        bl.next = tl
        br.next = bl
        tr.next = br
        tl.previous = bl
        tr.previous = tl
        br.previous = tr
        bl.previous = br
        return [tl, tr, br, bl]

    def _build_room_object_edges(self, room_object):
        return [(v, v.next) for v in self._build_room_object_vertices(room_object)]

    def _build_edges(self):
        return [(v, v.next) for v in self.vertices]

    def _is_vertex_occluded(self, point):
        position = Position(point.x, point.y)
        in_room = self.room.position_within(position)
        return self.room.object_at(position) or not in_room

    def _get_intersects_for(self, from_v, to_v):
        intersects = []
        # for room edges
        edges = self._build_edges()

        # for each object
        for edge_from, edge_to in edges:
            # for object vertices
            intersect = intersection_point(from_v.coords, to_v.coords, edge_from.coords, edge_to.coords)
            if intersect and intersect not in (from_v.coords, to_v.coords, edge_from.coords, edge_to.coords):
                intersects.append((intersect, edge_from, edge_to))
        # sort intersect points by distance from "from_v"
        def cmpdist(v):
            return Position(from_v.x, from_v.y).distance_to(Position(v[0][0], v[0][1]))
        intersects = sorted(set(intersects), key=cmpdist)
        return intersects

    def add_object(self, room_object):
        object_edges = self._build_room_object_edges(room_object)
        # mark start vertex as "in" or "out"
        occluded = self._is_vertex_occluded(object_edges[0][0])

        for_addition = []

        # for each edge in the room
        for from_v, to_v in object_edges:
            # for each intersection
            intersects = self._get_intersects_for(from_v, to_v)

            vertex = from_v
            for (int_x, int_y), edge_from, edge_to in intersects:
                if occluded:
                    vertex = Vertex(int_x, int_y)
                    vertex.previous = edge_from
                    vertex.next = to_v
                else:
                    vertex = Vertex(int_x, int_y)
                    vertex.previous = from_v
                    vertex.next = edge_to

                for_addition.append(vertex)
                occluded = not occluded
            # to_v
            if not occluded:
                to_v.previous = vertex
                for_addition.append(to_v)

            # add a vertex
            # swap in / out
            # hook up previous next
        for vertex in for_addition:
            vertex.previous.next = vertex
            vertex.next.previous = vertex
            self._vertices.append(vertex)
