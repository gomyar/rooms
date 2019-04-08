

from .basic_geography import BasicGeography
from rooms.position import Position
from rooms.geography.intersect import intersection_point, is_between


class Vertex(object):
    def __init__(self, x, y, previous=None, next=None):
        self.x = x
        self.y = y
        self._previous = None
        self._next = None
        self.previous = previous
        self.next = next

    @property
    def previous(self):
        return self._previous

    @previous.setter
    def previous(self, prev):
        self._previous = prev
        if prev:
            prev._next = self

    @property
    def next(self):
        return self._next

    @next.setter
    def next(self, nex):
        self._next = nex
        if nex:
           nex._previous = self

    @property
    def coords(self):
        return (self.x, self.y)

    def __eq__(self, rhs):
        return rhs and self.x == rhs.x and self.y == rhs.y

    def __repr__(self):
        pre = "(%s, %s)" % (self.previous.x, self.previous.y) if self.previous else ''
        nex = "(%s, %s)" % (self.next.x, self.next.y) if self.next else ''
        return "Vertex((%s, %s), %s, %s)" % (self.x, self.y, pre, nex)

    def midpoint(self):
        v = Vertex((self.x + self.next.x) / 2, (self.y + self.next.y) / 2)
        v.previous = self
        v.next = self.next
        return v


class PolygonFunnel(BasicGeography):
    def setup(self, room):
        self.room = room
        self._vertices = None

    @property
    def vertices(self):
        if not self._vertices:
            self._vertices = self._build_room_vertices()
        return self._vertices

    def vertex_at(self, x, y):
        for vertex in self.vertices:
            if vertex.x == x and vertex.y == y:
                return vertex
        return None

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
        return self._is_point_occluded(position)

    def _is_point_occluded(self, position):
        in_room = self.room.position_within(position)
        return self.room.object_at(position) or not in_room

    def _get_intersects_for(self, from_v, to_v, occluded):
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
        # add intersects for point-on-line vertices
#        rebuilt =[]
#        for index in intersects[:-1]:
#            (x1, y1), prev_v1, next_v1 = intersects[index]
#            (x2, y2), prev_v2, next_v2 = intersects[index + 1]
#
#            edge_points = self._vertices_along_line()
        return intersects

    def _get_intersects(self, from_v):
        to_v = from_v.next
        intersects = []
        for edge_from, edge_to in self._build_edges():
            # for object vertices
            intersect = intersection_point(from_v.coords, to_v.coords, edge_from.coords, edge_to.coords)
            if intersect:
                intersects.append((intersect, edge_from, edge_to))
        # sort intersect points by distance from "from_v"
        def cmpdist(v):
            return Position(from_v.x, from_v.y).distance_to(Position(v[0][0], v[0][1]))
        intersects = sorted(set(intersects), key=cmpdist)
        return intersects

    def _is_edge_occluded(self, from_v, to_v):
        midpoint = Position((from_v.x + to_v.x) / 2,
                            (from_v.y + to_v.y) / 2)
        return self._is_point_occluded(midpoint)

    def _get_vertex_intersects(self, from_v):

        intersects = self._get_intersects(from_v)
        vertices = []

        start_vertex = self.vertex_at(from_v.x, from_v.y)
        if not start_vertex:
            start_vertex = from_v
        last_vertex = self.vertex_at(from_v.next.x, from_v.next.y)
        if not last_vertex:
            last_vertex = from_v.next

        if intersects:
            # do for start vertex
            (x2, y2), edge_from2, edge_to2 = intersects[0]

            vertex_from = from_v
            vertex_to = Vertex(x2, y2)
            if not self._is_edge_occluded(vertex_from, vertex_to):
                existing_vertex1 = self.vertex_at(vertex_from.x, vertex_from.y)
                existing_vertex2 = self.vertex_at(x2, y2)
                if existing_vertex1 and existing_vertex2:
                    existing_vertex1.next = existing_vertex2
                elif existing_vertex1:
                    existing_vertex1.next = vertex_to
                    vertex_to.next = edge_to2
                    vertices.append(vertex_to)
                elif existing_vertex2:
                    existing_vertex2.previous = vertex_from
                    vertices.append(vertex_from)
                else:
                    vertex_from.previous = edge_from2
                    vertex_from.next = vertex_to
                    vertices.append(vertex_from)
                    vertices.append(vertex_to)

        for index in range(len(intersects)-1):
            (x1, y1), edge_from1, edge_to1 = intersects[index]
            (x2, y2), edge_from2, edge_to2 = intersects[index+1]
            vertex_from = Vertex(x1, y1)
            vertex_to = Vertex(x2, y2)
            if not self._is_edge_occluded(vertex_from, vertex_to):
                existing_vertex1 = self.vertex_at(x1, y1)
                existing_vertex2 = self.vertex_at(x2, y2)
                if existing_vertex1 and existing_vertex2:
                    existing_vertex1.next = existing_vertex2
                elif existing_vertex1:
                    existing_vertex1.next = vertex_to
                    vertex_to.next = edge_to2
                    vertices.append(vertex_to)
                elif existing_vertex2:
                    existing_vertex2.previous = vertex_from
                    vertex_from.previous = edge_from1
                    vertices.append(vertex_from)
                else:
                    vertex_from.next = vertex_to
                    vertices.append(vertex_from)
                    vertices.append(vertex_to)

        if intersects:
            # do for end vertex
            (x1, y1), edge_from1, edge_to1 = intersects[-1]

            vertex_from = Vertex(x1, y1)
            vertex_to = last_vertex
            if not self._is_edge_occluded(vertex_from, vertex_to):
                existing_vertex1 = self.vertex_at(x1, y1)
                existing_vertex2 = self.vertex_at(vertex_to.x, vertex_to.y)
                if existing_vertex1 and existing_vertex2:
                    existing_vertex1.next = existing_vertex2
                elif existing_vertex1:
                    existing_vertex1.next = vertex_to
                    vertices.append(vertex_to)
                elif existing_vertex2:
                    existing_vertex2.previous = vertex_from
                    vertices.append(vertex_from)
                else:
                    vertex_from.next = vertex_to
                    vertices.append(vertex_from)
                    vertices.append(vertex_to)

        if not intersects:
            if not self._is_edge_occluded(from_v, from_v.next):
                vertices.append(from_v)
                vertices.append(from_v.next)

        return vertices

    def add_intersecting_vertices(self, from_v):
        # check first vertex, does one exist already, if so, use that
        # get intersects 
        # for each intersect
        #   if not occluded
        #       if vertex exists at current_vertex, relink current
        #       else add new vertex
        #       if vertex exists at intersect, relink existing to current
        #       else add new vertex
        pass

    def _vertices_along_line(self, from_v, to_v):
        return [v for v in self.vertices if is_between(from_v, to_v, v)]

    def add_object(self, room_object):
        object_edges = self._build_room_object_edges(room_object)
        # mark start vertex as "in" or "out"
        occluded = self._is_vertex_occluded(object_edges[0][0])

        for_addition = []

        # for each edge in the room
        for from_v, to_v in object_edges:
            # for each intersection
            intersects = self._get_intersects_for(from_v, to_v, occluded)

#            if intersects:
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

                        # add vertices that are on the line from_v -> to_v as they don't show up on intersect
#                        line_points = self._vertices_along_line(vertex, edge_to)
#                        for v in self.vertices:
#                            if is_between(vertex, edge_to, v):
#                                occluded = self._is_vertex_occluded(v.midpoint())
#                                if not occluded:
#                                    for_addition.append(v)

                # test if entry/exit angle suggests occlusion change
                for_addition.append(vertex)
                #occluded = self._is_vertex_occluded(vertex.midpoint())
                occluded = not occluded
            # to_v
            if not occluded:
                to_v.previous = vertex
                for_addition.append(to_v)
#            else:
#                # add vertices that are on the line from_v -> to_v as they don't show up on intersect
#                for v in self.vertices:
#                    if is_between(vertex, edge_to, v):
#                        occluded = self._is_vertex_occluded(v.midpoint())
#                        if not occluded:
#                            for_addition.append(v)

            # add a vertex
            # swap in / out
            # hook up previous next
        # remove newly occluded vertices
        for vertex in self._vertices:
            if room_object.position_within(Position(vertex.x, vertex.y)):
                self._vertices.remove(vertex)
        for vertex in for_addition:
            vertex.previous.next = vertex
            vertex.next.previous = vertex
            self._vertices.append(vertex)

    def add_object(self, room_object):
        object_edges = self._build_room_object_edges(room_object)

        # for each edge in the room
        for from_v, to_v in object_edges:
            # for each intersection
            intersects = self._get_vertex_intersects(from_v)

            self._vertices.extend(intersects)
