
import math
from .intersect import intersect, intersection_point, is_between
from .basic_geography import BasicGeography
from rooms.position import Position
from rooms.geography.astar_polyfunnel import AStar


class Polygon(object):
    def __init__(self, v1, v2, v3):
        self.vertices = [v1, v2, v3]
        self.connections = []

    def __repr__(self):
        return "Polygon(%s, %s, %s)" % (self.vertices[0].position.coords(),
                                        self.vertices[1].position.coords(),
                                        self.vertices[2].position.coords())

    def __eq__(self, rhs):
        return rhs and len(rhs.vertices) == len(self.vertices) and (
            self.vertices[0] in rhs.vertices and
            self.vertices[1] in rhs.vertices and
            self.vertices[2] in rhs.vertices)

    @property
    def midpoint(self):
        return Position(
            sum(v.position.x for v in self.vertices) / 3.0,
            sum(v.position.y for v in self.vertices) / 3.0
        )

    def distance_to(self, target_polygon):
        return self.midpoint.distance_to(target_polygon.midpoint)

    def point_within(self, position):
        p0, p1, p2 = [v.position for v in self.vertices]
        p = position
        A = 0.5 * (-p1.y * p2.x + p0.y * (-p1.x + p2.x) + p0.x * (p1.y - p2.y) + p1.x * p2.y)
        sign = -1 if A < 0 else 1
        s = (p0.y * p2.x - p0.x * p2.y + (p2.y - p0.y) * p.x + (p0.x - p2.x) * p.y) * sign
        t = (p0.x * p1.y - p0.y * p1.x + (p0.y - p1.y) * p.x + (p1.x - p0.x) * p.y) * sign
        return s >= 0 and t >= 0 and (s + t) <= 2.0 * A * sign

    def connection_for(self, target_polygon):
        for connection in self.connections:
            if connection.target_polygon == target_polygon:
                return connection
        return None


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
        return "Vertex(%s, %s)" % (self.room_object.object_type if self.room_object else None,
                                   self.position)

    @property
    def coords(self):
        return (self.position.x, self.position.y)


class Connection(object):
    def __init__(self, target_polygon, left_vertex, right_vertex):
        self.target_polygon = target_polygon
        self.left_vertex = left_vertex
        self.right_vertex = right_vertex

    def __repr__(self):
        return "Connection(%s, %s, %s)" % (self.target_polygon, self.left_vertex, self.right_vertex)

    def __eq__(self, rhs):
        return rhs and rhs.target_polygon == self.target_polygon and rhs.left_vertex == self.left_vertex and rhs.right_vertex == self.right_vertex


def angle(v1, v2):
    return (math.atan2(v1.position.y - v2.position.y, v1.position.x - v2.position.x) + math.pi) % (math.pi * 2)


def angle_p(p1, p2):
    return (math.atan2(p1.y - p2.y, p1.x - p2.x) + math.pi) % (math.pi * 2)


def diff_angles(left_from, left_to, right_from, right_to):
    ' Difference between angles of right_from->right_to - left_from->left_to '
    left_angle = angle_p(left_from, left_to)
    right_angle = angle_p(right_from, right_to)
    return diff(left_angle, right_angle)


def angle_max(lhs, rhs):
    if diff(lhs, rhs) < 0:
        return lhs
    else:
        return rhs


def angle_min(lhs, rhs):
    if diff(lhs, rhs) < 0:
        return rhs
    else:
        return lhs


def diff(left_angle, right_angle):
    if left_angle - right_angle > math.pi:
        return (math.pi * 2 - left_angle) + right_angle
    elif right_angle - left_angle > math.pi:
        return right_angle - left_angle - math.pi * 2
    else:
        return right_angle - left_angle


def connect_polygons(polygons):
    for polygon in polygons:
        for match in polygons:
            vertices = [v for v in polygon.vertices if v in match.vertices]
            if polygon is not match and len(vertices) == 2:
                # case where vertices are looped
                if polygon.vertices[0] == vertices[0] and polygon.vertices[2] == vertices[1]:
                    right_vertex, left_vertex = vertices
                else:
                    left_vertex, right_vertex = vertices
                polygon.connections.append(Connection(match, left_vertex, right_vertex))


class PolygonFunnelGeography(BasicGeography):
    def setup(self, room):
        self.room = room
        self._vertices = dict()
        self.polygons = self.polyfill()
        connect_polygons(self.polygons)

    def draw(self):
        polygons = []
        for polygon in self.polygons:
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

    def _edge_intersects_vertices(self, edge, vertices):
        for vertex in vertices:
            if vertex not in edge and is_between(edge[0].position, edge[1].position, vertex.position):
                return True
        return False

    def _filter_edges_for_occlusion(self, edges, polygons, vertices):
        #   remove edges which intersect any objects
        edges = [e for e in edges if not self._edge_intersects_objects(e)]
        #   remove edges which intersect existing polygons
        edges = [e for e in edges if not self._edge_intersects_polygons(e, polygons)]
        #   remove edges which are occluded at their midpoint
        edges = [e for e in edges if not self._edge_occluded_at_midpoint(e)]
        # remove edges which are intersected by vertices
        edges = [e for e in edges if not self._edge_intersects_vertices(e, vertices)]

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
            edges = self._filter_edges_for_occlusion(edges, polygons, vertices)
            #   for each connected vertex
            for index in range(len(edges) - 1):
                to_v1 = edges[index][1]
                to_v2 = edges[index + 1][1]
                if (not self._edge_occluded_at_midpoint((to_v1, to_v2)) and
                    not self._edge_intersects_objects((to_v1, to_v2)) and
                    not self._edge_intersects_polygons((to_v1, to_v2), polygons) and
                    not self._edge_intersects_vertices((to_v1, to_v2), vertices) and
                    not self._polygon_contains_object(vertex, to_v1, to_v2)):
                    #     create polygon
                    new_polygon = Polygon(vertex, to_v1, to_v2)
                    if new_polygon not in polygons:
                        polygons.append(new_polygon)
        return polygons

    def find_poly_at_point(self, point):
        for polygon in self.polygons:
            if polygon.point_within(point):
                return polygon
        return None

    def find_path(self, room, from_point, to_point):
        # get poly chain
        poly_chain = AStar(self).find_path(from_point, to_point)
        path = self.funnel_poly_chain(poly_chain, from_point, to_point)
        print "Path: %s" % (path,)
        return path

    def funnel_poly_chain(self, poly_chain, from_position, to_position):

        if not poly_chain:
            return []
        if len(poly_chain) == 1:
            return [from_position, to_position]

        path = [from_position]
        current_position = from_position

        if len(poly_chain) == 2:
            current_polygon = poly_chain.pop(0)
            next_polygon = poly_chain.pop(0)
            connection = current_polygon.connection_for(next_polygon)
            if diff_angles(current_position, connection.left_vertex.position, current_position, to_position) < 0:
                path.append(connection.left_vertex.position)
            if diff_angles(current_position, to_position, current_position, connection.right_vertex.position) < 0:
                path.append(connection.right_vertex.position)

            path.append(to_position)
            return path

        first_polygon = poly_chain.pop(0)
        current_polygon = poly_chain.pop(0)
        connection = first_polygon.connection_for(current_polygon)
        left_position = connection.left_vertex.position
        right_position = connection.right_vertex.position
        left_angle = angle_p(current_position, left_position)
        right_angle = angle_p(current_position, right_position)
        while len(poly_chain) > 1:
            next_polygon = poly_chain.pop(0)
            connection = current_polygon.connection_for(next_polygon)
            if left_position == connection.left_vertex.position:
                left_angle = angle_max(left_angle, angle_p(current_position, left_position))
                right_angle = angle_min(right_angle, angle_p(current_position, connection.right_vertex.position))

                angle = diff(left_angle, right_angle)
                if angle < 0 or diff_angles(current_position, left_position, current_position, to_position) < 0:
                    current_position = left_position
                    if current_position not in path:
                        path.append(current_position)
            if right_position == connection.right_vertex.position:
                left_angle = angle_max(left_angle, angle_p(current_position, connection.left_vertex.position))
                right_angle = angle_min(right_angle, angle_p(current_position, right_position))

                angle = diff(left_angle, right_angle)
                if angle < 0 or diff_angles(current_position, to_position, current_position, right_position) < 0:
                    current_position = right_position
                    if current_position not in path:
                        path.append(current_position)

            current_polygon = next_polygon
            left_position = connection.left_vertex.position
            right_position = connection.right_vertex.position

        next_polygon = poly_chain.pop(0)
        connection = current_polygon.connection_for(next_polygon)

        left_angle = angle_max(left_angle, angle_p(current_position, left_position))
        right_angle = angle_min(right_angle, angle_p(current_position, right_position))

        if diff_angles(current_position, connection.left_vertex.position, current_position, to_position) < 0:
            path.append(connection.left_vertex.position)
        if diff_angles(current_position, to_position, current_position, connection.right_vertex.position) < 0:
            path.append(connection.right_vertex.position)

        path.append(to_position)
        return path
