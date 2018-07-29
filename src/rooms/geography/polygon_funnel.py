
import math
from .intersect import vertex_intersect

class Segment(object):
    def __init__(self, v1, v2, v3):
        self.v1 = v1
        self.v2 = v2
        self.v3 = v3

    def __eq__(self, rhs):
        return rhs and self.v1 == rhs.v1 and self.v2 == rhs.v2 and self.v3 == rhs.v3

    def __ne__(self, rhs):
        return not self.__eq__(rhs)

    def __repr__(self):
        return "<Segment %s %s %s>" % (self.v1, self.v2, self.v3)


class Vertex(object):
    def __init__(self, room_object, position):
        self.room_object = room_object
        self.position = position
        self.previous = None
        self.next = None
        self.segments = []

    def __eq__(self, rhs):
        return rhs and self.position == rhs.position

    def __ne__(self, rhs):
        return not self.__eq__(rhs)

    def __repr__(self):
        return "<Vertex %s (%s, %s)>" % (self.room_object.object_type if self.room_object else None,
                                         self.position.x, self.position.y)


def get_vertices(room_object):
    v1 = Vertex(room_object, room_object.position.add_coords(-room_object.width / 2, -room_object.height / 2))
    v2 = Vertex(room_object, room_object.position.add_coords(room_object.width / 2, -room_object.height / 2))
    v3 = Vertex(room_object, room_object.position.add_coords(room_object.width / 2, room_object.height / 2))
    v4 = Vertex(room_object, room_object.position.add_coords(-room_object.width / 2, room_object.height / 2))
    v1.previous = v4
    v1.next = v2
    v2.previous = v1
    v2.next = v3
    v3.previous = v2
    v3.next = v4
    v4.previous = v3
    v4.next = v1

    s1 = Segment(v1, v2, v4)
    s2 = Segment(v3, v4, v2)

    v1.segments = [[v2, v4]]
    v2.segments = [[v3, v4], [v4, v1]]
    v3.segments = [[v4, v2]]
    v4.segments = [[v1, v2], [v2, v3]]

    return [v1, v2, v3, v4], [s1, s2]


def complete_segments(vertex):
    first_v = vertex.segments[0][0]
    current_v = vertex.segments[0][1]
    for v1, v2 in vertex.segments[1:]:
        if v1 != current_v:
            return False
        current_v = v2

    return current_v == first_v

def get_next_node(room, vertex):
    # check for complete segments
    if complete_segments(vertex):
        return None

    # start at 0 degrees
    # find next gap in segments
    next_v = vertex.segments[0][1]
    index = 1
    while index < len(vertex.segments) and vertex.segments[index][0] == next_v:
        next_v = vertex.segments[index][1]
        index += 1

    if index == len(vertex.segments) - 1:
        next_next_v = vertex.segments[index][0]
    else:
        next_next_v = vertex.segments[0][0]

    # get all the vertices in the room
    all_vertices = get_all_vertices(room)

    # get all vertices reachable between next_v and next_next_v
    vertices = get_vertices_between(all_vertices, vertex, next_v, next_next_v)

    # filter out vertices occluded by existing edges
    vertices = filter_occluded_vertices(vertices, all_vertices)

    # fill in gap
    if vertices:
#        current_v = next_v
#        for v in vertices:
#            Segment(vertex, current_v, v)
#            current_v = v
#        Segment(vertex, current_v, next_next_v)
        return Segment(vertex, next_v, vertices[0])
    else:
        return Segment(vertex, next_v, next_next_v)

    # add node

    # return result or None if no gap
    pass


def filter_occluded_vertices(vertices, all_vertices):
    # todo
    return vertices


def get_all_vertices(room):
    vertices = []
    for obj in room.room_objects:
        vs, _ = get_vertices(obj)
        vertices.extend(vs)
    vertices.append(Vertex(None, room.topleft))
    vertices.append(Vertex(None, room.topright))
    vertices.append(Vertex(None, room.bottomright))
    vertices.append(Vertex(None, room.bottomleft))
    return vertices


def get_vertices_between(all_vertices, v1, v2, v3):
    vertices = [(_angle(v1, v), v) for v in all_vertices if v not in (v1, v2, v3)]
    from_angle = _angle(v1, v2)
    to_angle = _angle(v1, v3)
    if to_angle < from_angle:
        to_angle += math.pi * 2
    vertices = [(a, v) for (a, v) in vertices if _angle(v1, v) > from_angle
                and _angle(v1, v) < to_angle]
    vertices.sort()
    return [v for (a, v) in vertices]


def get_nodes_for(room, vertex):
    segments = []
    segment = get_next_node(room, vertex)
    if segment:
        vertex.segments.append([segment.v2, segment.v3])
    while segment:
        segments.append(segment)
        segment = get_next_node(room, vertex)
        if segment:
            vertex.segments.append([segment.v2, segment.v3])
    return segments


def _angle(v1, v2):
    return (math.atan2(v1.position.y - v2.position.y, v1.position.x - v2.position.x) + math.pi) % (math.pi * 2)


def _diff(origin, v1, v2):
    a2 = _angle(origin, v2)
    a1 = _angle(origin, v1)
    if a2 > a1:
        return a2 - a1
    else:
        return math.pi * 2 + (a2 - a1)


def __diff(a1, a2):
    d = a1 - a2
    if d >= 0:
        return d % math.pi
    else:
        return -(abs(d) % math.pi)

class PolygonFunnelGeography(object):
    def __init__(self):
        self.nodes = []

    def init(self, room):
        # create nodes
        self.room = room

        # for each object vertex duo (self + clockwise neighbour)
#        for obj in room.room_objects:
#            for vertex in get_vertices(obj):
#                next_vertex = vertex.next
#                angle = _angle(vertex, next_vertex)

                # get all other vertices ( except vertices in this object )
#                vertices = self._all_vertices(room)

                # filter out vertices at > 180 degrees
#                vertices = self._filter_pi(vertex, _angle(vertex.previous, vertex), vertices)

                # filter out vertices occluded by polys / objects
#                vertices = self._filter_occluded(vertex, vertices)

                # sort by angle, pick smallest

        # find attachable vertex
            # search every other vertex, beginning clockwise, find other vertex which is not occluded by another object or node

        pass

    def _filter_pi(self, vertex, angle, vertices):
        return [v for v in vertices if _angle(v, vertex) > angle]

    def _filter_occluded(self, vertex, vertices):
        return [v for v in vertices if self._complete(vertex, v)]

    def _complete(self, v1, v2):
        ''' return true if line segment is not intersected by a node or object
        '''
        for node in self.nodes:
            for v in node.vertices:
                if vertex_intersect(v1, v2, v, v.next):
                    return False
        for obj in self.room.room_objects:
            for v in get_vertices(obj):
                if vertex_intersect(v1, v2, v, v.next):
                    return False
        return True


    def _all_vertices(self, room):
        vertices = []
        for obj in room.room_objects:
            vertices.extend(get_vertices(obj))
        return vertices

