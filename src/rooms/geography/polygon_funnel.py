
import math
from .intersect import intersect, intersection_point
from .basic_geography import BasicGeography
from rooms.position import Position


class Polygon(object):
    def __init__(self, v1, v2, v3):
        self.vertices = [v1, v2, v3]

    def __repr__(self):
        return "Polygon(%s, %s, %s)" % (self.vertices[0], self.vertices[1], self.vertices[2])

    def __eq__(self, rhs):
        return rhs and len(rhs.vertices) == len(self.vertices) and (
            self.vertices[0] in rhs.vertices and
            self.vertices[1] in rhs.vertices and
            self.vertices[2] in rhs.vertices)


class Vertex(object):
    def __init__(self, room_object, position):
        self.room_object = room_object
        self.position = position
        self.previous = None
        self.next = None

    def __eq__(self, rhs):
        return rhs and self.position == rhs.position

    def __ne__(self, rhs):
        return not self.__eq__(rhs)

    def __repr__(self):
        return "<Vertex %s (%s, %s)>" % (self.room_object.object_type if self.room_object else None,
                                         self.position.x, self.position.y)

    @property
    def coords(self):
        return (self.position.x, self.position.y)


def angle(v1, v2):
    return (math.atan2(v1.position.y - v2.position.y, v1.position.x - v2.position.x) + math.pi) % (math.pi * 2)


class PolygonFunnelGeography(BasicGeography):
    def setup(self, room):
        self.room = room
        self._vertices = dict()
        self._polygons = self.polyfill()

    def draw(self):
        polygons = []
        for polygon in self._polygons:
            poly = [
                {'x': polygon.vertices[0].position.x, 'y': polygon.vertices[0].position.y},
                {'x': polygon.vertices[1].position.x, 'y': polygon.vertices[1].position.y},
                {'x': polygon.vertices[2].position.x, 'y': polygon.vertices[2].position.y},
            ]
            polygons.append(poly)
        return {"polygons": polygons, "type": "polygon_funnel"}

    def get_vertices(self, room_object):
        if room_object not in self._vertices:
            v1 = Vertex(room_object, room_object.position.add_coords(-room_object.width / 2.0, -room_object.height / 2.0))
            v2 = Vertex(room_object, room_object.position.add_coords(room_object.width / 2.0, -room_object.height / 2.0))
            v3 = Vertex(room_object, room_object.position.add_coords(room_object.width / 2.0, room_object.height / 2.0))
            v4 = Vertex(room_object, room_object.position.add_coords(-room_object.width / 2.0, room_object.height / 2.0))
            v1.previous = v4
            v1.next = v2
            v2.previous = v1
            v2.next = v3
            v3.previous = v2
            v3.next = v4
            v4.previous = v3
            v4.next = v1

            self._vertices[room_object] = [v1, v2, v3, v4]
        return self._vertices[room_object]

    def any_intersect(self, from_x, from_y, to_x, to_y, s1, sectors):
        for sector in sectors:
            if intersect(from_x, from_y, to_x, to_y, \
                            s1.x, s1.y,
                            sector[0].position.x, sector[0].position.y):
                return True
            if intersect(from_x, from_y, to_x, to_y, \
                            sector[0].position.x, sector[0].position.y,
                            sector[1].position.x, sector[1].position.y):
                return True

            if intersect(from_x, from_y, to_x, to_y, \
                            sector[1].position.x, sector[1].position.y,
                            s1.x, s1.y):
                return True
        return False

    def get_all_vertices(self):
        vertices = []

        tl = Vertex(None, self.room.topleft)
        tr = Vertex(None, self.room.topright)
        br = Vertex(None, self.room.bottomright)
        bl = Vertex(None, self.room.bottomleft)

        tl.next = tr
        tr.next = br
        br.next = bl
        bl.next = tl

        vertices.append(tl)
        vertices.append(tr)
        vertices.append(br)
        vertices.append(bl)

        for obj in self.room.room_objects:
            vs = self.get_vertices(obj)
            vertices.extend(vs)

        intersects = []

        for from_vertex in vertices:
            for to_vertex in vertices:
                intersect = intersection_point(
                    from_vertex.coords,
                    from_vertex.next.coords,
                    to_vertex.coords,
                    to_vertex.next.coords)
                if intersect:
                    int_vertex = Vertex(None, Position(*intersect))
                    if int_vertex not in vertices and int_vertex not in intersects:
                        intersects.append(int_vertex)

        vertices.extend(intersects)
        return vertices

    def _is_occluded(self, vertex):
        if not self.room.position_within(vertex.position):
            return True
        for room_object in self.room.room_objects:
            if room_object.position_within(vertex.position):
                return True
        return False

    def _get_edges(self, vertex, vertices):
        edges = []
        for v in vertices:
            if v != vertex:
                edges.append((vertex, v))
        return sorted(edges, key=lambda v: angle(vertex, v[1]))

    def _edge_intersects_objects(self, edge):
        for room_object in self.room.room_objects:
            for from_p, to_p in [
                    (room_object.topleft, room_object.topright),
                    (room_object.topleft, room_object.bottomleft),
                    (room_object.topright, room_object.bottomright),
                    (room_object.bottomleft, room_object.bottomright)]:
                if intersect(edge[0].position.x, edge[0].position.y, edge[1].position.x, edge[1].position.y,
                              from_p.x, from_p.y, to_p.x, to_p.y):
                    return True
        return False

    def _edge_intersects_polygons(self, edge, polygons):
        for polygon in polygons:
            for index in range(len(polygon.vertices) - 1):
                from_v = polygon.vertices[index]
                to_v = polygon.vertices[index + 1]
                if intersect(edge[0].position.x, edge[0].position.y, edge[1].position.x, edge[1].position.y,
                        from_v.position.x, from_v.position.y, to_v.position.x, to_v.position.y):
                    return True
            from_v = polygon.vertices[2]
            to_v = polygon.vertices[0]
            if intersect(edge[0].position.x, edge[0].position.y, edge[1].position.x, edge[1].position.y,
                    from_v.position.x, from_v.position.y, to_v.position.x, to_v.position.y):
                return True

        return False

    def _edge_occluded_at_midpoint(self, edge):
        midpoint = Position((edge[0].position.x + edge[1].position.x) / 2.0, (edge[0].position.y + edge[1].position.y) / 2.0)
        for room_object in self.room.room_objects:
            if room_object.position_within(midpoint):
                return True
        return False

    def _filter_edges_for_occlusion(self, edges, polygons):
        #   remove edges which intersect any objects
        edges = [e for e in edges if not self._edge_intersects_objects(e)]
        #   remove edges which intersect existing polygons
        edges = [e for e in edges if not self._edge_intersects_polygons(e, polygons)]
        #   remove edges which are occluded at their midpoint
        edges = [e for e in edges if not self._edge_occluded_at_midpoint(e)]

        return edges

    def _polygon_contains_object(self, v1, v2, v3):
        for room_object in self.room.room_objects:
            from_x, from_y, to_x, to_y = room_object.position.x, room_object.position.y, room_object.position.x, -1000
            int1 = intersect(from_x, from_y, to_x, to_y, v1.position.x, v1.position.y, v2.position.x, v2.position.y)
            int2 = intersect(from_x, from_y, to_x, to_y, v2.position.x, v2.position.y, v3.position.x, v3.position.y)
            int3 = intersect(from_x, from_y, to_x, to_y, v3.position.x, v3.position.y, v1.position.x, v1.position.y)
            if (int(int1) + int(int2) + int(int3)) % 2:
                return True
        return False

    def polyfill(self):
        polygons = []
        # get vertices - corners, object corners, intersects between objects/objects/room walls
        # remove occluded vertices
        vertices = [v for v in self.get_all_vertices() if not self._is_occluded(v)]
        # for each vertex
        for vertex in vertices:
            #   get edges between vertex and all other vertices
            edges = self._get_edges(vertex, vertices)
            edges = self._filter_edges_for_occlusion(edges, polygons)
            #   for each connected vertex
            for index in range(len(edges) - 1):
                to_v1 = edges[index][1]
                to_v2 = edges[index + 1][1]
                if (not self._edge_occluded_at_midpoint((to_v1, to_v2)) and
                    not self._edge_intersects_objects((to_v1, to_v2)) and
                    not self._edge_intersects_polygons((to_v1, to_v2), polygons) and
                    not self._polygon_contains_object(vertex, to_v1, to_v2)):
                    #     create polygon
                    polygons.append(Polygon(vertex, to_v1, to_v2))
        return polygons
