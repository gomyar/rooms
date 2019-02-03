
import math
from .intersect import vertex_intersect, intersect
from .basic_geography import BasicGeography


class Sector(object):
    def __init__(self, v1, v2, v3):
        self.v1 = v1
        self.v2 = v2
        self.v3 = v3

    def __eq__(self, rhs):
        return rhs and self.v1 == rhs.v1 and self.v2 == rhs.v2 and self.v3 == rhs.v3

    def __ne__(self, rhs):
        return not self.__eq__(rhs)

    def __repr__(self):
        return "<Sector %s %s %s>" % (self.v1, self.v2, self.v3)


class Vertex(object):
    def __init__(self, room_object, position):
        self.room_object = room_object
        self.position = position
        self.previous = None
        self.next = None
        self.sectors = []

    def __eq__(self, rhs):
        return rhs and self.position == rhs.position

    def __ne__(self, rhs):
        return not self.__eq__(rhs)

    def __repr__(self):
        return "<Vertex %s (%s, %s)>" % (self.room_object.object_type if self.room_object else None,
                                         self.position.x, self.position.y)

    def add_sector(self, from_vector, to_vector):
        new_sector = [from_vector, to_vector]
        # check for next linked sector
        for index, (s1, s2) in enumerate(self.sectors):
            if s1 == to_vector:
                self.sectors.insert(index, new_sector)
                return
            if s2 == from_vector:
                self.sectors.insert(index + 1, new_sector)
                return

        # order sectors by angle
        ordered_sectors = [(angle(self, s[0]), s) for s in self.sectors]
        ordered_sectors.append((angle(self, from_vector), new_sector))
        ordered_sectors = sorted(ordered_sectors)

        sectors = [o[1] for o in ordered_sectors]

        # insert in between existing
        self.sectors = sectors

    def sectors_gaps(self):
        sectors = []
        last_sector = (None, None)
        for from_vector, to_vector in self.sectors:
            if last_sector[1] != from_vector:
                sectors.append([])
            sectors[-1].append([from_vector, to_vector])
            last_sector = (from_vector, to_vector)
        return sectors

    def complete_sectors(self):
        first_v = self.sectors[0][0]
        current_v = self.sectors[0][1]
        for v1, v2 in self.sectors[1:]:
            if v1 != current_v:
                return False
            current_v = v2

        return current_v == first_v

    def almost_complete_sectors(self):
        first_v = self.sectors[0][0]
        current_v = self.sectors[0][1]
        for v1, v2 in self.sectors[1:]:
            if v1 != current_v:
                return False
            current_v = v2

        return True


def angle(v1, v2):
    return (math.atan2(v1.position.y - v2.position.y, v1.position.x - v2.position.x) + math.pi) % (math.pi * 2)


class PolygonFunnelGeography(BasicGeography):
    def setup(self, room):
        self.room = room
        self._vertices = dict()
        self._sectors = self._create_sectors()

    def _create_sectors(self):
        sectors = []
        for vertex in self.get_all_vertices():
            sectors.extend(self.get_sectors_for(vertex))
        return sectors

    def draw(self):
        polygons = []
        for sector in self._sectors:
            poly = [
                {'x': sector.v1.position.x, 'y': sector.v1.position.y},
                {'x': sector.v2.position.x, 'y': sector.v2.position.y},
                {'x': sector.v3.position.x, 'y': sector.v3.position.y},
            ]
            polygons.append(poly)
        return {"polygons": polygons, "type": "polygon_funnel"}

    def get_vertices(self, room_object):
        if room_object not in self._vertices:
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

            v1.sectors = [[v2, v4]]
            v2.sectors = [[v3, v4], [v4, v1]]
            v3.sectors = [[v4, v2]]
            v4.sectors = [[v1, v2], [v2, v3]]

            self._vertices[room_object] = [v1, v2, v3, v4]
        return self._vertices[room_object]

    def get_next_sector(self, vertex):
        if not vertex.sectors:
            return None

        # check for complete sectors
        if vertex.complete_sectors():
            return None


        # find next gap in sectors
        next_v = vertex.sectors[0][1]

        # get all the vertices in the room
        all_vertices = self.get_all_vertices()


        # check for last sector which crosses 0 degrees
        if vertex.almost_complete_sectors() and \
                not self.get_vertices_betweenangle(all_vertices, vertex, vertex.sectors[-1][1], math.pi * 2) and \
                not self.get_vertices_betweenangle(all_vertices, vertex, vertex.sectors[0][0], 0):
            if self.filter_occluded_vertices(vertex, [vertex.sectors[-1][1], vertex.sectors[0][0]], all_vertices):
                return Sector(vertex, vertex.sectors[-1][1], vertex.sectors[0][0])

        # start at 0 degrees - check for gaps starting from 0
        # if any non-occluded vertices exists between 0  degrees and next_v, add them
        missing_initial = self.get_vertices_betweenangle(all_vertices, vertex, next_v, 0)
        missing_initial = self.filter_occluded_vertices(vertex, missing_initial, all_vertices)

        if len(missing_initial) > 1:
            if [missing_initial[0], missing_initial[1]] not in vertex.sectors:
                return Sector(vertex, missing_initial[0], missing_initial[1])
        elif missing_initial:
            if [missing_initial[0], next_v] not in vertex.sectors:
                return Sector(vertex, missing_initial[0], next_v)

        # process sectors clockwise
        index = 1
        while index < len(vertex.sectors) and vertex.sectors[index][0] == next_v:
            next_v = vertex.sectors[index][1]
            index += 1

        if index == len(vertex.sectors) - 1:
            next_next_v = vertex.sectors[index][0]
        else:
            next_next_v = vertex.sectors[0][0]

        # get all vertices reachable between next_v and next_next_v
        vertices = self.get_vertices_between(all_vertices, vertex, next_v, next_next_v)

        # filter out vertices occluded by existing edges
        vertices = self.filter_occluded_vertices(vertex, vertices, all_vertices)

        # fill in gap
        if vertices:
            return Sector(vertex, next_v, vertices[0])
        else:
            return Sector(vertex, next_v, next_next_v)

        # add node

        # return result or None if no gap
        pass

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

    def get_intersections(self, x1, y1, x2, y2):
        for sector in sectors:
            pass

    def filter_occluded_vertices(self, vertex, vertices, all_vertices):
        filtered = []
        for v in vertices:
            intersects = False
            for existing in all_vertices:
                from_x, from_y = vertex.position.x, vertex.position.y
                to_x, to_y = v.position.x, v.position.y
                sectors = existing.sectors
                if self.any_intersect(from_x, from_y, to_x, to_y, existing.position, sectors):
                    intersects = True
            if not intersects:
                filtered.append(v)
        return filtered

    def get_all_vertices(self):
        vertices = []
        for obj in self.room.room_objects:
            vs = self.get_vertices(obj)
            vertices.extend(vs)
        vertices.append(Vertex(None, self.room.topleft))
        vertices.append(Vertex(None, self.room.topright))
        vertices.append(Vertex(None, self.room.bottomright))
        vertices.append(Vertex(None, self.room.bottomleft))
        return vertices

    def get_vertices_between(self, all_vertices, v1, v2, v3):
        fromangle = angle(v1, v2)
        vertices = [(angle(v1, v), v) for v in all_vertices if v not in (v1, v2, v3)]
        toangle = angle(v1, v3)

        if toangle < fromangle:
            vertices = [(a, v) for (a, v) in vertices if angle(v1, v) > fromangle
                        or angle(v1, v) < toangle]
        else:
            vertices = [(a, v) for (a, v) in vertices if angle(v1, v) > fromangle
                        and angle(v1, v) < toangle]
        vertices.sort()
        return [v for (a, v) in vertices]

    def get_vertices_betweenangle(self, all_vertices, v1, v2, fromangle):
        vertices = [(angle(v1, v), v) for v in all_vertices if v not in (v1, v2)]
        toangle = angle(v1, v2)
        if toangle < fromangle:
            fromangle, toangle = toangle, fromangle
        vertices = [(a, v) for (a, v) in vertices if angle(v1, v) > fromangle
                    and angle(v1, v) < toangle]
        vertices.sort()
        return [v for (a, v) in vertices]

    def get_sectors_for(self, vertex):
        sectors = []
        sector = self.get_next_sector(vertex)
        if sector:
            vertex.add_sector(sector.v2, sector.v3)
            sector.v2.add_sector(sector.v3, vertex)
            sector.v3.add_sector(vertex, sector.v2)
        while sector:
            sectors.append(sector)
            sector = self.get_next_sector(vertex)
            if sector:
                vertex.add_sector(sector.v2, sector.v3)
                sector.v2.add_sector(sector.v3, vertex)
                sector.v3.add_sector(vertex, sector.v2)
        return sectors

    def get_all_the_things(self):
        # get all vertices in room
           # check for vertices inside another object
              # split out new vertices
        # for vertices in room
           # fill sectors, create sectors
        # for all sectors
           # link sectors
        pass

    def get_polygon_intersects(self, polygon):
        intersects = []
        for room_object in self.room.room_objects:
            vertices = self.get_vertices(room_object)
            for vertex in vertices[:-1]:
                for p in polygon.v1, polygon.v2, polygon.v3:
                    intersect = intersect()
        return intersects

